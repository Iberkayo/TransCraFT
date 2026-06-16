"""Generate diagnostics for the TIE v0.6 human translator strategy planner."""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.language_profile import LanguageProfileLoader
from src.tie.strategy_planner import TranslationStrategyPlanner, build_strategy_prompt_context


DEFAULT_SAMPLES = [
    {
        "name": "Alice sample",
        "source": "Alice was beginning to get very tired of sitting by her sister on the bank.",
        "genre": "literary",
        "work_id": "alice_in_wonderland",
    },
    {
        "name": "Frontier literary sample",
        "source": "The judge watched the fire while the boy stood silent in the doorway.",
        "genre": "literary",
        "work_id": "blood_meridian",
    },
    {
        "name": "Attention sample",
        "source": "The model relies on attention mechanisms to draw global dependencies between input and output.",
        "genre": "tech",
        "work_id": "attention_is_all_you_need",
    },
]

SMOKE_TEST_SOURCE = (
    "The legacy software is expected to be phased out by the end of Q3, "
    "a decision which has left many departments wondering how their daily operations will be affected."
)


def run_diagnostics(samples: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    loader = LanguageProfileLoader()
    planner = TranslationStrategyPlanner(profile_loader=loader)
    records = []

    for sample in samples or DEFAULT_SAMPLES:
        strategy = planner.plan(
            source_text=sample["source"],
            source_language="English",
            target_language="Turkish",
            genre=sample["genre"],
            work_id=sample["work_id"],
        )
        profile_context = planner.language_profile_context("English", "Turkish")
        records.append(
            {
                "sample": sample,
                "strategy": strategy,
                "source_language_profile": profile_context["source_language_profile"],
                "target_language_profile": profile_context["target_language_profile"],
            }
        )

    smoke_strategy = planner.plan(
        source_text=SMOKE_TEST_SOURCE,
        source_language="English",
        target_language="Turkish",
        genre="business",
    )
    smoke_profile = loader.load_profile("Turkish")
    smoke = {
        "source": SMOKE_TEST_SOURCE,
        "strategy_on_context": build_strategy_prompt_context(smoke_strategy, smoke_profile),
        "strategy_off_context": "",
        "observed_difference": (
            "Strategy ON adds meaning units, target profile rules, reconstruction notes, "
            "and structural risks. This is prompt-level evidence only; no real translation output was generated."
        ),
        "reduced_literalness_claim": "Not proven by this diagnostics run.",
    }

    return {"records": records, "summary": summarize(records), "smoke": smoke}


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "sample_count": len(records),
        "fallback_count": sum(1 for r in records if r["strategy"].get("fallback_used")),
        "meaning_unit_count": sum(len(r["strategy"].get("meaning_units", [])) for r in records),
        "structural_risk_count": sum(len(r["strategy"].get("structural_risks", [])) for r in records),
    }


def generate_report(result: Dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = result["summary"]
    lines = [
        "# Strategy Planner Diagnostics Report",
        "",
        "## 1. Executive Summary",
        "",
        f"- Samples evaluated: {summary['sample_count']}",
        f"- Fallback strategies used: {summary['fallback_count']}",
        f"- Meaning units generated: {summary['meaning_unit_count']}",
        f"- Structural risks detected: {summary['structural_risk_count']}",
        "",
        "This report validates planning, language-profile loading, and prompt guidance only. "
        "It does not run a full translation-quality benchmark.",
        "",
        "Fallback strategy was used for all current samples. Quality improvement is not proven here; "
        "the next evidence step is a small Strategy ON/OFF translation output comparison.",
        "",
        "## 2. Sample Source Text",
        "",
    ]

    for record in result["records"]:
        sample = record["sample"]
        strategy = record["strategy"]
        lines.extend(
            [
                f"### {sample['name']}",
                "",
                f"Source: {sample['source']}",
                "",
                "## 3. Generated Translation Strategy",
                "",
                f"- Text type: {strategy.get('text_type')}",
                f"- Tone: {strategy.get('tone')}",
                f"- Register: {strategy.get('register')}",
                f"- Literalness level: {strategy.get('literalness_level')}",
                f"- Sentence reconstruction: {strategy.get('sentence_reconstruction_strategy')}",
                f"- Localization: {strategy.get('localization_strategy')}",
                "",
                "## 4. Meaning Units",
                "",
                bullet_list(strategy.get("meaning_units", [])),
                "",
                "## 5. Target-Language Reconstruction Notes",
                "",
                bullet_list(strategy.get("turkish_reconstruction_notes", [])),
                "",
                "## 6. Structural Risks Detected",
                "",
                bullet_list(strategy.get("structural_risks", [])),
                "",
                "## 7. Translator Instructions",
                "",
                bullet_list(strategy.get("translator_instructions", [])),
                "",
                "## 8. Critic Checklist",
                "",
                bullet_list(strategy.get("critic_checklist", [])),
                "",
                "## 9. Before/After Translation Comparison",
                "",
                "Not executed in this diagnostics run. The sprint intentionally checks planner output without adding a new translation benchmark path.",
                "",
            ]
        )

    smoke = result["smoke"]
    lines.extend(
        [
            "## 10. Strategy ON/OFF Prompt Smoke Test",
            "",
            f"Source: {smoke['source']}",
            "",
            "Strategy Planner OFF context:",
            "",
            "_None._",
            "",
            "Strategy Planner ON context excerpt:",
            "",
            fenced_excerpt(smoke["strategy_on_context"]),
            "",
            f"Observed difference: {smoke['observed_difference']}",
            "",
            f"Reduced literalness: {smoke['reduced_literalness_claim']}",
            "",
            "## 11. Risks / Limitations",
            "",
            "- The planner is deterministic and conservative; it does not prove translation quality by itself.",
            "- Strategy quality still depends on translator and critic adherence.",
            "- Current diagnostics cover English to Turkish profiles only.",
            "- Prompt-level ON/OFF evidence is not a substitute for human review of actual translation outputs.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def bullet_list(items: List[Any]) -> str:
    if not items:
        return "_None._"
    lines = []
    for item in items:
        if isinstance(item, dict):
            lines.append(
                "- {risk_type}: {evidence} | strategy: {recommended_strategy}".format(
                    risk_type=item.get("risk_type", "risk"),
                    evidence=item.get("evidence", ""),
                    recommended_strategy=item.get("recommended_strategy", ""),
                )
            )
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def fenced_excerpt(text: str, max_lines: int = 28) -> str:
    lines = text.splitlines()[:max_lines]
    return "```text\n" + "\n".join(lines) + "\n```"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TIE v0.6 strategy planner diagnostics.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "strategy_planner_diagnostics_report.md",
    )
    args = parser.parse_args()

    result = run_diagnostics()
    output_path = generate_report(result, args.output)
    summary = result["summary"]

    print(f"Strategy planner diagnostics report written to: {output_path}")
    print(f"Samples: {summary['sample_count']}")
    print(f"Fallback strategies used: {summary['fallback_count']}")
    print(f"Meaning units: {summary['meaning_unit_count']}")
    print(f"Structural risks: {summary['structural_risk_count']}")


if __name__ == "__main__":
    main()
