"""Run diagnostics for v0.9.2 source extraction cleanup."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.source_cleanup import SourceExtractionCleaner, SourceExtractionQualityChecker


CASES = [
    {
        "id": "merged_pdf_tokens",
        "text": "He stokesthe scullery fire. Outside lie dark fields with darker woodsbeyond.",
    },
    {
        "id": "punctuation_spacing",
        "text": "The boy watches him.He waits,he listens.",
    },
    {
        "id": "uncertain_merged_token",
        "text": "This unknownmergedtoken should be flagged rather than guessed.",
    },
    {
        "id": "hyphenation",
        "text": "The rider crossed the moun-\ntain road and kept going.",
    },
    {
        "id": "split_initial_letter",
        "text": "S ee the child.",
        "expected": "See the child.",
    },
    {
        "id": "split_initial_now",
        "text": "N ow come days of begging.",
        "expected": "Now come days of begging.",
    },
    {
        "id": "invisible_word_split",
        "text": "Neigh\u200bbor, you caint get shed of him.",
        "expected": "Neighbor, you caint get shed of him.",
    },
    {
        "id": "word_internal_split",
        "text": "from his cloth\u200bing",
        "expected": "from his clothing",
    },
]


def main() -> None:
    output = PROJECT_ROOT / "outputs" / "source_cleanup_diagnostics_report.md"
    cleaner = SourceExtractionCleaner()
    checker = SourceExtractionQualityChecker()

    lines = [
        "# Source Cleanup Diagnostics",
        "",
        "## Summary",
        "",
        "Synthetic diagnostics for PDF extraction cleanup. The cleaner performs conservative repairs and flags uncertain merged tokens for review.",
        "",
        "## Cases",
        "",
    ]

    for case in CASES:
        cleaned = cleaner.clean(case["text"])
        quality = checker.check(cleaned["cleaned_text"])
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
                f"- Expected: `{case.get('expected', 'n/a')}`",
                "",
                "**Cleaned**",
                "",
                "```text",
                cleaned["cleaned_text"],
                "```",
                "",
                f"- Repairs: `{cleaned['repairs']}`",
                f"- Cleanup recommendation: `{cleaned['recommendation']}`",
                f"- Quality score: `{quality['quality_score']}`",
                f"- Quality flags: `{quality['flags']}`",
                f"- Quality recommendation: `{quality['recommendation']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitations",
            "",
            "- The repair map is intentionally small.",
            "- Split initial-letter repair is limited to explicit high-confidence forms such as `S ee` and `N ow`.",
            "- Invisible separators inside alphabetic tokens are joined, but semantic word-boundary questions still require review.",
            "- Uncertain merged words are flagged instead of guessed.",
            "- Diagnostics use synthetic examples; chapter extraction still requires boundary review.",
            "",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Source cleanup diagnostics written to: {output}")


if __name__ == "__main__":
    main()
