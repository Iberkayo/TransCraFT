"""Generate diagnostics for the TIE v0.5 memory-aware context router."""

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import Config
from src.tie.memory_manager import MemoryManager
from src.tie.router import ContextRouter


DEFAULT_SAMPLES = [
    {
        "name": "Alice sample",
        "source": "Alice saw the White Rabbit and the jar marked ORANGE MARMALADE.",
        "genre": "literary",
        "work_id": "alice_in_wonderland",
    },
    {
        "name": "Blood Meridian sample",
        "source": "Judge Holden and the kid cross the dark fields. He stokes the scullery fire.",
        "genre": "literary",
        "work_id": "blood_meridian",
    },
    {
        "name": "Attention sample",
        "source": "The Transformer uses attention mechanisms without recurrent neural networks.",
        "genre": "tech",
        "work_id": "attention_is_all_you_need",
    },
]


def run_diagnostics(max_memory_items: int = 20) -> Dict[str, Any]:
    manager = MemoryManager(base_dir=Config.MEMORY_DIR, enable_backups=False)
    router = ContextRouter(memory_manager=manager, enable_memory_aware=True, record_usage=False)

    all_decisions: List[Dict[str, Any]] = []
    loaded_ids = set()
    injected_ids = set()
    skipped_ids = set()

    for sample in DEFAULT_SAMPLES:
        router.retrieve_relevant_memory(
            source_text=sample["source"],
            genre=sample["genre"],
            work_id=sample["work_id"],
            max_memory_items=max_memory_items,
        )
        loaded_ids.update(router.last_loaded_memory_ids)
        injected_ids.update(router.last_injected_memory_ids)
        skipped_ids.update(router.last_skipped_memory_ids)
        for decision in router.last_routing_decisions:
            enriched = decision.copy()
            enriched["sample"] = sample["name"]
            all_decisions.append(enriched)

    summary = summarize(all_decisions, loaded_ids, injected_ids, skipped_ids)
    return {
        "summary": summary,
        "decisions": all_decisions,
    }


def summarize(
    decisions: List[Dict[str, Any]],
    loaded_ids: set,
    injected_ids: set,
    skipped_ids: set,
) -> Dict[str, Any]:
    injected = [d for d in decisions if d.get("decision") == "inject"]
    skipped = [d for d in decisions if d.get("decision") in {"skip", "downrank"}]
    global_injected = [d for d in injected if d.get("scope") == "global"]
    promoted_injected = [d for d in injected if d.get("hygiene_status") == "promote"]
    retire_skipped = [d for d in skipped if d.get("hygiene_status") == "retire_candidate"]
    downgraded_skipped = [d for d in skipped if d.get("hygiene_status") == "downgrade"]
    avg_score = sum(float(d.get("final_score", 0.0) or 0.0) for d in injected) / len(injected) if injected else 0.0
    return {
        "total_loaded": len(loaded_ids),
        "total_injected": len(injected_ids),
        "total_skipped": len(skipped_ids),
        "global_memory_share": len(global_injected) / len(injected) if injected else 0.0,
        "promoted_injected": len(promoted_injected),
        "downgraded_skipped": len(downgraded_skipped),
        "retire_candidate_skipped": len(retire_skipped),
        "average_injected_score": avg_score,
    }


def generate_report(result: Dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = result["summary"]
    decisions = result["decisions"]
    injected = unique_records([d for d in decisions if d.get("decision") == "inject"], prefer_high_score=True)
    skipped = unique_records([d for d in decisions if d.get("decision") in {"skip", "downrank"}], prefer_high_score=False)

    lines = [
        "# Router Diagnostics Report",
        "",
        "## 1. Executive Summary",
        "",
        f"- Total memories loaded: {summary['total_loaded']}",
        f"- Total memories injected: {summary['total_injected']}",
        f"- Total memories skipped: {summary['total_skipped']}",
        f"- Global memory share: {summary['global_memory_share']:.2%}",
        f"- Promoted memories injected: {summary['promoted_injected']}",
        f"- Retire candidates skipped: {summary['retire_candidate_skipped']}",
        f"- Average injected score: {summary['average_injected_score']:.2f}",
        "",
        "## 2. Total Memories Loaded",
        "",
        f"{summary['total_loaded']}",
        "",
        "## 3. Total Memories Injected",
        "",
        f"{summary['total_injected']}",
        "",
        "## 4. Total Memories Skipped",
        "",
        f"{summary['total_skipped']}",
        "",
        "## 5. Promoted Memories Injected",
        "",
        table([d for d in injected if d.get("hygiene_status") == "promote"]),
        "",
        "## 6. Downgraded Memories Skipped",
        "",
        table([d for d in skipped if d.get("hygiene_status") == "downgrade"]),
        "",
        "## 7. Retire Candidates Skipped",
        "",
        table([d for d in skipped if d.get("hygiene_status") == "retire_candidate"]),
        "",
        "## 8. Global Memory Share",
        "",
        f"{summary['global_memory_share']:.2%}",
        "",
        "## 9. Top Injected Memories",
        "",
        table(sorted(injected, key=lambda d: d.get("final_score", 0.0), reverse=True)[:20]),
        "",
        "## 10. Top Skipped Memories",
        "",
        table(sorted(skipped, key=lambda d: d.get("final_score", 0.0))[:20]),
        "",
        "## 11. Recommendations",
        "",
        *recommendations(summary, decisions),
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def table(records: List[Dict[str, Any]]) -> str:
    if not records:
        return "_No records._"
    lines = [
        "| Memory ID | Key | Scope | Hygiene | Impact | Score | Decision | Reason |",
        "| --------- | --- | ----- | ------- | -----: | ----: | -------- | ------ |",
    ]
    for record in records:
        lines.append(
            "| {memory_id} | {key} | {scope} | {hygiene} | {impact:.2f} | {score:.2f} | {decision} | {reason} |".format(
                memory_id=cell(record.get("memory_id")),
                key=cell(record.get("key")),
                scope=cell(record.get("scope")),
                hygiene=cell(record.get("hygiene_status")),
                impact=float(record.get("estimated_quality_impact_avg", 0.0) or 0.0),
                score=float(record.get("final_score", 0.0) or 0.0),
                decision=cell(record.get("decision")),
                reason=cell(record.get("reason")),
            )
        )
    return "\n".join(lines)


def unique_records(records: List[Dict[str, Any]], prefer_high_score: bool) -> List[Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for record in records:
        key = str(record.get("memory_id") or f"{record.get('scope')}|{record.get('type')}|{record.get('key')}")
        existing = by_id.get(key)
        if existing is None:
            by_id[key] = record
            continue
        current_score = float(record.get("final_score", 0.0) or 0.0)
        existing_score = float(existing.get("final_score", 0.0) or 0.0)
        if (prefer_high_score and current_score > existing_score) or (
            not prefer_high_score and current_score < existing_score
        ):
            by_id[key] = record
    return list(by_id.values())


def recommendations(summary: Dict[str, Any], decisions: List[Dict[str, Any]]) -> List[str]:
    lines = []
    if summary["total_loaded"] == 0:
        return ["- No memory was available for router diagnostics."]
    if summary["global_memory_share"] <= 0.30:
        lines.append("- Global memory share is within the v0.5 target cap.")
    else:
        lines.append("- Global memory share remains high; tighten relevance thresholds or hygiene more aggressively.")
    if summary["retire_candidate_skipped"] > 0:
        lines.append("- Retire candidates are being kept out of prompt context.")
    if summary["promoted_injected"] > 0:
        lines.append("- Promoted memories are successfully reaching prompt context.")
    skipped_reasons = Counter(d.get("reason", "") for d in decisions if d.get("decision") in {"skip", "downrank"})
    if skipped_reasons:
        top_reason = skipped_reasons.most_common(1)[0][0]
        lines.append(f"- Most common skip/downrank reason: {top_reason}")
    return lines


def cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TIE v0.5 memory-aware router diagnostics.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "router_diagnostics_report.md",
    )
    parser.add_argument("--max-memory-items", type=int, default=20)
    args = parser.parse_args()

    result = run_diagnostics(max_memory_items=args.max_memory_items)
    output_path = generate_report(result, args.output)
    summary = result["summary"]

    print(f"Router diagnostics report written to: {output_path}")
    print(f"Loaded: {summary['total_loaded']}")
    print(f"Injected: {summary['total_injected']}")
    print(f"Skipped: {summary['total_skipped']}")
    print(f"Global memory share: {summary['global_memory_share']:.2%}")


if __name__ == "__main__":
    main()
