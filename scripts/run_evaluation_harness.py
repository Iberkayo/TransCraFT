import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.evaluation.harness import (
    load_harness,
    render_markdown_report,
    scan_forbidden_phrases,
    summarize_cases,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic TransCraft leakage/provenance guardrail checks."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=PROJECT_ROOT / "data" / "eval" / "translation_harness_cases.json",
        help="Path to harness case JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "evaluation_harness_report.md",
        help="Markdown report output path.",
    )
    args = parser.parse_args()

    harness = load_harness(args.cases)
    summary = summarize_cases(harness["cases"])

    scan_paths = [
        PROJECT_ROOT / path
        for path in harness.get(
            "runtime_scan_paths",
            ["src/agents", "src/tie/style_contract.py", "memory/works"],
        )
    ]
    leakage_findings = scan_forbidden_phrases(scan_paths, harness.get("forbidden_runtime_phrases", []))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown_report(summary, leakage_findings), encoding="utf-8")

    print(f"Evaluation harness report written to: {args.output}")
    print(f"TIE ON win rate: {summary['tie_on_win_rate']:.2%}")
    if leakage_findings:
        print(f"Benchmark leakage findings: {len(leakage_findings)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
