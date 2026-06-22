"""Query local private translation memory with safe terminal previews."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.tm_retrieval import (
    TranslationMemoryStore,
    build_reference_pack,
    retrieve_translation_memory,
)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    query = resolve_query(args)
    store = TranslationMemoryStore.from_directory(args.tm_dir)
    retrieved = retrieve_translation_memory(
        query_text=query,
        tm_entries=store.entries,
        top_k=args.top_k,
        min_alignment_confidence=args.min_confidence,
    )
    pack = build_reference_pack(
        query_text=query,
        retrieved=retrieved,
        max_chars_per_side=args.max_chars_per_side,
        warnings=store.warnings,
    )
    print_safe_summary(pack, tm_files=len(list(Path(args.tm_dir).glob("*_translation_memory.jsonl"))))
    if args.output_json:
        output_path = resolve_output_path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Reference pack written to: {output_path}")
    return 0


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tm-dir", default="outputs/parallel")
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("--query")
    query_group.add_argument("--query-file")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-confidence", choices=["high", "medium", "low"], default="medium")
    parser.add_argument("--max-chars-per-side", type=int, default=180)
    parser.add_argument("--output-json")
    return parser.parse_args(argv)


def resolve_query(args: argparse.Namespace) -> str:
    if args.query is not None:
        query = args.query.strip()
    else:
        query = Path(args.query_file).read_text(encoding="utf-8").strip()
    if not query:
        raise SystemExit("Query text is empty.")
    return query


def resolve_output_path(value: str) -> Path:
    requested = Path(value)
    if requested.is_absolute() or requested.parent != Path("."):
        return requested
    return PROJECT_ROOT / "outputs" / "tm_retrieval" / requested.name


def print_safe_summary(pack: Dict[str, Any], tm_files: int = 0) -> None:
    print(f"TM files discovered: {tm_files}")
    print(f"References returned: {len(pack.get('references', []))}")
    for index, reference in enumerate(pack.get("references", []), start=1):
        print(
            f"{index}. {reference['tm_id']} | pair={reference['pair_id']} | "
            f"score={reference['similarity_score']:.3f} | confidence={reference['alignment_confidence']}"
        )
        print(f"   source: {reference['source_preview']}")
        print(f"   target: {reference['target_preview']}")
    for warning in pack.get("warnings", []):
        print(f"warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main())
