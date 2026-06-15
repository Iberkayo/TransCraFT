import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_harness(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("cases"), list):
        raise ValueError("Harness file must contain a 'cases' list.")
    return data


def summarize_cases(cases: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    cases = list(cases)
    total = len(cases)
    tie_on_wins = sum(1 for case in cases if case.get("expected_winner") == "tie_on")
    tie_off_wins = sum(1 for case in cases if case.get("expected_winner") == "tie_off")
    ties = sum(1 for case in cases if case.get("expected_winner") == "tie")

    return {
        "total_cases": total,
        "tie_on_wins": tie_on_wins,
        "tie_off_wins": tie_off_wins,
        "ties": ties,
        "tie_on_win_rate": tie_on_wins / total if total else 0.0,
    }


def scan_forbidden_phrases(paths: Iterable[Path], forbidden_phrases: Iterable[str]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    phrases = [phrase for phrase in forbidden_phrases if phrase]

    for path in paths:
        if path.is_dir():
            files = [p for p in path.rglob("*") if p.is_file()]
        elif path.exists():
            files = [path]
        else:
            files = []

        for file_path in files:
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for phrase in phrases:
                if phrase in text:
                    findings.append({"path": str(file_path), "phrase": phrase})

    return findings


def render_markdown_report(summary: Dict[str, Any], leakage_findings: List[Dict[str, str]]) -> str:
    lines = [
        "# TransCraft Evaluation Harness Report",
        "",
        "## Scope",
        "",
        "This harness is currently a leakage/provenance guardrail. It is not yet a full blinded pairwise translation-quality benchmark.",
        "The fixture winner counts below summarize curated cases and should not be treated as proof of production translation quality.",
        "",
        "## Pairwise Fixture Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- TIE ON wins: {summary['tie_on_wins']}",
        f"- TIE OFF wins: {summary['tie_off_wins']}",
        f"- Ties: {summary['ties']}",
        f"- TIE ON win rate: {summary['tie_on_win_rate']:.2%}",
        "",
        "## Benchmark Leakage Scan",
        "",
    ]

    if leakage_findings:
        lines.append("Forbidden benchmark phrases were found in runtime files:")
        for finding in leakage_findings:
            lines.append(f"- `{finding['phrase']}` in `{finding['path']}`")
    else:
        lines.append("No forbidden benchmark phrases found in configured runtime files.")

    return "\n".join(lines) + "\n"
