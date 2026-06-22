"""Build local private parallel-corpus alignment artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.parallel_corpus import (
    align_parallel_units,
    build_parallel_style_profile,
    build_translation_memory,
    discover_parallel_candidates,
    extract_glossary_candidates,
    extract_pdf_text_by_page,
    segment_text_units,
    write_parallel_artifacts,
)


def main() -> None:
    args = parse_args()
    candidates = discover_parallel_candidates(
        input_root=args.input_root,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
    )
    if args.pair_id:
        candidates = [candidate for candidate in candidates if candidate["pair_id"] == args.pair_id]
    if args.max_pairs is not None:
        candidates = candidates[: args.max_pairs]
    if not candidates:
        raise SystemExit("No parallel document pair candidates were discovered.")

    output_dir = PROJECT_ROOT / "outputs" / "parallel"
    build_records: List[Dict[str, Any]] = []
    for pair in candidates:
        source = extract_pdf_text_by_page(pair["source_path"], max_pages=args.max_pages)
        target = extract_pdf_text_by_page(pair["target_path"], max_pages=args.max_pages)
        source_units = segment_text_units(source["text"], mode=args.mode)
        target_units = segment_text_units(target["text"], mode=args.mode)
        source_units = _prefix_unit_ids(source_units, "src")
        target_units = _prefix_unit_ids(target_units, "trg")
        alignment = align_parallel_units(
            source_units,
            target_units,
            pair_id=pair["pair_id"],
            source_lang=pair["source_lang"],
            target_lang=pair["target_lang"],
        )
        translation_memory = build_translation_memory(alignment)
        glossary = extract_glossary_candidates(alignment)
        style_profile = build_parallel_style_profile(alignment)
        result = {
            "pair": pair,
            "source_extraction": source,
            "target_extraction": target,
            "alignment": alignment,
            "translation_memory": translation_memory,
            "glossary_candidates": glossary,
            "style_profile": style_profile,
        }
        paths = write_parallel_artifacts(result, str(output_dir)) if args.write_local_artifacts else {}
        record = {
            "pair_id": pair["pair_id"],
            "match_confidence": pair["match_confidence"],
            "source_file": Path(pair["source_path"]).name,
            "target_file": Path(pair["target_path"]).name,
            "source_pages_processed": source["pages_extracted"],
            "target_pages_processed": target["pages_extracted"],
            "source_units": alignment["source_units"],
            "target_units": alignment["target_units"],
            "aligned_units": len(alignment["aligned_units"]),
            "alignment_quality": alignment["alignment_quality"],
            "translation_memory_entries": len(translation_memory),
            "glossary_candidates": len(glossary),
            "style_profile_generated": bool(style_profile),
            "local_output_paths": paths,
        }
        build_records.append(record)
        print(
            f"{pair['pair_id']}: pages {source['pages_extracted']}/{target['pages_extracted']}, "
            f"units {alignment['source_units']}/{alignment['target_units']}, "
            f"aligned {len(alignment['aligned_units'])}, quality {alignment['alignment_quality']}"
        )

    if args.write_local_artifacts:
        output_dir.mkdir(parents=True, exist_ok=True)
        combined_path = output_dir / "parallel_corpus_build_report.md"
        combined_path.write_text(build_report(candidates, build_records, args), encoding="utf-8")
        summary_path = output_dir / "parallel_corpus_build_summary.json"
        summary_path.write_text(
            json.dumps({"pairs": build_records}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Combined report: {combined_path}")
    print(f"Pairs processed: {len(build_records)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", default="data/inputs")
    parser.add_argument("--source-lang", default="EN")
    parser.add_argument("--target-lang", default="TR")
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--max-pairs", type=int)
    parser.add_argument("--pair-id")
    parser.add_argument("--mode", choices=["paragraph", "sentence", "page"], default="paragraph")
    parser.add_argument(
        "--write-local-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write private full-text artifacts under outputs/parallel (default: true).",
    )
    return parser.parse_args()


def build_report(
    candidates: List[Dict[str, Any]],
    records: List[Dict[str, Any]],
    args: argparse.Namespace,
) -> str:
    confidence = Counter(candidate["match_confidence"] for candidate in candidates)
    lines = [
        "# Parallel Corpus Build Report",
        "",
        "This report contains filenames, counts, and hashes/metadata only. Full aligned text remains local and untracked.",
        "",
        f"- Source language folder: `{args.source_lang}`",
        f"- Target language folder: `{args.target_lang}`",
        f"- Max pages per document: `{args.max_pages}`",
        f"- Pair candidates: `{len(candidates)}`",
        f"- Match confidence distribution: `{dict(confidence)}`",
        "",
        "## Processed Pairs",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"### {record['pair_id']}",
                "",
                f"- Source file: `{record['source_file']}`",
                f"- Target file: `{record['target_file']}`",
                f"- Pages processed: `{record['source_pages_processed']}` / `{record['target_pages_processed']}`",
                f"- Source/target units: `{record['source_units']}` / `{record['target_units']}`",
                f"- Aligned units: `{record['aligned_units']}`",
                f"- Alignment quality: `{record['alignment_quality']}`",
                f"- TM entries: `{record['translation_memory_entries']}`",
                f"- Glossary candidates: `{record['glossary_candidates']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            "",
            "- Input PDFs were read in place and were not copied.",
            "- Full extracted and aligned text is stored only in ignored local artifacts.",
            "- Translation memory is private reference data, not fine-tuning data.",
            "- Alignment is heuristic and requires human review.",
            "",
        ]
    )
    return "\n".join(lines)


def _prefix_unit_ids(units: List[Dict[str, Any]], prefix: str) -> List[Dict[str, Any]]:
    result = []
    for index, unit in enumerate(units, start=1):
        item = dict(unit)
        item["unit_id"] = f"{prefix}_{index:06d}"
        result.append(item)
    return result


if __name__ == "__main__":
    main()
