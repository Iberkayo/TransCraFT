"""Run diagnostics for v0.9.2 foreign residue QA."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.foreign_residue import ForeignResidueDetector


CASES = [
    {
        "id": "critical_phrase",
        "text": "All races, all breeds. İnsanlar oradaydı.",
    },
    {
        "id": "merged_token",
        "text": "Hisshoulders dardır.",
    },
    {
        "id": "isolated_nouns",
        "text": "Tarlalarda Blacks çalışır; konuşmaları kaba olan Men geçer.",
    },
    {
        "id": "protected_places",
        "text": "Memphis'ten Saint Louis'e, oradan New Orleans'a gider.",
    },
]


def main() -> None:
    output = PROJECT_ROOT / "outputs" / "foreign_residue_diagnostics_report.md"
    detector = ForeignResidueDetector()

    lines = [
        "# Foreign Residue Diagnostics",
        "",
        "## Summary",
        "",
        "Synthetic diagnostics for target-side English residue detection in Turkish output.",
        "",
        "## Cases",
        "",
    ]

    for case in CASES:
        result = detector.detect(case["text"])
        lines.extend(
            [
                f"### {case['id']}",
                "",
                "**Input**",
                "",
                "```text",
                case["text"],
                "```",
                "",
                f"- Residue count: `{result['foreign_residue_count']}`",
                f"- Residues: `{result['residues']}`",
                f"- Recommendation: `{result['recommendation']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitations",
            "",
            "- Proper nouns must be passed as protected terms when the workflow knows them.",
            "- The detector is conservative and may mark uncertain English-looking nouns for review.",
            "- It is a QA guardrail, not a translation-quality scorer.",
            "",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Foreign residue diagnostics written to: {output}")


if __name__ == "__main__":
    main()
