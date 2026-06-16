"""Run v0.7 revision checklist diagnostics on small synthetic EN->TR samples."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.revision_checklist import RevisionChecklistBuilder, RevisionChecklistEvaluator


SYNTHETIC_CASES = [
    {
        "id": "business_translationese",
        "genre": "business",
        "source": "The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.",
        "draft": (
            "Eski yazılımın 3. çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor, "
            "bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu."
        ),
        "expected_issues": ["translationese", "long relative clause"],
    },
    {
        "id": "literary_fragment",
        "genre": "literary",
        "source": "He stood at the door. Silent. Waiting.",
        "draft": "Kapıda durdu. Sessizce. Bekleyerek.",
        "expected_issues": [],
    },
    {
        "id": "pronoun_heavy",
        "genre": "general",
        "source": "She told him that she would send him the file when she finished reviewing it.",
        "draft": "O, ona dosyayı incelemeyi bitirdiğinde onu ona göndereceğini söyledi.",
        "expected_issues": ["pronouns"],
    },
]


def render_report(cases: List[Dict[str, Any]], output_path: Path) -> Path:
    builder = RevisionChecklistBuilder()
    evaluator = RevisionChecklistEvaluator()
    lines = [
        "# Revision Checklist Diagnostics Report",
        "",
        "## 1. Executive Summary",
        "",
        f"Samples tested: {len(cases)}",
        "This is not a human evaluation. Checklist heuristics are not perfect.",
        "Naturalness scoring is approximate. Meaning preservation cannot be fully verified with heuristics.",
        "Human review is still needed.",
        "",
    ]

    for case in cases:
        lines.append(f"## {case['id']}")
        lines.append("")
        lines.append("### Source")
        lines.append("")
        lines.append(f"> {case['source']}")
        lines.append("")
        lines.append("### Draft Translation")
        lines.append("")
        lines.append(f"> {case['draft']}")
        lines.append("")

        checklist = builder.build(
            source_text=case["source"],
            genre=case.get("genre", "general"),
        )
        evaluation = evaluator.evaluate(
            checklist, case["draft"], case["source"]
        )

        lines.append("### Generated Checklist")
        lines.append("")
        for check in checklist.get("checks", []):
            lines.append(
                f"- [{check['severity'].upper()}] {check['question']}"
            )
        lines.append("")

        lines.append("### Checklist Evaluation")
        lines.append("")
        lines.append(f"Overall score: {evaluation['overall_revision_score']}/5")
        lines.append(f"Critical failures: {evaluation['critical_failures']}")
        lines.append(f"Warnings: {evaluation['warnings']}")
        lines.append(f"Passed: {evaluation['passed_checks']}/{len(evaluation['checks'])}")
        lines.append("")

        failed = [c for c in evaluation["checks"] if not c["passed"]]
        if failed:
            lines.append("### Failed / Warning Items")
            lines.append("")
            for f in failed:
                lines.append(f"- **{f['id']}** [{f['severity']}]: {f['evidence']}")
            lines.append("")
        else:
            lines.append("### Failed / Warning Items")
            lines.append("")
            lines.append("_None._")
            lines.append("")

        recs = evaluation.get("revision_recommendations", [])
        if recs:
            lines.append("### Recommended Revisions")
            lines.append("")
            for rec in recs:
                lines.append(f"- {rec}")
            lines.append("")

        expected = case.get("expected_issues", [])
        lines.append(f"Expected issues: {', '.join(expected) if expected else 'none'}")
        lines.append("")

    lines.append("## Notes on Limitations")
    lines.append("")
    lines.append("- Heuristic evaluation cannot verify meaning preservation or register consistency.")
    lines.append("- Translationese detection uses a fixed pattern list; it may miss novel patterns.")
    lines.append("- Pronoun counting is approximate; context-dependent pronoun necessity is not modeled.")
    lines.append("- Human review remains essential before accepting any checklist-driven revision.")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run revision checklist diagnostics.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "revision_checklist_diagnostics_report.md",
    )
    args = parser.parse_args()

    output_path = render_report(SYNTHETIC_CASES, args.output)
    print(f"Revision checklist diagnostics report written to: {output_path}")


if __name__ == "__main__":
    main()