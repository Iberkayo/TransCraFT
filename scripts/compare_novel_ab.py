"""Compare the existing Book Runner to a direct single-model literary translation.

Examples:
    python scripts/compare_novel_ab.py --input data/inputs/novel.epub --dry-run
    python scripts/compare_novel_ab.py --input data/inputs/novel.epub --provider openai --model YOUR_MODEL_ID
    python scripts/compare_novel_ab.py --input data/inputs/novel.epub --provider anthropic --model YOUR_CLAUDE_MODEL_ID
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark.novel_ab import run_novel_ab


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Local TXT, Markdown, EPUB or PDF")
    parser.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    parser.add_argument("--model", help="Direct challenger model ID; default is DEFAULT_MAIN_MODEL")
    parser.add_argument("--first-words", type=int, default=1000)
    parser.add_argument("--chunk-chars", type=int, default=3200)
    parser.add_argument("--output-root", default="outputs/novel_ab")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start-at", choices=["body", "beginning"], default="body")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Use synthetic translator stubs; does NOT evaluate real model quality.",
    )
    args = parser.parse_args(argv)

    report = run_novel_ab(
        args.input,
        model=args.model,
        provider=args.provider,
        first_words=args.first_words,
        chunk_chars=args.chunk_chars,
        output_root=args.output_root,
        seed=args.seed,
        start_at=args.start_at,
        dry_run=args.dry_run,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
