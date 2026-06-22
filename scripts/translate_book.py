"""Translate a bounded range from a generic local book file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.book_runner import BookTranslationRunner, build_book_run_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--source", default="en")
    parser.add_argument("--target", default="tr")
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument("--first-pages", type=int)
    range_group.add_argument("--first-words", type=int)
    parser.add_argument("--words-per-page", type=int, default=300)
    parser.add_argument("--chunk-chars", type=int, default=3200)
    parser.add_argument("--tm-dir", default="outputs/parallel")
    parser.add_argument("--tm-top-k", type=int, default=3)
    parser.add_argument("--tm-min-confidence", choices=["high", "medium", "low"], default="high")
    parser.add_argument("--no-tm", action="store_true")
    parser.add_argument("--output-root", default="outputs/book_runs")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--md", action="store_true")
    parser.add_argument("--side-by-side", action="store_true")
    parser.add_argument("--quality-report", action="store_true")
    parser.add_argument("--metadata", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    explicit_outputs = any(
        [args.pdf, args.md, args.side_by_side, args.quality_report, args.metadata]
    )
    config = build_book_run_config(
        input_path=args.input,
        source_language=args.source,
        target_language=args.target,
        first_pages=args.first_pages,
        first_words=args.first_words,
        words_per_page=args.words_per_page,
        chunk_chars=args.chunk_chars,
        tm_enabled=not args.no_tm,
        tm_dir=args.tm_dir,
        tm_top_k=args.tm_top_k,
        tm_min_confidence=args.tm_min_confidence,
        output_root=args.output_root,
        write_pdf=args.pdf,
        write_markdown=args.md if explicit_outputs else True,
        write_side_by_side=args.side_by_side,
        write_quality_report=args.quality_report if explicit_outputs else True,
        write_metadata=args.metadata if explicit_outputs else True,
    )
    result = BookTranslationRunner().run(config)
    print(f"Run: {result.run_id}")
    print(f"Chunks: {result.chunks_translated}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Output directory: {Path(result.output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
