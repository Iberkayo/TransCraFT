"""Aggregate a completed, blinded human review after its A/B choices are frozen."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

METRICS = ("accuracy", "naturalness", "literary_voice")
ARMS = ("baseline", "direct")


def score_novel_ab(run_dir: str | Path, scored_file: str | Path) -> dict[str, Any]:
    """Validate per-passage human judgments and reveal arm mapping.

    IMPORTANT: This tool does not provide model-generated quality claims.
    It only summarizes values manually supplied by a human reviewer.
    """
    root = Path(run_dir).expanduser().resolve()
    comparison = json.loads((root / "comparison.json").read_text(encoding="utf-8"))
    if comparison.get("status") == "dry_run_no_model_calls":
        raise ValueError("Dry run contains no real translations; cannot produce a quality winner.")
    keys = json.loads((root / "answer_key.json").read_text(encoding="utf-8"))
    scores = json.loads(Path(scored_file).read_text(encoding="utf-8"))
    passages = scores.get("passages", [])
    if not isinstance(passages, list):
        raise ValueError("human scores must include a passages array.")
    actual = [str(row.get("passage_id", "")) for row in passages]
    if set(actual) != set(keys) or len(actual) != len(keys):
        raise ValueError("Score entries must match all unique passage IDs in the answer key.")

    buckets = {arm: {metric: [] for metric in METRICS} for arm in ARMS}
    preferences = {"baseline": 0, "direct": 0, "tie": 0}
    for passage in passages:
        passage_id = passage["passage_id"]
        labels = keys[passage_id]
        if set(labels) != {"A", "B"} or set(labels.values()) != set(ARMS):
            raise ValueError(f"Corrupt answer key for {passage_id}")
        preference = passage.get("preference")
        if preference not in {"A", "B", "tie"}:
            raise ValueError(f"{passage_id}: preference must be A, B, or tie.")
        preferences[labels[preference] if preference != "tie" else "tie"] += 1
        for metric in METRICS:
            dimensions = passage.get(metric, {})
            for label in ("A", "B"):
                value = dimensions.get(label) if isinstance(dimensions, dict) else None
                if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                    raise ValueError(f"{passage_id} {metric} {label}: expected integer 1..5.")
                buckets[labels[label]][metric].append(value)

    means = {
        arm: {
            metric: round(mean(buckets[arm][metric]), 3)
            for metric in METRICS
        }
        for arm in ARMS
    }
    if preferences["direct"] > preferences["baseline"]:
        preferred = "direct"
    elif preferences["baseline"] > preferences["direct"]:
        preferred = "baseline"
    else:
        preferred = "tie"
    result = {
        "status": "completed_human_review",
        "passage_count": len(passages),
        "direct_model": comparison.get("direct_model"),
        "baseline_model": comparison.get("baseline_model"),
        "preference_counts": preferences,
        "mean_human_scores": means,
        "most_preferred_arm": preferred,
        "note": (
            "This is a descriptive summary of human preferences, not a statistically "
            "validated claim of superiority. More blinded reviewers and books are needed."
        ),
    }
    (root / "human_review_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Human-reviewed EN → TR book translation comparison",
        "",
        f"- Passages reviewed: {len(passages)}",
        f"- Preference votes: baseline {preferences['baseline']}, "
        f"direct {preferences['direct']}, tie {preferences['tie']}",
        f"- Most-preferred arm (descriptive only): **{preferred}**",
        "",
        "| Arm | Meaning fidelity | Turkish naturalness | Literary voice |",
        "| --- | ---: | ---: | ---: |",
    ]
    for arm in ARMS:
        lines.append(
            f"| {arm} | {means[arm]['accuracy']:.2f} | "
            f"{means[arm]['naturalness']:.2f} | "
            f"{means[arm]['literary_voice']:.2f} |"
        )
    lines.extend(["", result["note"], ""])
    (root / "human_review_summary.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument(
        "--scores", required=True,
        help="Completed copy of human_scores.template.json (no empty metrics).",
    )
    args = parser.parse_args(argv)
    result = score_novel_ab(args.run_dir, args.scores)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
