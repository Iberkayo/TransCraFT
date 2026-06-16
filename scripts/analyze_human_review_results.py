"""v0.9.1 — Analyze filled human review results and generate calibration report."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.error_taxonomy import ErrorTaxonomyAnalyzer


def load_reviews(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def render_report(reviews: List[Dict[str, Any]], output_path: Path) -> Path:
    summary = ErrorTaxonomyAnalyzer.summarize_calibration(reviews)
    lines = [
        "# Human Review Calibration Report — v0.9.1",
        "",
    ]

    if not reviews:
        lines.extend([
            "## No Real Human Review Results Found",
            "",
            "No completed human review results were found.",
            "The review template is ready. Run manual review first, then rerun this analyzer.",
            "",
            "See:",
            "- `outputs/human_review_template.md`",
            "- `outputs/human_review_template.json`",
            "- `data/eval/human_review_schema.json`",
            "",
            "After filling the review results into `outputs/human_review_results.json`, re-run:",
            "```bash",
            "python scripts/analyze_human_review_results.py",
            "```",
        ])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    # Real results exist
    lines.extend([
        "## 1. Executive Summary",
        "",
        f"- Total reviewed: {summary['total_reviewed']}",
        f"- Baseline wins: {summary['baseline_wins']}",
        f"- Strategy-only wins: {summary['strategy_only_wins']}",
        f"- Full-chain wins: {summary['full_chain_wins']}",
        f"- Ties: {summary['ties']}",
        f"- Cannot judge: {summary.get('cannot_judge', 0)}",
        f"- Full-chain over-edit count: {summary['full_chain_over_edit_count']}",
        f"- Protected term issues: {summary['protected_term_issue_count']}",
        f"- Critical errors: {summary['critical_errors']}",
        f"- Major errors: {summary['major_errors']}",
        f"- Minor errors: {summary['minor_errors']}",
        f"- Full-chain win rate: {summary['full_chain_win_rate']:.1%}",
        f"- Full-chain harm rate: {summary['full_chain_harm_rate']:.1%}",
        "",
        "This is not a human evaluation unless a human filled the review results.",
        "Heuristic metrics are approximate. Meaning preservation cannot be fully verified automatically.",
        "Synthetic cases are limited. Human review is required before quality claims.",
        "",
        "## 2. Error Tag Frequency",
        "",
    ])

    tags = summary.get("error_tag_frequency", {})
    if tags:
        lines.append("| Error Tag | Count |")
        lines.append("| --------- | ----: |")
        for tag, count in sorted(tags.items(), key=lambda x: -x[1]):
            lines.append(f"| {tag} | {count} |")
        lines.append("")
    else:
        lines.append("_No error tags recorded._")

    lines.extend([
        "## 3. Top Error Categories & Recommended Fixes",
        "",
    ])
    for fix in summary.get("recommendations", []):
        lines.append(f"- {fix}")

    lines.extend([
        "",
        "## 4. Severity Distribution",
        "",
    ])

    lines.extend([
        "",
        "## 5. Recommendations",
        "",
    ])
    for fix in summary.get("recommendations", []):
        lines.append(f"- {fix}")
    if not summary.get("recommendations"):
        lines.append("- No recommendations — insufficient error data.")

    lines.extend([
        "",
        "## 6. Notes on Limitations",
        "",
        "- This report is only as reliable as the human review data.",
        "- Error taxonomy is deterministic but coarse; human judgment nuances may not be captured.",
        "- Synthetic benchmark cases are limited; real-world performance may differ.",
        "- Human review is required before quality claims.",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze human review results.")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "outputs" / "human_review_results.json")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "human_review_calibration_report.md")
    args = parser.parse_args()

    reviews = load_reviews(args.input)
    output = render_report(reviews, args.output)
    print(f"Calibration report: {output}")
    print(f"Reviews loaded: {len(reviews)}")


if __name__ == "__main__":
    main()