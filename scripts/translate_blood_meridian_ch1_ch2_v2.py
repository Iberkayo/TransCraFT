"""Generate Blood Meridian chapter 1-2 review outputs with v0.9.2 QA.

This script writes local review artifacts only. Do not commit the full chapter
translation outputs without explicit review.
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
from src.tie.foreign_residue import ForeignResidueDetector
from src.tie.revision_checklist import build_and_evaluate
from src.tie.source_cleanup import SourceExtractionCleaner, SourceExtractionQualityChecker
from src.tie.strategy_planner import TranslationStrategyPlanner
from src.tie.target_naturalness import TargetOnlyNaturalnessPass


PDF_CANDIDATES = [
    PROJECT_ROOT / "data" / "inputs" / "mccarthy_cormac_blood_meridianbooksee-org.pdf",
    PROJECT_ROOT / "data" / "mccarthy_cormac_blood_meridianbooksee-org.pdf",
    PROJECT_ROOT / "inputs" / "mccarthy_cormac_blood_meridianbooksee-org.pdf",
    PROJECT_ROOT / "mccarthy_cormac_blood_meridianbooksee-org.pdf",
]

PROPER_NOUNS = [
    "Memphis",
    "Saint Louis",
    "New Orleans",
    "Leonids",
    "Dipper",
    "Tennessee",
    "Texas",
    "Galveston",
    "Nacogdoches",
    "Fredonia",
    "Judge Holden",
    "Toadvine",
]


def main() -> None:
    Config.validate()
    pdf_path = find_pdf()
    chapters, boundaries = extract_chapters(pdf_path)

    cleaner = SourceExtractionCleaner()
    quality_checker = SourceExtractionQualityChecker()
    cleaned_chapters: Dict[str, Dict[str, Any]] = {}
    source_summary = {"repairs": [], "quality": {}}

    for chapter_id in ("1", "2"):
        cleanup = cleaner.clean(
            chapters[chapter_id]["text"],
            source_language="en_US",
            document_type="pdf",
            genre="literary_fiction",
        )
        quality = quality_checker.check(cleanup["cleaned_text"])
        cleaned_chapters[chapter_id] = {
            **chapters[chapter_id],
            "cleaned_text": cleanup["cleaned_text"],
            "cleanup": cleanup,
            "quality": quality,
        }
        source_summary["repairs"].extend(cleanup["repairs"])
        source_summary["quality"][chapter_id] = quality

    if any(cleaned_chapters[c]["quality"]["recommendation"] == "reject" for c in ("1", "2")):
        write_source_extract(pdf_path, cleaned_chapters, source_summary)
        raise SystemExit("Source extraction was rejected by quality checker; translation stopped.")

    chunks = build_chunks(cleaned_chapters)
    style_contract = load_style_contract()
    language_context = TranslationStrategyPlanner().language_profile_context("en_US", "tr_TR")
    style_guide = load_text(PROJECT_ROOT / "data" / "reference" / "literary" / "style_guide.txt")
    glossary = load_json(PROJECT_ROOT / "data" / "reference" / "literary" / "glossary.json", default=[])

    detector = ForeignResidueDetector()
    naturalness = TargetOnlyNaturalnessPass()
    planner = TranslationStrategyPlanner()
    translated_chunks: List[Dict[str, Any]] = []

    previous_context = "None (first chunk)"
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = f"bm_ch{chunk['chapter']}_{index:02d}"
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

        state = {
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

        recommendation = chunk_recommendation(
            chunk["source_quality"]["recommendation"],
            residue_after["recommendation"],
            naturalness_result["recommendation"],
        )

        record = {
            "chunk_id": chunk_id,
            "chapter": chunk["chapter"],
            "source_pages": chunk["source_pages"],
            "source_text": chunk["source_text"],
            "translation": final_text,
            "source_quality_score": chunk["source_quality"]["quality_score"],
            "source_repairs": chunk["source_repairs"],
            "strategy_used": True,
            "strategy_notes": strategy.get("translator_instructions", [])[:6],
            "revision_checklist_used": True,
            "revision_checklist": checklist,
            "revision_evaluation": revision_eval,
            "target_naturalness_used": True,
            "target_naturalness_result": naturalness_result,
            "foreign_residue_count_before_final": residue_before["foreign_residue_count"],
            "foreign_residue_count_after_final": residue_after["foreign_residue_count"],
            "foreign_residues": residue_after["residues"],
            "recommendation": recommendation,
        }
        translated_chunks.append(record)
        previous_context = summarize_previous_context(final_text)

    write_source_extract(pdf_path, cleaned_chapters, source_summary)
    write_translation_outputs(pdf_path, boundaries, cleaned_chapters, translated_chunks, source_summary)
    print("Blood Meridian v2 outputs written under outputs/. Full translation files are local review artifacts.")


def find_pdf() -> Path:
    for candidate in PDF_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Blood Meridian PDF not found in expected paths.")


def extract_chapters(pdf_path: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    offsets: List[int] = []
    parts: List[str] = []
    cursor = 0
    for page_number, text in enumerate(page_texts, start=1):
        offsets.append(cursor)
        page_blob = f"\n\n[[PAGE {page_number}]]\n\n{text}"
        parts.append(page_blob)
        cursor += len(page_blob)
    full_text = "".join(parts)

    markers = []
    for match in re.finditer(r"(?m)^\s*(I|II|III|IV|V|VI|VII|VIII|IX|X)\s*$", full_text):
        markers.append({"roman": match.group(1), "start": match.start(), "end": match.end(), "page": page_for_offset(offsets, match.start())})

    sequence = None
    for first in markers:
        if first["roman"] != "I":
            continue
        second = next((m for m in markers if m["roman"] == "II" and m["start"] > first["end"]), None)
        third = next((m for m in markers if m["roman"] == "III" and second and m["start"] > second["end"]), None)
        if second and third:
            sequence = (first, second, third)
            break

    if not sequence:
        raise RuntimeError(f"Could not confidently locate chapter I-II-III markers. Markers: {markers[:20]}")

    first, second, third = sequence
    chapter_one = full_text[first["end"]:second["start"]].strip()
    chapter_two = full_text[second["end"]:third["start"]].strip()

    chapters = {
        "1": {"text": strip_page_markers(chapter_one), "source_pages": page_range(first["page"], second["page"])},
        "2": {"text": strip_page_markers(chapter_two), "source_pages": page_range(second["page"], third["page"])},
    }
    boundaries = {
        "markers": {"I": first, "II": second, "III": third},
        "total_pages": len(page_texts),
    }
    return chapters, boundaries


def page_for_offset(offsets: List[int], offset: int) -> int:
    page = 1
    for index, start in enumerate(offsets, start=1):
        if start <= offset:
            page = index
        else:
            break
    return page


def page_range(start: int, end: int) -> List[int]:
    return list(range(start, max(start, end) + 1))


def strip_page_markers(text: str) -> str:
    return re.sub(r"\n*\[\[PAGE \d+\]\]\n*", "\n\n", text).strip()


def build_chunks(cleaned_chapters: Dict[str, Dict[str, Any]], max_chars: int = 3600) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    for chapter_id in ("1", "2"):
        chapter = cleaned_chapters[chapter_id]
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", chapter["cleaned_text"]) if p.strip()]
        current: List[str] = []
        current_len = 0
        for paragraph in paragraphs:
            units = split_large_paragraph(paragraph, max_chars)
            for unit in units:
                next_len = current_len + len(unit) + (2 if current else 0)
                if current and next_len > max_chars:
                    chunks.append(chunk_record(chapter_id, current, chapter))
                    current = []
                    current_len = 0
                current.append(unit)
                current_len += len(unit) + (2 if current else 0)
        if current:
            chunks.append(chunk_record(chapter_id, current, chapter))
    return chunks


def split_large_paragraph(paragraph: str, max_chars: int) -> List[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    units: List[str] = []
    current: List[str] = []
    size = 0
    for sentence in sentences:
        if current and size + len(sentence) + 1 > max_chars:
            units.append(" ".join(current).strip())
            current = []
            size = 0
        if len(sentence) > max_chars:
            units.extend(split_by_words(sentence, max_chars))
        else:
            current.append(sentence)
            size += len(sentence) + 1
    if current:
        units.append(" ".join(current).strip())
    return [unit for unit in units if unit]


def split_by_words(text: str, max_chars: int) -> List[str]:
    words = text.split()
    units = []
    current: List[str] = []
    size = 0
    for word in words:
        if current and size + len(word) + 1 > max_chars:
            units.append(" ".join(current))
            current = []
            size = 0
        current.append(word)
        size += len(word) + 1
    if current:
        units.append(" ".join(current))
    return units


def chunk_record(chapter_id: str, units: List[str], chapter: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chapter": chapter_id,
        "source_text": "\n\n".join(units).strip(),
        "source_pages": chapter["source_pages"],
        "source_repairs": summarize_repairs(chapter["cleanup"]["repairs"]),
        "source_quality": chapter["quality"],
    }


def load_style_contract() -> Dict[str, Any]:
    path = PROJECT_ROOT / "memory" / "works" / "blood_meridian" / "style" / "style_contract.json"
    if not path.exists():
        return {
            "tone": "sparse, biblical, violent, dry, archaic, unsentimental",
            "sentence_rhythm": "paratactic, fragment-preserving",
            "rules": [
                "Preserve short fragments where natural in Turkish.",
                "Avoid over-explaining imagery.",
            ],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def style_contract_context(contract: Dict[str, Any]) -> str:
    rules = "\n".join(f"- {rule}" for rule in contract.get("rules", []))
    return (
        "### Style & Narrative Voice Guidelines\n"
        f"* **Tone**: {contract.get('tone')}\n"
        f"* **Sentence Rhythm**: {contract.get('sentence_rhythm')}\n"
        "* **Directives**:\n"
        f"{rules}"
    )


def style_analysis(contract: Dict[str, Any]) -> str:
    return (
        "Preserve bleak literary tone, spare diction, concrete imagery, and source rhythm. "
        f"Tone: {contract.get('tone')}. Rhythm: {contract.get('sentence_rhythm')}."
    )


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def strip_response_wrappers(text: str) -> str:
    value = (text or "").strip()
    value = re.sub(r"^```(?:\w+)?\s*", "", value)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def chunk_recommendation(*recommendations: str) -> str:
    if "reject" in recommendations:
        return "reject"
    if "review" in recommendations:
        return "review"
    return "accept"


def summarize_previous_context(text: str) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    return compact[-700:] if len(compact) > 700 else compact


def summarize_repairs(repairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summarized = []
    for repair in repairs:
        item = {
            "type": repair.get("type"),
            "after": repair.get("after"),
            "confidence": repair.get("confidence"),
        }
        if repair.get("count") is not None:
            item["count"] = repair.get("count")
        summarized.append(item)
    return summarized


def write_source_extract(
    pdf_path: Path,
    cleaned_chapters: Dict[str, Dict[str, Any]],
    source_summary: Dict[str, Any],
) -> None:
    output = PROJECT_ROOT / "outputs" / "blood_meridian_ch1_ch2_source_extract_cleaned.md"
    lines = [
        "# Blood Meridian Ch1-Ch2 Cleaned Source Extract",
        "",
        f"- PDF path: `{pdf_path}`",
        f"- Chapters: `1`, `2`",
        f"- Total repairs applied: `{len(source_summary['repairs'])}`",
        "",
        "## Source Quality Recommendation",
        "",
    ]
    for chapter_id in ("1", "2"):
        quality = cleaned_chapters[chapter_id]["quality"]
        lines.append(f"- Chapter {chapter_id}: `{quality['recommendation']}` score `{quality['quality_score']}`")
    lines.extend(["", "## Repair Notes Summary", ""])
    for repair in summarize_repairs(source_summary["repairs"])[:50]:
        lines.append(f"- `{repair}`")
    if len(source_summary["repairs"]) > 50:
        lines.append(f"- ... {len(source_summary['repairs']) - 50} additional repairs")
    for chapter_id in ("1", "2"):
        lines.extend(
            [
                "",
                f"## Chapter {chapter_id}",
                "",
                "```text",
                cleaned_chapters[chapter_id]["cleaned_text"],
                "```",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")


def write_translation_outputs(
    pdf_path: Path,
    boundaries: Dict[str, Any],
    cleaned_chapters: Dict[str, Dict[str, Any]],
    translated_chunks: List[Dict[str, Any]],
    source_summary: Dict[str, Any],
) -> None:
    outputs = PROJECT_ROOT / "outputs"
    translation_path = outputs / "blood_meridian_ch1_ch2_translation_tr_v2.md"
    review_path = outputs / "blood_meridian_ch1_ch2_translation_review_pack_v2.md"
    metadata_path = outputs / "blood_meridian_ch1_ch2_translation_metadata_v2.json"
    quality_path = outputs / "blood_meridian_ch1_ch2_translation_quality_report_v2.md"

    translation_lines = ["# Blood Meridian Ch1-Ch2 Turkish Translation v2", ""]
    for chapter_id in ("1", "2"):
        translation_lines.extend([f"## Chapter {chapter_id}", ""])
        chapter_text = "\n\n".join(c["translation"] for c in translated_chunks if c["chapter"] == chapter_id)
        translation_lines.extend([chapter_text, ""])
    translation_path.write_text("\n".join(translation_lines), encoding="utf-8")

    review_lines = ["# Blood Meridian Ch1-Ch2 Translation Review Pack v2", ""]
    for chunk in translated_chunks:
        review_lines.extend(
            [
                f"## Chunk ID: {chunk['chunk_id']}",
                "",
                f"- Chapter: `{chunk['chapter']}`",
                f"- Source pages: `{chunk['source_pages']}`",
                f"- Recommendation: `{chunk['recommendation']}`",
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
                f"`{chunk['source_repairs'][:10]}`",
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
                "### Reviewer notes",
                "",
                "_Human review needed for literary quality, rhythm, and any chunks marked review/reject._",
                "",
            ]
        )
    review_path.write_text("\n".join(review_lines), encoding="utf-8")

    metadata_chunks = []
    for chunk in translated_chunks:
        metadata_chunks.append(
            {
                "chunk_id": chunk["chunk_id"],
                "chapter": chunk["chapter"],
                "source_pages": chunk["source_pages"],
                "source_quality_score": chunk["source_quality_score"],
                "source_repairs": chunk["source_repairs"],
                "strategy_used": chunk["strategy_used"],
                "revision_checklist_used": chunk["revision_checklist_used"],
                "target_naturalness_used": chunk["target_naturalness_used"],
                "foreign_residue_count_before_final": chunk["foreign_residue_count_before_final"],
                "foreign_residue_count_after_final": chunk["foreign_residue_count_after_final"],
                "foreign_residues": chunk["foreign_residues"],
                "recommendation": chunk["recommendation"],
            }
        )
    metadata = {
        "pdf_path": str(pdf_path),
        "chapters": ["1", "2"],
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "literary_fiction",
        "author": "Cormac McCarthy",
        "work_id": "blood_meridian",
        "chapter_boundaries": boundaries,
        "source_cleanup": {
            "total_repairs": len(source_summary["repairs"]),
            "chapter_quality": source_summary["quality"],
        },
        "chunks": metadata_chunks,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    accepted = sum(1 for c in translated_chunks if c["recommendation"] == "accept")
    reviews = sum(1 for c in translated_chunks if c["recommendation"] == "review")
    rejects = sum(1 for c in translated_chunks if c["recommendation"] == "reject")
    residue_remaining = sum(c["foreign_residue_count_after_final"] for c in translated_chunks)
    review_chunks = [c["chunk_id"] for c in translated_chunks if c["recommendation"] != "accept"]

    quality_lines = [
        "# Blood Meridian Ch1-Ch2 Translation Quality Report v2",
        "",
        "## 1. Executive Summary",
        "",
        f"- Chunks translated: `{len(translated_chunks)}`",
        f"- Accepted chunks: `{accepted}`",
        f"- Review chunks: `{reviews}`",
        f"- Rejected chunks: `{rejects}`",
        f"- Foreign residues remaining after final pass: `{residue_remaining}`",
        "- This is a review artifact, not publication-ready copy.",
        "",
        "## 2. Source Extraction Quality",
        "",
    ]
    for chapter_id in ("1", "2"):
        quality = cleaned_chapters[chapter_id]["quality"]
        quality_lines.append(f"- Chapter {chapter_id}: `{quality['recommendation']}` score `{quality['quality_score']}` flags `{quality['flags']}`")
    quality_lines.extend(
        [
            "",
            "## 3. Cleanup Repairs Applied",
            "",
            f"- Total repairs: `{len(source_summary['repairs'])}`",
            f"- Repair sample: `{source_summary['repairs'][:10]}`",
            "",
            "## 4. Translation Pipeline Used",
            "",
            "- raw PDF extraction -> source cleanup -> source quality check -> strategy planner -> translator -> stylist -> revision checklist -> residue QA -> target naturalness -> residue QA",
            "",
            "## 5. Foreign Residue QA Summary",
            "",
            f"- Remaining residues after final pass: `{residue_remaining}`",
            f"- Chunks requiring review/reject: `{review_chunks}`",
            "",
            "## 6. Target Naturalness Summary",
            "",
            f"- Naturalness pass used for all chunks: `{len(translated_chunks)}`",
            "",
            "## 7. Style Preservation Notes",
            "",
            "- Style contract was loaded read-only from work memory and passed as prompt context.",
            "- Human review should check whether sparse rhythm was preserved without stiff Turkish.",
            "",
            "## 8. Chunks Requiring Review",
            "",
        ]
    )
    if review_chunks:
        for chunk_id in review_chunks:
            quality_lines.append(f"- `{chunk_id}`")
    else:
        quality_lines.append("_None flagged by deterministic QA._")
    quality_lines.extend(
        [
            "",
            "## 9. Known Risks",
            "",
            "- Deterministic residue detection may miss fluent but semantically wrong translations.",
            "- Literary quality still requires human reading.",
            "- Chapter boundaries are inferred from PDF roman-numeral markers.",
            "",
            "## 10. Suggested Berkay Review Focus",
            "",
            "- First review chunks marked review/reject in the metadata.",
            "- Then compare Chapter 1 opening rhythm and Chapter 2 continuity.",
            "- Check proper noun handling and any remaining English-looking tokens.",
            "",
        ]
    )
    quality_path.write_text("\n".join(quality_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
