"""Translate Blood Meridian chapter 1 first five content pages for quick review.

Writes local review artifacts only. The full translation outputs should not be
committed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.stylist import stylize_translation
from src.agents.translator import translate_draft
from src.core.config import Config
from src.tie.chunk_stitching import SentenceSafeChunker
from src.tie.foreign_residue import ForeignResidueDetector
from src.tie.literary_semantic_qa import LiterarySemanticQAChecker
from src.tie.quality_gate import QualityGate
from src.tie.revision_checklist import build_and_evaluate
from src.tie.source_cleanup import SourceExtractionCleaner, SourceExtractionQualityChecker
from src.tie.strategy_planner import TranslationStrategyPlanner
from src.tie.target_naturalness import TargetOnlyNaturalnessPass
from src.tie.turkish_fluency_qa import TurkishFluencyAnomalyChecker

from scripts.translate_blood_meridian_ch1_ch2_v2 import (
    PROPER_NOUNS,
    load_json,
    load_style_contract,
    load_text,
    strip_response_wrappers,
    style_analysis,
    style_contract_context,
    summarize_previous_context,
    summarize_repairs,
)


PDF_PATH = PROJECT_ROOT / "data" / "inputs" / "mccarthy_cormac_blood_meridianbooksee-org.pdf"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MAX_CHARS = 3200


def main() -> None:
    Config.validate()
    if not PDF_PATH.exists():
        raise FileNotFoundError("PDF not found under data/inputs/")

    extracted = extract_first_five_content_pages(PDF_PATH)
    cleaner = SourceExtractionCleaner()
    quality_checker = SourceExtractionQualityChecker()
    cleanup = cleaner.clean(
        extracted["raw_text"],
        source_language="en_US",
        document_type="pdf",
        genre="literary_fiction",
    )
    quality = quality_checker.check(cleanup["cleaned_text"])
    if quality["recommendation"] == "reject":
        write_source_cleaned(PDF_PATH, extracted, cleanup, quality)
        raise SystemExit("Source extraction rejected; translation stopped.")

    chunks = build_chunks(cleanup["cleaned_text"], extracted["pages_used"], quality, cleanup)
    translated_chunks = translate_chunks(chunks)
    write_source_cleaned(PDF_PATH, extracted, cleanup, quality)
    write_outputs(PDF_PATH, extracted, cleanup, quality, translated_chunks)

    residue_after = sum(chunk["foreign_residue_count_after_final"] for chunk in translated_chunks)
    accepted = sum(chunk["recommendation"] == "accept" for chunk in translated_chunks)
    reviews = sum(chunk["recommendation"] == "review" for chunk in translated_chunks)
    rejects = sum(chunk["recommendation"] == "reject" for chunk in translated_chunks)
    print("Blood Meridian first-five-pages review outputs written.")
    print(f"PDF: {PDF_PATH}")
    print(f"Pages used: {extracted['pages_used']}")
    print(f"Chunks translated: {len(translated_chunks)}")
    print(f"Source cleanup repairs: {len(cleanup['repairs'])}")
    print(f"Foreign residue after final pass: {residue_after}")
    print(f"Recommendations: accept={accepted}, review={reviews}, reject={rejects}")


def extract_first_five_content_pages(pdf_path: Path) -> Dict[str, Any]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    chapter_start_page = None
    chapter_start_offset = None

    for page_index, text in enumerate(page_texts, start=1):
        marker = re.search(r"(?m)^\s*I\s*$", text)
        opening = re.search(r"S\s*ee the child\.|See the child\.", text, re.IGNORECASE)
        if marker and opening and opening.start() > marker.start():
            chapter_start_page = page_index
            chapter_start_offset = marker.start()
            break

    if chapter_start_page is None or chapter_start_offset is None:
        candidates = []
        for page_index, text in enumerate(page_texts, start=1):
            if re.search(r"(?m)^\s*I\s*$", text) or re.search(r"S\s*ee the child\.|See the child\.", text, re.IGNORECASE):
                candidates.append(page_index)
        raise RuntimeError(f"Chapter 1 boundary unclear. Candidate pages: {candidates}")

    end_page = min(chapter_start_page + 4, len(page_texts))
    pages_used = list(range(chapter_start_page, end_page + 1))
    page_parts = []
    for page_index in pages_used:
        text = page_texts[page_index - 1]
        if page_index == chapter_start_page:
            text = text[chapter_start_offset:]
        page_parts.append(text)

    raw_text = "\n\n".join(page_parts).strip()
    if not re.search(r"S\s*ee the child\.|See the child\.", raw_text, re.IGNORECASE):
        raise RuntimeError(f"Chapter 1 opening not found after extraction. Pages: {pages_used}")

    return {
        "raw_text": raw_text,
        "chapter_start_page": chapter_start_page,
        "pages_used": pages_used,
    }


def build_chunks(
    cleaned_text: str,
    pages_used: List[int],
    source_quality: Dict[str, Any],
    cleanup: Dict[str, Any],
) -> List[Dict[str, Any]]:
    chunker = SentenceSafeChunker(max_chars=MAX_CHARS)
    chunk_result = chunker.chunk_text(cleaned_text, chunk_id_prefix="bm_first5")
    return [
        chunk_record(chunk, pages_used, source_quality, cleanup)
        for chunk in chunk_result["chunks"]
    ]


def chunk_record(
    chunk: Dict[str, Any],
    pages_used: List[int],
    source_quality: Dict[str, Any],
    cleanup: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "chunk_id": chunk["chunk_id"],
        "source_text": chunk["text"],
        "start_offset": chunk["start_offset"],
        "end_offset": chunk["end_offset"],
        "source_pages": pages_used,
        "boundary_flags": chunk["boundary_flags"],
        "boundary_recommendation": chunk["recommendation"],
        "source_quality": source_quality,
        "source_repairs": summarize_repairs(cleanup["repairs"]),
    }


def translate_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    style_contract = load_style_contract()
    planner = TranslationStrategyPlanner()
    language_context = planner.language_profile_context("en_US", "tr_TR")
    style_guide = load_text(PROJECT_ROOT / "data" / "reference" / "literary" / "style_guide.txt")
    glossary = load_json(PROJECT_ROOT / "data" / "reference" / "literary" / "glossary.json", default=[])
    detector = ForeignResidueDetector()
    naturalness = TargetOnlyNaturalnessPass()
    semantic_checker = LiterarySemanticQAChecker()
    fluency_checker = TurkishFluencyAnomalyChecker()
    quality_gate = QualityGate()

    translated_chunks = []
    previous_context = "None (first chunk)"
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk["chunk_id"]
        print(f"Translating {chunk_id} ({len(chunk['source_text'])} chars)")
        strategy = planner.plan(
            source_text=chunk["source_text"],
            source_language="en_US",
            target_language="tr_TR",
            genre="literary",
            style="sparse, biblical, violent, dry, archaic, unsentimental",
            work_id="blood_meridian",
            style_contract=style_contract,
            memory_context=style_contract_context(style_contract),
        )
        state = build_translation_state(
            chunk=chunk,
            index=index,
            previous_context=previous_context,
            strategy=strategy,
            language_context=language_context,
            style_contract=style_contract,
            style_guide=style_guide,
            glossary=glossary,
        )

        draft = translate_draft(state)
        state.update(draft)
        styled = stylize_translation(state)
        state.update(styled)
        translated = strip_response_wrappers(state["stylized_translation"] or state["raw_translation"] or "")

        checklist, revision_eval = build_and_evaluate(
            source_text=chunk["source_text"],
            translated_text=translated,
            genre="literary",
            source_language="en_US",
            target_language="tr_TR",
            translation_strategy=strategy,
            language_profile=language_context.get("target_language_profile"),
            style_contract=style_contract,
        )
        residue_before = detector.detect(
            translated,
            target_language="tr_TR",
            protected_terms=PROPER_NOUNS,
            proper_nouns=PROPER_NOUNS,
        )
        naturalness_result = naturalness.apply(
            translated,
            genre="literary",
            target_language="tr_TR",
            translation_strategy=strategy,
            revision_evaluation=revision_eval,
            revision_recommendations=revision_eval.get("revision_recommendations", []),
            language_profile=language_context.get("target_language_profile"),
            protected_terms=PROPER_NOUNS,
        )
        final_text = strip_response_wrappers(naturalness_result["revised_text"])
        residue_after = detector.detect(
            final_text,
            target_language="tr_TR",
            protected_terms=PROPER_NOUNS,
            proper_nouns=PROPER_NOUNS,
        )
        semantic_qa = semantic_checker.check(chunk["source_text"], final_text)
        fluency_qa = fluency_checker.check(final_text)
        gate = quality_gate.evaluate(
            source_quality=chunk["source_quality"],
            foreign_residue=residue_after,
            boundary_flags=chunk["boundary_flags"],
            semantic_flags=semantic_qa["flags"],
            fluency_flags=fluency_qa["flags"],
        )
        if naturalness_result["recommendation"] == "reject" and gate["recommendation"] == "accept":
            gate["recommendation"] = "review"

        record = {
            "chunk_id": chunk_id,
            "source_pages": chunk["source_pages"],
            "boundary_flags": chunk["boundary_flags"],
            "source_text": chunk["source_text"],
            "translation": final_text,
            "source_quality_score": chunk["source_quality"]["quality_score"],
            "source_repairs": chunk["source_repairs"],
            "strategy_used": True,
            "strategy_notes": strategy.get("translator_instructions", [])[:6],
            "revision_checklist_used": True,
            "revision_evaluation": revision_eval,
            "target_naturalness_used": True,
            "target_naturalness_result": naturalness_result,
            "foreign_residue_count_before_final": residue_before["foreign_residue_count"],
            "foreign_residue_count_after_final": residue_after["foreign_residue_count"],
            "foreign_residues": residue_after["residues"],
            "semantic_qa_flags": semantic_qa["flags"],
            "fluency_qa_flags": fluency_qa["flags"],
            "quality_gate": gate,
            "recommendation": gate["recommendation"],
        }
        translated_chunks.append(record)
        previous_context = summarize_previous_context(final_text)
    return translated_chunks


def build_translation_state(
    chunk: Dict[str, Any],
    index: int,
    previous_context: str,
    strategy: Dict[str, Any],
    language_context: Dict[str, Any],
    style_contract: Dict[str, Any],
    style_guide: str,
    glossary: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "source_text": chunk["source_text"],
        "source_language": "en_US",
        "target_language": "tr_TR",
        "style_preset": "literary",
        "style_guide": style_guide,
        "glossary": glossary,
        "positive_glossary": {},
        "negative_glossary": {},
        "idioms": [],
        "auto_glossary_candidates": {},
        "style_analysis": style_analysis(style_contract),
        "raw_translation": None,
        "stylized_translation": None,
        "critique": None,
        "is_approved": False,
        "revision_count": 0,
        "style_revision_count": 0,
        "final_translation": None,
        "logs": [],
        "previous_chunk_context": previous_context,
        "dynamic_glossary": [],
        "trace_id": None,
        "chunk_index": index,
        "user_id": None,
        "work_id": "blood_meridian",
        "genre": "literary",
        "enable_tie": True,
        "relevant_memories": [],
        "compact_memory_context": style_contract_context(style_contract),
        "memory_provenance": [],
        "loaded_memory_ids": [],
        "injected_memory_ids": [],
        "skipped_memory_ids": [],
        "routing_decisions": [],
        "routing_summary": {},
        "memory_effectiveness_records": [],
        "memory_effectiveness_summary": {},
        "translation_strategy": strategy,
        "language_profile": language_context.get("target_language_profile"),
        "source_language_profile": language_context.get("source_language_profile"),
        "target_language_profile": language_context.get("target_language_profile"),
        "strategy_planner_fallback_used": strategy.get("fallback_used"),
        "revision_checklist": None,
        "revision_evaluation": None,
        "revision_recommendations": [],
        "target_naturalness_result": None,
        "target_naturalness_revised_text": None,
        "target_naturalness_recommendation": None,
    }


def write_source_cleaned(
    pdf_path: Path,
    extracted: Dict[str, Any],
    cleanup: Dict[str, Any],
    quality: Dict[str, Any],
) -> None:
    lines = [
        "# Blood Meridian First 5 Pages Cleaned Source",
        "",
        f"- PDF path: `{pdf_path}`",
        f"- Scope: `chapter_1_first_5_content_pages`",
        f"- Chapter 1 start page: `{extracted['chapter_start_page']}`",
        f"- Pages used: `{extracted['pages_used']}`",
        f"- Source cleanup repairs: `{len(cleanup['repairs'])}`",
        f"- Source quality: `{quality['recommendation']}` score `{quality['quality_score']}`",
        "",
        "## Repair Summary",
        "",
    ]
    for repair in summarize_repairs(cleanup["repairs"]):
        lines.append(f"- `{repair}`")
    lines.extend(["", "## Cleaned Source", "", "```text", cleanup["cleaned_text"], "```", ""])
    (OUTPUTS_DIR / "blood_meridian_first5_source_cleaned.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def write_outputs(
    pdf_path: Path,
    extracted: Dict[str, Any],
    cleanup: Dict[str, Any],
    quality: Dict[str, Any],
    translated_chunks: List[Dict[str, Any]],
) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    translation_path = OUTPUTS_DIR / "blood_meridian_first5_translation_tr.md"
    review_path = OUTPUTS_DIR / "blood_meridian_first5_review_pack.md"
    metadata_path = OUTPUTS_DIR / "blood_meridian_first5_metadata.json"
    quality_path = OUTPUTS_DIR / "blood_meridian_first5_quality_report.md"

    translation_lines = ["# Blood Meridian First 5 Pages Turkish Translation", ""]
    translation_lines.append("\n\n".join(chunk["translation"] for chunk in translated_chunks))
    translation_lines.append("")
    translation_path.write_text("\n".join(translation_lines), encoding="utf-8")

    review_lines = ["# Blood Meridian First 5 Pages Review Pack", ""]
    for chunk in translated_chunks:
        review_lines.extend(
            [
                f"## Chunk ID: {chunk['chunk_id']}",
                "",
                f"- Source page range: `{chunk['source_pages']}`",
                f"- Recommendation: `{chunk['recommendation']}`",
                "",
                "### Chunk boundary QA",
                "",
                f"`{chunk['boundary_flags']}`",
                "",
                "### Source excerpt",
                "",
                "```text",
                chunk["source_text"][:1200],
                "```",
                "",
                "### Turkish translation",
                "",
                chunk["translation"],
                "",
                "### Source cleanup repairs",
                "",
                f"`{chunk['source_repairs']}`",
                "",
                "### Strategy notes",
                "",
                f"`{chunk['strategy_notes']}`",
                "",
                "### Revision checklist warnings",
                "",
                f"`{chunk['revision_evaluation'].get('revision_recommendations', [])}`",
                "",
                "### Target naturalness changes",
                "",
                f"`{chunk['target_naturalness_result'].get('changes', [])}`",
                "",
                "### Foreign residue QA",
                "",
                f"- Before final: `{chunk['foreign_residue_count_before_final']}`",
                f"- After final: `{chunk['foreign_residue_count_after_final']}`",
                f"- Residues: `{chunk['foreign_residues']}`",
                "",
                "### Literary semantic QA",
                "",
                f"`{chunk['semantic_qa_flags']}`",
                "",
                "### Turkish fluency QA",
                "",
                f"`{chunk['fluency_qa_flags']}`",
                "",
                "### Reviewer notes",
                "",
                "_Check literary rhythm, meaning, and proper noun handling._",
                "",
            ]
        )
    review_path.write_text("\n".join(review_lines), encoding="utf-8")

    metadata_chunks = [
        {
            "chunk_id": chunk["chunk_id"],
            "source_pages": chunk["source_pages"],
            "boundary_flags": chunk["boundary_flags"],
            "source_quality_score": chunk["source_quality_score"],
            "source_repairs": chunk["source_repairs"],
            "strategy_used": chunk["strategy_used"],
            "revision_checklist_used": chunk["revision_checklist_used"],
            "target_naturalness_used": chunk["target_naturalness_used"],
            "foreign_residue_count_before_final": chunk["foreign_residue_count_before_final"],
            "foreign_residue_count_after_final": chunk["foreign_residue_count_after_final"],
            "foreign_residues": chunk["foreign_residues"],
            "semantic_qa_flags": chunk["semantic_qa_flags"],
            "fluency_qa_flags": chunk["fluency_qa_flags"],
            "quality_gate": chunk["quality_gate"],
            "recommendation": chunk["recommendation"],
        }
        for chunk in translated_chunks
    ]
    metadata = {
        "pdf_path": str(pdf_path),
        "scope": "chapter_1_first_5_content_pages",
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "literary_fiction",
        "author": "Cormac McCarthy",
        "work_id": "blood_meridian",
        "pages_used": extracted["pages_used"],
        "chapter_1_start_page": extracted["chapter_start_page"],
        "source_cleanup": {
            "repairs_count": len(cleanup["repairs"]),
            "quality_score": quality["quality_score"],
            "recommendation": quality["recommendation"],
            "flags": quality["flags"],
        },
        "chunks": metadata_chunks,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    accepted = sum(chunk["recommendation"] == "accept" for chunk in translated_chunks)
    reviews = sum(chunk["recommendation"] == "review" for chunk in translated_chunks)
    rejects = sum(chunk["recommendation"] == "reject" for chunk in translated_chunks)
    residue_after = sum(chunk["foreign_residue_count_after_final"] for chunk in translated_chunks)
    review_chunks = [chunk["chunk_id"] for chunk in translated_chunks if chunk["recommendation"] != "accept"]
    boundary_flag_count = sum(len(chunk["boundary_flags"]) for chunk in translated_chunks)
    semantic_flag_count = sum(len(chunk["semantic_qa_flags"]) for chunk in translated_chunks)
    fluency_flag_count = sum(len(chunk["fluency_qa_flags"]) for chunk in translated_chunks)
    quality_lines = [
        "# Blood Meridian First 5 Pages Quality Report",
        "",
        "## 1. Executive Summary",
        "",
        "- This is a quick review artifact, not publication-ready copy.",
        f"- Chunks translated: `{len(translated_chunks)}`",
        f"- Accepted chunks: `{accepted}`",
        f"- Review chunks: `{reviews}`",
        f"- Rejected chunks: `{rejects}`",
        f"- Foreign residues remaining after final pass: `{residue_after}`",
        f"- Chunk boundary flags: `{boundary_flag_count}`",
        f"- Literary semantic QA flags: `{semantic_flag_count}`",
        f"- Turkish fluency QA flags: `{fluency_flag_count}`",
        "",
        "## 2. Pages Extracted",
        "",
        f"- Chapter 1 start page: `{extracted['chapter_start_page']}`",
        f"- Pages used: `{extracted['pages_used']}`",
        "",
        "## 3. Source Cleanup Summary",
        "",
        f"- Repairs applied: `{len(cleanup['repairs'])}`",
        f"- Source quality: `{quality['recommendation']}` score `{quality['quality_score']}`",
        f"- Source flags: `{quality['flags']}`",
        "",
        "## 4. Translation Pipeline Used",
        "",
        "- source cleanup -> source quality check -> strategy planner -> translator -> revision checklist -> target-only naturalness -> foreign residue QA",
        "",
        "## 5. Foreign Residue QA Summary",
        "",
        f"- Remaining residues after final pass: `{residue_after}`",
        "",
        "## 6. Literary Semantic and Fluency QA Summary",
        "",
        f"- Semantic flags: `{semantic_flag_count}`",
        f"- Fluency flags: `{fluency_flag_count}`",
        f"- Boundary flags: `{boundary_flag_count}`",
        "",
        "## 7. Chunks Requiring Review",
        "",
    ]
    if review_chunks:
        quality_lines.extend(f"- `{chunk_id}`" for chunk_id in review_chunks)
    else:
        quality_lines.append("_None flagged by deterministic QA._")
    quality_lines.extend(
        [
            "",
            "## 8. Known Literary Risks",
            "",
            "- This run does not prove literary quality.",
            "- Human review should verify voice, rhythm, and semantic precision.",
            "- Proper noun handling and archaic register still need human attention.",
            "",
            "## 9. Berkay Review Focus",
            "",
            "- Start with the opening page rhythm and whether fragments remain sharp in Turkish.",
            "- Then check meaning preservation on dense descriptive sentences.",
            "- Finally scan for any awkward modern Turkish or missed residue.",
            "",
        ]
    )
    quality_path.write_text("\n".join(quality_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
