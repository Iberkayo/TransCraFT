"""CLI script for TIE v0.4.1 Memory Hygiene & Pruning.

Usage:
    python scripts/run_memory_hygiene.py --dry-run      (default, no mutations)
    python scripts/run_memory_hygiene.py --apply          (persist hygiene metadata)
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.memory_hygiene import MemoryHygieneManager
from src.tie.memory_manager import MemoryManager


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TIE v0.4.1 — Evaluate and apply memory hygiene decisions."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Generate recommendations without mutating memory files (default).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Persist hygiene metadata into memory files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "memory_hygiene_report.md",
        help="Path for the hygiene report.",
    )
    args = parser.parse_args()

    # Resolve mode: if --apply is explicitly passed, it overrides the default dry-run
    if args.apply:
        dry_run = False
    else:
        dry_run = args.dry_run

    print("=== TIE v0.4.1 Memory Hygiene ===")
    print(f"Mode: {'DRY-RUN (no mutations)' if dry_run else 'APPLY (will update memory metadata)'}")

    # Load all memory items (disable backups in dry-run mode)
    manager = MemoryManager(enable_backups=not dry_run)
    memory_items = manager.all_memory_items()

    if not memory_items:
        print("No memory items found. Nothing to evaluate.")
        return

    print(f"Loaded {len(memory_items)} memory items from all scopes.")

    # Evaluate hygiene
    hygiene = MemoryHygieneManager(dry_run=dry_run, memory_dir=manager.base_dir)
    recommendations = hygiene.evaluate(memory_items)

    # Generate report
    output_path = hygiene.generate_report(recommendations, args.output)
    print(f"Hygiene report written to: {output_path}")

    # Print summary to stdout
    from collections import Counter
    decision_counts = Counter(r["decision"] for r in recommendations)
    print(f"\nSummary:")
    print(f"  Promote:         {decision_counts.get('promote', 0)}")
    print(f"  Keep:            {decision_counts.get('keep', 0)}")
    print(f"  Downgrade:       {decision_counts.get('downgrade', 0)}")
    print(f"  Review:          {decision_counts.get('review', 0)}")
    print(f"  Retire Candidate: {decision_counts.get('retire_candidate', 0)}")

    # Apply if requested
    if not dry_run:
        memory_items, mutations = hygiene.apply(memory_items, recommendations)

        # Persist mutations back to files
        # We know each item has a _source_path
        from collections import defaultdict
        files_to_items: dict = defaultdict(list)
        for item in memory_items:
            src = item.get("_source_path")
            if src:
                files_to_items[src].append(item)

        import json
        saved_count = 0
        for file_path_str, items in files_to_items.items():
            file_path = Path(file_path_str)
            # Strip internal keys before saving
            clean_items = []
            for item in items:
                clean = {k: v for k, v in item.items() if not k.startswith("_")}
                # Ensure hygiene fields are in output
                hygiene_fields = [
                    "hygiene_status", "hygiene_reason", "hygiene_updated_at",
                    "effectiveness_observation_count", "previous_importance_score",
                ]
                for hf in hygiene_fields:
                    if hf not in clean:
                        clean[hf] = None
                clean_items.append(clean)

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(clean_items, f, ensure_ascii=False, indent=2)
            saved_count += 1

        print(f"\nApplied mutations to {saved_count} memory file(s).")
        print(f"Updated {mutations} memory record(s) with hygiene metadata.")

    if dry_run:
        print("\n>>> This was a DRY-RUN. No memory files were modified.")
        print(">>> Run with --apply to persist hygiene metadata.")

    print("\nDone.")


if __name__ == "__main__":
    main()