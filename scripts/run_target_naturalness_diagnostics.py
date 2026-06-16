"""Diagnostics for v0.8 target-only Turkish naturalness pass."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.target_naturalness import TargetOnlyNaturalnessPass, TargetNaturalnessEvaluator

SAMPLES = [
    {
        "id": "business_translationese",
        "text": "Bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu.",
        "genre": "business",
    },
    {
        "id": "literary_fragment",
        "text": "Kapıda durdu. Sessiz. Bekleyerek.",
        "genre": "literary",
    },
    {
        "id": "with_numbers",
        "text": "25 Aralık 2024 tarihinde 150 TL ödeme yapıldı.",
        "genre": "business",
        "protected": ["ödeme", "yapıldı"],
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "target_naturalness_diagnostics_report.md")
    args = parser.parse_args()

    t_pass = TargetOnlyNaturalnessPass()
    evaluator = TargetNaturalnessEvaluator()
    lines = [
        "# Target-Only Naturalness Diagnostics Report",
        "",
        "## 1. Executive Summary",
        "",
        f"Samples: {len(SAMPLES)}",
        "This is not a human evaluation. Deterministic rewrites are limited.",
        "Naturalness scoring is approximate. Target-only pass cannot verify source meaning.",
        "Protected terms and numbers must be preserved. Human review is still needed.",
        "",
    ]

    for s in SAMPLES:
        result = t_pass.apply(turkish_text=s["text"], genre=s.get("genre"), protected_terms=s.get("protected"))
        ev = evaluator.evaluate(result, s.get("protected"))

        lines.append(f"## {s['id']}")
        lines.append("")
        lines.append("### Input Turkish Text")
        lines.append("")
        lines.append(f"> {s['text']}")
        lines.append("")
        lines.append(f"**Translationese before:** {result['translationese_patterns_before']}")
        lines.append(f"**Translationese after:** {result['translationese_patterns_after']}")
        lines.append(f"**Pronouns before:** {result['pronoun_count_before']}")
        lines.append(f"**Pronouns after:** {result['pronoun_count_after']}")
        lines.append(f"**Naturalness before:** {result['naturalness_score_before']}")
        lines.append(f"**Naturalness after:** {result['naturalness_score_after']}")
        lines.append("")

        if result["changed"]:
            lines.append("### Changes Made")
            lines.append("")
            for c in result["changes"]:
                lines.append(f"- `{c['before']}` → `{c['after']}` ({c['reason']})")
            lines.append("")

        lines.append("### Revised Text")
        lines.append("")
        lines.append(f"> {result['revised_text']}")
        lines.append("")

        if result["risk_flags"]:
            lines.append("### Risk Flags")
            lines.append("")
            for f in result["risk_flags"]:
                lines.append(f"- {f}")
            lines.append("")

        lines.append(f"**Recommendation:** {result['recommendation']}")
        lines.append(f"**Safe to apply:** {ev['safe_to_apply']}")
        lines.append(f"**Verdict:** {ev['verdict']}")
        lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append("- Deterministic rewrites are high-confidence only; context may still require different wording.")
    lines.append("- Naturalness scoring uses fixed heuristics; it cannot detect all translationese.")
    lines.append("- This pass cannot verify source meaning because it only sees Turkish text.")
    lines.append("- Protected terms and numbers must be provided or auto-extracted; extraction is regex-based.")
    lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to: {args.output}")


if __name__ == "__main__":
    main()