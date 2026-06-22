"""Generic local book translation orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.tie.book_ingestion import (
    clean_selected_book_text,
    extract_book_text,
    select_book_range,
    slugify_book_run_name,
)
from src.tie.chunk_stitching import SentenceSafeChunker
from src.tie.export_pdf import export_translation_pdf
from src.tie.foreign_residue import ForeignResidueDetector
from src.tie.literary_semantic_qa import LiterarySemanticQAChecker
from src.tie.quality_gate import QualityGate
from src.tie.revision_checklist import build_and_evaluate
from src.tie.source_cleanup import SourceExtractionQualityChecker
from src.tie.strategy_planner import TranslationStrategyPlanner
from src.tie.target_naturalness import TargetOnlyNaturalnessPass
from src.tie.tm_retrieval import build_translation_reference_context
from src.tie.turkish_fluency_qa import TurkishFluencyAnomalyChecker


Translator = Callable[[str, Dict[str, Any]], str]


@dataclass
class BookRunResult:
    run_id: str
    output_dir: str
    chunks_translated: int
    source_words: int
    target_words: int
    recommendation: str
    output_paths: Dict[str, Optional[str]]


def build_book_run_config(
    input_path: str,
    target_language: str = "tr_TR",
    source_language: str = "en_US",
    first_pages: Optional[int] = None,
    first_words: Optional[int] = None,
    words_per_page: int = 300,
    chunk_chars: int = 3200,
    tm_enabled: bool = True,
    tm_dir: str = "outputs/parallel",
    tm_top_k: int = 3,
    tm_min_confidence: str = "high",
    output_root: str = "outputs/book_runs",
    write_pdf: bool = False,
    write_markdown: bool = True,
    write_side_by_side: bool = False,
    write_quality_report: bool = True,
    write_metadata: bool = True,
) -> Dict[str, Any]:
    if first_pages is not None and first_words is not None:
        raise ValueError("Choose either first_pages or first_words, not both.")
    return {
        "input_path": str(input_path),
        "source_language": _normalize_language(source_language, "en_US"),
        "target_language": _normalize_language(target_language, "tr_TR"),
        "first_pages": first_pages,
        "first_words": first_words,
        "words_per_page": words_per_page,
        "chunk_chars": chunk_chars,
        "genre": "literary",
        "tm": {
            "enabled": tm_enabled,
            "directory": tm_dir,
            "top_k": tm_top_k,
            "min_alignment_confidence": tm_min_confidence,
            "use_mode": "reference_only",
            "auto_inject": False,
        },
        "outputs": {
            "root": output_root,
            "pdf": write_pdf,
            "markdown": write_markdown,
            "side_by_side": write_side_by_side,
            "quality_report": write_quality_report,
            "metadata": write_metadata,
        },
    }


class BookTranslationRunner:
    """Run ingestion, translation, QA, and local artifact generation."""

    def __init__(
        self,
        translator: Optional[Translator] = None,
        tm_builder: Callable[..., Dict[str, Any]] = build_translation_reference_context,
    ):
        self.translator = translator or self._translate_with_existing_agent
        self.tm_builder = tm_builder
        self.strategy_planner = TranslationStrategyPlanner()
        self.source_checker = SourceExtractionQualityChecker()
        self.naturalness = TargetOnlyNaturalnessPass()
        self.residue = ForeignResidueDetector()
        self.semantic = LiterarySemanticQAChecker()
        self.fluency = TurkishFluencyAnomalyChecker()
        self.quality_gate = QualityGate()

    def run(self, config: Dict[str, Any]) -> BookRunResult:
        extracted = extract_book_text(
            config["input_path"],
            max_pages=config.get("first_pages") if str(config["input_path"]).lower().endswith(".pdf") else None,
        )
        selected = select_book_range(
            extracted,
            first_pages=config.get("first_pages"),
            first_words=config.get("first_words"),
            words_per_page=config.get("words_per_page", 300),
        )
        cleaned = clean_selected_book_text(selected)
        source_text = cleaned["cleaned_text"].strip()
        if not source_text:
            raise ValueError("No translatable text was extracted from the requested range.")

        run_id = self._run_id(config["input_path"], config["target_language"])
        output_dir = Path(config["outputs"]["root"]) / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        source_quality = self.source_checker.check(
            source_text,
            source_language=config["source_language"],
            document_type=extracted["input_format"],
            genre="literary_fiction",
        )
        chunking = SentenceSafeChunker(max_chars=config["chunk_chars"]).chunk_text(
            source_text,
            chunk_id_prefix=run_id,
        )

        chunk_results = []
        previous_translation = ""
        for chunk in chunking["chunks"]:
            source_chunk = chunk["text"]
            strategy = self.strategy_planner.plan(
                source_chunk,
                source_language=config["source_language"],
                target_language=config["target_language"],
                genre=config["genre"],
            )
            tm_pack = self._reference_pack(source_chunk, config["tm"])
            context = {
                "run_id": run_id,
                "chunk_id": chunk["chunk_id"],
                "source_language": config["source_language"],
                "target_language": config["target_language"],
                "genre": config["genre"],
                "translation_strategy": strategy,
                "previous_chunk_context": previous_translation[-800:],
                "tm_reference_pack": tm_pack,
                "tm_reference_usage": "metadata_only",
            }
            draft = self.translator(source_chunk, context).strip()
            checklist, revision = build_and_evaluate(
                source_text=source_chunk,
                translated_text=draft,
                genre=config["genre"],
                source_language=config["source_language"],
                target_language=config["target_language"],
                translation_strategy=strategy,
            )
            naturalness = self.naturalness.apply(
                draft,
                genre=config["genre"],
                target_language=config["target_language"],
                translation_strategy=strategy,
                revision_evaluation=revision,
                revision_recommendations=revision["revision_recommendations"],
            )
            translation = naturalness["revised_text"]
            residue = self.residue.detect(translation, target_language=config["target_language"])
            semantic = self.semantic.check(source_chunk, translation)
            fluency = (
                self.fluency.check(translation)
                if config["target_language"].startswith("tr")
                else {"fluency_score": None, "flags": [], "recommendation": "accept"}
            )
            gate = self.quality_gate.evaluate(
                source_quality=source_quality,
                foreign_residue=residue,
                boundary_flags=chunk.get("boundary_flags", []),
                semantic_flags=semantic["flags"],
                fluency_flags=fluency["flags"],
            )
            chunk_results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "source_text": source_chunk,
                    "translation": translation,
                    "boundary": {
                        "flags": chunk.get("boundary_flags", []),
                        "recommendation": chunk.get("recommendation"),
                    },
                    "translation_strategy": strategy,
                    "tm_reference_pack": tm_pack,
                    "revision_checklist": checklist,
                    "revision_evaluation": revision,
                    "target_naturalness": naturalness,
                    "foreign_residue": residue,
                    "semantic_qa": semantic,
                    "fluency_qa": fluency,
                    "quality_gate": gate,
                }
            )
            previous_translation = translation

        recommendation = _aggregate_recommendation(
            [result["quality_gate"]["recommendation"] for result in chunk_results]
        )
        output_paths = self._write_outputs(
            config=config,
            run_id=run_id,
            output_dir=output_dir,
            extracted=extracted,
            selected=cleaned,
            source_quality=source_quality,
            chunking=chunking,
            chunks=chunk_results,
            recommendation=recommendation,
        )
        return BookRunResult(
            run_id=run_id,
            output_dir=str(output_dir),
            chunks_translated=len(chunk_results),
            source_words=_word_count(source_text),
            target_words=sum(_word_count(item["translation"]) for item in chunk_results),
            recommendation=recommendation,
            output_paths=output_paths,
        )

    def _reference_pack(self, source_chunk: str, tm_config: Dict[str, Any]) -> Dict[str, Any]:
        if not tm_config.get("enabled", True):
            return {"enabled": False, "references": [], "warnings": ["TM retrieval disabled."]}
        try:
            pack = self.tm_builder(
                source_chunk,
                tm_dir=tm_config["directory"],
                top_k=tm_config["top_k"],
                min_alignment_confidence=tm_config["min_alignment_confidence"],
            )
            return {
                "enabled": True,
                "use_mode": "reference_only",
                "auto_inject": False,
                **pack,
            }
        except (FileNotFoundError, OSError, ValueError) as exc:
            return {
                "enabled": True,
                "use_mode": "reference_only",
                "auto_inject": False,
                "references": [],
                "warnings": [f"TM retrieval unavailable: {exc}"],
            }

    def _write_outputs(
        self,
        config: Dict[str, Any],
        run_id: str,
        output_dir: Path,
        extracted: Dict[str, Any],
        selected: Dict[str, Any],
        source_quality: Dict[str, Any],
        chunking: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        recommendation: str,
    ) -> Dict[str, Optional[str]]:
        paths: Dict[str, Optional[str]] = {
            "translation_markdown": None,
            "side_by_side_markdown": None,
            "metadata_json": None,
            "quality_report": None,
            "pdf": None,
        }
        translations = [item["translation"] for item in chunks]
        if config["outputs"]["markdown"]:
            path = output_dir / "translation.md"
            path.write_text("\n\n".join(translations), encoding="utf-8")
            paths["translation_markdown"] = str(path)
        if config["outputs"]["side_by_side"]:
            path = output_dir / "side_by_side.md"
            lines = ["# Source / Translation Review", ""]
            for item in chunks:
                lines.extend(
                    [
                        f"## {item['chunk_id']}",
                        "",
                        "### Source",
                        "",
                        item["source_text"],
                        "",
                        "### Translation",
                        "",
                        item["translation"],
                        "",
                    ]
                )
            path.write_text("\n".join(lines), encoding="utf-8")
            paths["side_by_side_markdown"] = str(path)

        metadata = {
            "schema_version": "book_run_v1",
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "input_path": config["input_path"],
            "input_format": extracted["input_format"],
            "title": extracted.get("title"),
            "author": extracted.get("author"),
            "source_language": config["source_language"],
            "target_language": config["target_language"],
            "range": selected["range"],
            "page_definition": extracted["page_definition"],
            "tm_retrieval": config["tm"],
            "source_cleanup": selected["source_cleanup"],
            "source_quality": source_quality,
            "chunking": {
                "chunk_count": len(chunks),
                "recommendation": chunking["recommendation"],
                "global_flags": chunking["global_flags"],
            },
            "quality_recommendation": recommendation,
            "chunks": chunks,
        }
        if config["outputs"]["metadata"]:
            path = output_dir / "metadata.json"
            path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            paths["metadata_json"] = str(path)
        qa_summary = _qa_summary(chunks, recommendation)
        if config["outputs"]["quality_report"]:
            path = output_dir / "quality_report.md"
            path.write_text(_quality_report(metadata, qa_summary), encoding="utf-8")
            paths["quality_report"] = str(path)
        if config["outputs"]["pdf"]:
            pdf_result = export_translation_pdf(
                str(output_dir / "translation.pdf"),
                translations,
                metadata,
                qa_summary,
            )
            paths["pdf"] = pdf_result.get("path")
        return paths

    def _translate_with_existing_agent(self, source_text: str, context: Dict[str, Any]) -> str:
        from src.agents.translator import translate_draft

        state = {
            "source_text": source_text,
            "source_language": context["source_language"],
            "target_language": context["target_language"],
            "genre": context["genre"],
            "glossary": {},
            "positive_glossary": {},
            "negative_glossary": {},
            "auto_glossary_candidates": {},
            "compact_memory_context": "",
            "translation_strategy": context["translation_strategy"],
            "language_profile": {},
            "logs": [],
            "chunk_index": context["chunk_id"],
        }
        return translate_draft(state)["raw_translation"]

    @staticmethod
    def _run_id(input_path: str, target_language: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{slugify_book_run_name(input_path)}_{target_language.casefold()}_{timestamp}"


def _normalize_language(value: str, default: str) -> str:
    aliases = {"en": "en_US", "tr": "tr_TR"}
    return aliases.get((value or "").casefold(), value or default)


def _aggregate_recommendation(recommendations: List[str]) -> str:
    if "reject" in recommendations:
        return "reject"
    if "review" in recommendations:
        return "review"
    return "accept"


def _qa_summary(chunks: List[Dict[str, Any]], recommendation: str) -> Dict[str, Any]:
    return {
        "recommendation": recommendation,
        "chunk_count": len(chunks),
        "accepted_chunks": sum(item["quality_gate"]["recommendation"] == "accept" for item in chunks),
        "review_chunks": sum(item["quality_gate"]["recommendation"] == "review" for item in chunks),
        "rejected_chunks": sum(item["quality_gate"]["recommendation"] == "reject" for item in chunks),
        "tm_references_retrieved": sum(
            len(item["tm_reference_pack"].get("references", [])) for item in chunks
        ),
        "human_review_required": True,
    }


def _quality_report(metadata: Dict[str, Any], summary: Dict[str, Any]) -> str:
    lines = [
        "# Generic Book Translation Run Quality Report",
        "",
        f"- Run: `{metadata['run_id']}`",
        f"- Format: {metadata['input_format']}",
        f"- Target language: {metadata['target_language']}",
        f"- Page definition: {metadata['page_definition']}",
        f"- Recommendation: **{summary['recommendation']}**",
        f"- Chunks: {summary['chunk_count']}",
        f"- TM references retrieved: {summary['tm_references_retrieved']}",
        "- Human review required: yes",
        "",
        "This report contains deterministic guardrails. It is not proof of publication-ready translation quality.",
        "",
        "## Chunk Results",
        "",
    ]
    for chunk in metadata["chunks"]:
        lines.append(
            f"- `{chunk['chunk_id']}`: {chunk['quality_gate']['recommendation']} "
            f"(residue={chunk['foreign_residue']['foreign_residue_count']}, "
            f"semantic_flags={len(chunk['semantic_qa']['flags'])}, "
            f"fluency_flags={len(chunk['fluency_qa']['flags'])})"
        )
    return "\n".join(lines) + "\n"


def _word_count(text: str) -> int:
    return len((text or "").split())
