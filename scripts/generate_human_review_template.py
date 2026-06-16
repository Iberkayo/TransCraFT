"""v0.9.1 — Generate fillable human review template from benchmark outputs and cases."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_cases(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pack(path: Path) -> Dict[str, str]:
    """Parse the human review pack markdown into a dict of case_id -> full_text."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    result: Dict[str, str] = {}
    current_id = ""
    current_lines: List[str] = []
    for line in text.splitlines():
        if line.startswith("## ") and not line.startswith("### "):
            if current_id:
                result[current_id] = "\n".join(current_lines)
            current_id = line[3:].strip()
            current_lines = [line]
        elif current_id:
            current_lines.append(line)
    if current_id:
        result[current_id] = "\n".join(current_lines)
    return result


def extract_outputs_from_pack(pack: Dict[str, str], case_id: str) -> Dict[str, str]:
    """Extract baseline, strategy, and full-chain outputs from pack text."""
    text = pack.get(case_id, "")
    outputs = {"baseline": "_Not available._", "strategy_only": "_Not available._", "full_chain": "_Not available._"}
    current_mode = ""
    for line in text.splitlines():
        if "### Baseline" in line:
            current_mode = "baseline"
        elif "### Strategy Only" in line:
            current_mode = "strategy_only"
        elif "### Full Chain" in line:
            current_mode = "full_chain"
        elif current_mode and line.startswith("> "):
            outputs[current_mode] = line[2:].strip()
        elif line.startswith("---"):
            current_mode = ""
    return outputs


def generate(args: Any) -> None:
    cases = load_cases(args.cases)
    pack = load_pack(args.pack)
    pack_available = bool(pack)
    template_data: List[Dict[str, Any]] = []

    md_lines = [
        "# Human Review Template — v0.9.1",
        "",
        "Fill this template manually. For each benchmark case, review the three outputs and answer the questions below.",
        "",
        "This is not an automatic evaluation. Heuristic metrics are approximate.",
        "Human review is required before quality claims.",
        "",
    ]

    for i, case in enumerate(cases, 1):
        case_id = case["id"]
        outputs = extract_outputs_from_pack(pack, case_id) if pack_available else {}
        baseline = outputs.get("baseline", "_Not available — run the benchmark first._")
        strategy = outputs.get("strategy_only", "_Not available — run the benchmark first._")
        full = outputs.get("full_chain", "_Not available — run the benchmark first._")

        entry = {
            "case_id": case_id,
            "reviewer": "",
            "preferred_output": "",
            "naturalness_winner": "",
            "meaning_preservation_winner": "",
            "least_translationese": "",
            "over_editing_detected": False,
            "protected_term_issue": False,
            "notes": "",
            "error_tags": [],
            "severity": "none",
        }
        template_data.append(entry)

        md_lines.extend([
            f"## Case {i}: {case_id}",
            "",
            f"**Genre:** {case.get('genre', '')}",
            f"**Risk types:** {', '.join(case.get('risk_type', []))}",
            f"**Expected behavior:** {case.get('expected_behavior', '')}",
            f"**Protected terms:** {', '.join(case.get('protected_terms', [])) or 'none'}",
            "",
            "### Source:",
            f"> {case['source_text']}",
            "",
            "### Baseline Output:",
            f"> {baseline}",
            "",
            "### Strategy-Only Output:",
            f"> {strategy}",
            "",
            "### Full Chain Output:",
            f"> {full}",
            "",
            "### Review Questions:",
            "1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)",
            "2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)",
            "3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)",
            "4. Did full_chain over-edit? (yes / no)",
            "5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)",
            "6. Preferred output: (baseline / strategy_only / full_chain / tie)",
            "7. Error tags: (see allowed list in human_review_schema.json)",
            "8. Severity: (none / minor / major / critical)",
            "9. Notes:",
            "",
            "---",
            "",
        ])

    if not pack_available:
        md_lines.insert(5, "**⚠ Outputs are not available. Run `python scripts/run_end_to_end_quality_benchmark.py` first to generate the human review pack.**")

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(template_data, ensure_ascii=False, indent=2), encoding="utf-8")
    args.md_output.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"JSON template: {args.json_output}")
    print(f"Markdown template: {args.md_output}")
    print(f"Outputs available: {pack_available}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate human review template.")
    parser.add_argument("--cases", type=Path, default=PROJECT_ROOT / "data" / "eval" / "end_to_end_quality_cases.json")
    parser.add_argument("--pack", type=Path, default=PROJECT_ROOT / "outputs" / "end_to_end_human_review_pack.md")
    parser.add_argument("--json-output", type=Path, default=PROJECT_ROOT / "outputs" / "human_review_template.json")
    parser.add_argument("--md-output", type=Path, default=PROJECT_ROOT / "outputs" / "human_review_template.md")
    args = parser.parse_args()
    generate(args)


if __name__ == "__main__":
    main()