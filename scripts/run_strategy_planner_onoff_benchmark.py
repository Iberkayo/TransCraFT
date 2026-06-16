"""Run a small Strategy Planner OFF/ON translation benchmark.

This benchmark intentionally stays narrow: it exercises the real draft
translator prompt with and without v0.6 strategy context, then writes a
human-readable report with lightweight heuristic checks.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.translator import translate_draft
from src.tie.language_profile import LanguageProfileLoader
from src.tie.strategy_planner import TranslationStrategyPlanner


VALID_PREFERENCES = {"OFF", "ON", "Tie"}

TRANSLATIONESE_PATTERNS = [
    "neden oldu",
    "merak etmesine neden oldu",
    "olan",
    "eden",
    "yapan",
    "tarafindan",
    "taraf\u0131ndan",
    "a\u015f\u0131r\u0131 uzun c\u00fcmle",
    "merak etmesine yol acti",
    "merak etmesine yol a\u00e7t\u0131",
    "bu da",
    "anlamina gelir",
    "anlam\u0131na gelir",
    " o ",
    " onun ",
]


def load_cases(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_benchmark_state(case: Dict[str, Any], strategy_enabled: bool) -> Dict[str, Any]:
    state: Dict[str, Any] = {
        "source_text": case["source_text"],
        "source_language": case.get("source_language", "en_US"),
        "target_language": case.get("target_language", "tr_TR"),
        "genre": case.get("genre", "general"),
        "glossary": [],
        "positive_glossary": {},
        "negative_glossary": {},
        "auto_glossary_candidates": {},
        "compact_memory_context": "",
        "logs": [],
        "trace_id": None,
        "chunk_index": 0,
    }
    if strategy_enabled:
        loader = LanguageProfileLoader()
        planner = TranslationStrategyPlanner(profile_loader=loader)
        state["translation_strategy"] = planner.plan(
            source_text=case["source_text"],
            source_language=case.get("source_language"),
            target_language=case.get("target_language"),
            genre=case.get("genre"),
            work_id=case.get("id"),
        )
        state["language_profile"] = loader.load_profile(case.get("target_language"), default="tr_TR")
    return state


def translate_case(
    case: Dict[str, Any],
    strategy_enabled: bool,
    translator: Callable[[Dict[str, Any]], Dict[str, Any]] = translate_draft,
) -> str:
    result = translator(build_benchmark_state(case, strategy_enabled))
    return str(result.get("raw_translation", "")).strip()


def detect_translationese_patterns(text: str) -> List[str]:
    normalized = f" {text.casefold()} "
    hits = []
    for pattern in TRANSLATIONESE_PATTERNS:
        if pattern.strip() in {"o", "onun", "bu"}:
            if re.search(rf"\b{re.escape(pattern.strip())}\b", normalized):
                hits.append(pattern.strip())
        elif pattern.casefold() in normalized:
            hits.append(pattern)
    return sorted(set(hits))


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def has_error(text: str) -> bool:
    return not text.strip() or text.startswith("ERROR:")


def score_case(off_text: str, on_text: str, case: Dict[str, Any] | None = None) -> Dict[str, Any]:
    risk_types = set((case or {}).get("risk_type", []))
    off_patterns = detect_translationese_patterns(off_text)
    on_patterns = detect_translationese_patterns(on_text)
    off_long_penalty = 1 if len(off_text.split()) > 32 and sentence_count(off_text) <= 1 else 0
    on_long_penalty = 1 if len(on_text.split()) > 32 and sentence_count(on_text) <= 1 else 0
    split_bonus = 1 if "sentence_splitting" in risk_types and sentence_count(on_text) > sentence_count(off_text) else 0

    off_naturalness = clamp_score(5 - min(3, len(off_patterns)) - off_long_penalty)
    on_naturalness = clamp_score(5 - min(3, len(on_patterns)) - on_long_penalty + split_bonus)
    off_literalness_score = clamp_score(5 - min(4, len(off_patterns) + off_long_penalty))
    on_literalness_score = clamp_score(5 - min(4, len(on_patterns) + on_long_penalty) + split_bonus)
    literalness_reduction = clamp_score(3 + on_literalness_score - off_literalness_score)
    off_meaning_preservation = 1 if has_error(off_text) else 4
    on_meaning_preservation = 1 if has_error(on_text) else 4

    if on_naturalness > off_naturalness or on_literalness_score > off_literalness_score:
        preferred = "ON"
    elif off_naturalness > on_naturalness or off_literalness_score > on_literalness_score:
        preferred = "OFF"
    else:
        preferred = "Tie"

    return {
        "off_patterns": off_patterns,
        "on_patterns": on_patterns,
        "off_naturalness": off_naturalness,
        "on_naturalness": on_naturalness,
        "off_literalness_score": off_literalness_score,
        "on_literalness_score": on_literalness_score,
        "literalness_reduction": literalness_reduction,
        "off_meaning_preservation": off_meaning_preservation,
        "on_meaning_preservation": on_meaning_preservation,
        "preferred": preferred,
        "on_reduced_literalness": len(on_patterns) < len(off_patterns) or on_long_penalty < off_long_penalty,
        "visible_difference": visible_difference(off_text, on_text),
        "on_harm": preferred == "OFF",
    }


def clamp_score(value: int | bool) -> int:
    return max(1, min(5, int(value)))


def visible_difference(off_text: str, on_text: str) -> str:
    if off_text.strip() == on_text.strip():
        return "No visible wording difference."
    off_sentences = sentence_count(off_text)
    on_sentences = sentence_count(on_text)
    if on_sentences > off_sentences:
        return "Strategy ON uses more sentence splitting."
    if len(on_text) < len(off_text) * 0.85:
        return "Strategy ON is more concise."
    return "Strategy ON changes wording or structure."


def run_benchmark(
    cases_path: Path,
    output_path: Path,
    translator: Callable[[Dict[str, Any]], Dict[str, Any]] = translate_draft,
) -> Dict[str, Any]:
    cases = load_cases(cases_path)
    records = []
    for case in cases:
        try:
            off_translation = translate_case(case, strategy_enabled=False, translator=translator)
        except Exception as exc:
            off_translation = f"ERROR: {exc}"
        try:
            on_translation = translate_case(case, strategy_enabled=True, translator=translator)
        except Exception as exc:
            on_translation = f"ERROR: {exc}"

        scores = score_case(off_translation, on_translation, case)
        records.append(
            {
                "case": case,
                "off_translation": off_translation,
                "on_translation": on_translation,
                **scores,
            }
        )

    summary = summarize(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(records, summary), encoding="utf-8")
    return {"records": records, "summary": summary, "output_path": output_path}


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "case_count": len(records),
        "on_wins": sum(1 for r in records if r["preferred"] == "ON"),
        "off_wins": sum(1 for r in records if r["preferred"] == "OFF"),
        "ties": sum(1 for r in records if r["preferred"] == "Tie"),
        "on_helped": [r["case"]["id"] for r in records if r["preferred"] == "ON"],
        "on_harmed": [r["case"]["id"] for r in records if r["preferred"] == "OFF"],
        "translationese_count_off": sum(len(r["off_patterns"]) for r in records),
        "translationese_count_on": sum(len(r["on_patterns"]) for r in records),
        "average_naturalness_off": average(r["off_naturalness"] for r in records),
        "average_naturalness_on": average(r["on_naturalness"] for r in records),
        "average_literalness_score_off": average(r["off_literalness_score"] for r in records),
        "average_literalness_score_on": average(r["on_literalness_score"] for r in records),
        "average_meaning_preservation_off": average(r["off_meaning_preservation"] for r in records),
        "average_meaning_preservation_on": average(r["on_meaning_preservation"] for r in records),
        "errors": [
            r["case"]["id"]
            for r in records
            if has_error(r["off_translation"]) or has_error(r["on_translation"])
        ],
    }


def average(values: Any) -> float:
    numbers = list(values)
    return sum(numbers) / len(numbers) if numbers else 0.0


def impact_label(summary: Dict[str, Any]) -> str:
    case_count = max(1, summary["case_count"])
    on_win_rate = summary["on_wins"] / case_count
    harm_rate = summary["off_wins"] / case_count
    if summary["ties"] > max(summary["on_wins"], summary["off_wins"]):
        return "Inconclusive"
    if on_win_rate >= 0.50 and harm_rate <= 0.10:
        return "Strong positive"
    if summary["on_wins"] > summary["off_wins"] and harm_rate <= 0.20:
        return "Mild positive"
    if summary["off_wins"] > summary["on_wins"] or harm_rate > 0.25:
        return "Negative"
    return "Inconclusive"


def render_report(records: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    lines = [
        "# Strategy Planner ON/OFF Benchmark",
        "",
        "## 1. Executive Summary",
        "",
        "This benchmark compares the real draft translator prompt with Strategy Planner OFF and ON. "
        "Scores are lightweight heuristics plus human-readable comparisons; they are not a full human evaluation platform.",
        "",
        f"- Cases tested: {summary['case_count']}",
        f"- Strategy ON wins: {summary['on_wins']}",
        f"- Strategy OFF wins: {summary['off_wins']}",
        f"- Ties: {summary['ties']}",
        f"- ON harm cases: {len(summary['on_harmed'])}",
        f"- Translationese patterns OFF: {summary['translationese_count_off']}",
        f"- Translationese patterns ON: {summary['translationese_count_on']}",
        f"- Average naturalness OFF: {summary['average_naturalness_off']:.2f}",
        f"- Average naturalness ON: {summary['average_naturalness_on']:.2f}",
        f"- Average literalness score OFF: {summary['average_literalness_score_off']:.2f}",
        f"- Average literalness score ON: {summary['average_literalness_score_on']:.2f}",
        f"- Average meaning preservation OFF: {summary['average_meaning_preservation_off']:.2f}",
        f"- Average meaning preservation ON: {summary['average_meaning_preservation_on']:.2f}",
        f"- Strategy Planner Impact: {impact_label(summary)}",
        f"- Translation errors: {len(summary['errors'])}",
        "",
        "This remains a small synthetic benchmark. Human review is still needed; ON wins do not automatically prove production quality. Ties mean the planner may still be insufficiently influential, and harm cases must be inspected manually.",
        "",
        "## 2. Overall Result",
        "",
        recommendation(summary),
        "",
        "| Case | Risk Type | Preferred | OFF Naturalness | ON Naturalness | ON Reduced Literalness? | Notes |",
        "| ---- | --------- | --------- | --------------: | -------------: | ----------------------- | ----- |",
    ]
    for record in records:
        case = record["case"]
        lines.append(
            "| {case_id} | {risk} | {preferred} | {off_nat} | {on_nat} | {reduced} | {notes} |".format(
                case_id=escape_cell(case["id"]),
                risk=escape_cell(", ".join(case.get("risk_type", []))),
                preferred=record["preferred"],
                off_nat=record["off_naturalness"],
                on_nat=record["on_naturalness"],
                reduced="yes" if record["on_reduced_literalness"] else "no",
                notes=escape_cell(record["visible_difference"]),
            )
        )

    lines.extend(["", "## 3. Case-by-Case Comparisons", ""])
    for record in records:
        case = record["case"]
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"Risk type: {', '.join(case.get('risk_type', []))}",
                "",
                f"Expected improvement: {case.get('expected_improvement', '')}",
                "",
                "Source:",
                "",
                quote(case["source_text"]),
                "",
                "Strategy OFF translation:",
                "",
                quote(record["off_translation"]),
                "",
                "Strategy ON translation:",
                "",
                quote(record["on_translation"]),
                "",
                f"Visible difference: {record['visible_difference']}",
                f"Did ON reduce translationese? {'yes' if record['on_reduced_literalness'] else 'no'}",
                f"Did ON improve Turkish naturalness? {'yes' if record['on_naturalness'] > record['off_naturalness'] else 'no'}",
                f"Did ON preserve meaning? heuristic score {record['on_meaning_preservation']}/5",
                f"Did ON over-edit or harm anything? {'yes' if record['on_harm'] else 'no'}",
                f"Preferred: {record['preferred']}",
                "",
            ]
        )

    lines.extend(
        [
            "## 4. Translationese Pattern Analysis",
            "",
            "| Case | OFF Patterns | ON Patterns |",
            "| ---- | ------------ | ----------- |",
        ]
    )
    for record in records:
        lines.append(
            "| {case_id} | {off} | {on} |".format(
                case_id=escape_cell(record["case"]["id"]),
                off=escape_cell(", ".join(record["off_patterns"]) or "none"),
                on=escape_cell(", ".join(record["on_patterns"]) or "none"),
            )
        )

    lines.extend(
        [
            "",
            "Summary:",
            "",
            f"- OFF pattern count: {summary['translationese_count_off']}",
            f"- ON pattern count: {summary['translationese_count_on']}",
            "",
            "## 5. Where Strategy ON Helped",
            "",
            bullet_list(summary["on_helped"]),
            "",
            "## 6. Where Strategy ON Did Not Help",
            "",
            bullet_list([r["case"]["id"] for r in records if r["preferred"] == "Tie"]),
            "",
            "## 7. Where Strategy ON Harmed Output",
            "",
            bullet_list(summary["on_harmed"]),
            "",
            "## 8. Recommendations",
            "",
            recommendation(summary),
            "",
        ]
    )
    return "\n".join(lines)


def recommendation(summary: Dict[str, Any]) -> str:
    if summary["errors"]:
        return "Revise before enabling by default; benchmark contains translation errors."
    label = impact_label(summary)
    if label in {"Strong positive", "Mild positive"}:
        return "Keep Strategy Planner enabled by default, with continued human review."
    if label == "Inconclusive":
        return "Keep Strategy Planner, but treat the default-enabled decision as inconclusive."
    return "Keep Strategy Planner available but disable by default until prompt strategy is revised."


def quote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines() or [""])


def bullet_list(items: List[str]) -> str:
    if not items:
        return "_None._"
    return "\n".join(f"- {item}" for item in items)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Strategy Planner OFF/ON translation benchmark.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=PROJECT_ROOT / "data" / "eval" / "strategy_planner_onoff_cases.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "strategy_planner_onoff_benchmark.md",
    )
    args = parser.parse_args()

    result = run_benchmark(args.cases, args.output)
    summary = result["summary"]
    print(f"Strategy Planner ON/OFF benchmark written to: {result['output_path']}")
    print(f"Cases: {summary['case_count']}")
    print(f"Strategy ON wins: {summary['on_wins']}")
    print(f"Strategy OFF wins: {summary['off_wins']}")
    print(f"Ties: {summary['ties']}")
    print(f"Impact: {impact_label(summary)}")
    print(f"Translationese OFF/ON: {summary['translationese_count_off']} / {summary['translationese_count_on']}")
    print(f"Errors: {len(summary['errors'])}")


if __name__ == "__main__":
    main()
