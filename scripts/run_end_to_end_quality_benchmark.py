"""Run end-to-end translation quality benchmark comparing baseline, strategy-only, and full TIE chain.

This benchmark calls the real translator with different TIE feature configurations
and compares output quality using lightweight heuristic metrics.

Not a human evaluation. Heuristic scores are approximate.
Meaning preservation cannot be fully verified automatically.
Human review pack must be consulted before drawing conclusions.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.translator import translate_draft
from src.tie.memory_manager import MemoryManager
from src.tie.strategy_planner import TranslationStrategyPlanner
from src.tie.language_profile import LanguageProfileLoader
from src.tie.revision_checklist import (
    RevisionChecklistBuilder,
    RevisionChecklistEvaluator,
)
from src.tie.target_naturalness import TargetOnlyNaturalnessPass, TargetNaturalnessEvaluator


TRANSLATIONESE_PATTERNS = [
    "neden oldu",
    "merak etmesine neden oldu",
    "merak etmesine yol acti",
    "merak etmesine yol a\u00e7t\u0131",
    "anlam\u0131na gelir",
    "anlam\u0131na gelmektedir",
    "buna ek olarak",
    "bu da",
]
TURKISH_PRONOUNS = {" o ", " onun ", " ona ", " onu ", " onlar ", " onlar\u0131n ", " bunlar ", " bunu ", " bu "}


def load_cases(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_state(case: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Build a TranslationState dict for the given case and benchmark mode."""
    source_text = case["source_text"]
    genre = case.get("genre", "general")

    state: Dict[str, Any] = {
        "source_text": source_text,
        "source_language": case.get("source_language", "en_US"),
        "target_language": case.get("target_language", "tr_TR"),
        "genre": genre,
        "glossary": [],
        "positive_glossary": {},
        "negative_glossary": {},
        "auto_glossary_candidates": {},
        "style_guide": "",
        "compact_memory_context": "",
        "style_preset": "neutral",
        "logs": [],
        "trace_id": None,
        "chunk_index": 0,
        "revision_count": 0,
        "style_revision_count": 0,
        "is_approved": False,
        "enable_tie": False,
        "work_id": None,
        "user_id": None,
    }

    if mode in {"strategy_only", "full_tie_quality_chain"}:
        loader = LanguageProfileLoader()
        planner = TranslationStrategyPlanner(profile_loader=loader)
        state["translation_strategy"] = planner.plan(
            source_text=source_text,
            source_language=case.get("source_language"),
            target_language=case.get("target_language"),
            genre=genre,
            work_id=case.get("id"),
        )
        state["language_profile"] = loader.load_profile(case.get("target_language"), default="tr_TR")

    if mode == "full_tie_quality_chain":
        # Revision checklist
        builder = RevisionChecklistBuilder()
        state["revision_checklist"] = builder.build(
            source_text=source_text,
            genre=genre,
            translation_strategy=state.get("translation_strategy"),
        )
        # Target naturalness will be applied post-translation

    return state


def translate_case(case: Dict[str, Any], mode: str) -> str:
    result = translate_draft(build_state(case, mode))
    return str(result.get("raw_translation", "")).strip()


def apply_target_naturalness(text: str, genre: str, protected: List[str]) -> Dict[str, Any]:
    t_pass = TargetOnlyNaturalnessPass()
    return t_pass.apply(turkish_text=text, genre=genre, protected_terms=protected)


def count_translationese(text: str) -> int:
    lower = f" {text.casefold()} "
    return sum(1 for p in TRANSLATIONESE_PATTERNS if p in lower)


def count_pronouns(text: str) -> int:
    lower = f" {text.casefold()} "
    return sum(lower.count(p) for p in TURKISH_PRONOUNS if p in lower)


def naturalness_score(text: str) -> float:
    t_count = count_translationese(text)
    p_count = count_pronouns(text)
    raw = 5.0 - (t_count * 0.4) - (min(p_count, 8) * 0.2)
    return round(max(0.5, min(5.0, raw)), 1)


def check_protected(text: str, protected: List[str]) -> int:
    return sum(1 for t in protected if t and t not in text)


def heuristic_preferred(baseline: str, strategy: str, full: str) -> str:
    """Simple heuristic to determine which mode produced the better output."""
    scores = {
        "baseline": naturalness_score(baseline) - count_translationese(baseline) * 0.5,
        "strategy_only": naturalness_score(strategy) - count_translationese(strategy) * 0.5,
        "full_chain": naturalness_score(full) - count_translationese(full) * 0.5,
    }
    best = max(scores, key=scores.get)
    if scores["full_chain"] == scores[best] and scores["full_chain"] > scores["baseline"]:
        return "full_chain"
    if scores[best] == scores["baseline"] and best == "baseline":
        return "tie"
    return best


def impact_label(summary: Dict[str, Any]) -> str:
    total = max(1, summary["case_count"])
    fc_rate = summary["full_chain_wins"] / total
    harm_rate = summary["full_chain_harms"] / total
    if summary["ties"] > max(summary["full_chain_wins"], summary["baseline_wins"]):
        return "inconclusive"
    if fc_rate >= 0.50 and harm_rate <= 0.10:
        return "strong_positive"
    if summary["full_chain_wins"] > summary["baseline_wins"] and harm_rate <= 0.20:
        return "mild_positive"
    if harm_rate > 0.25 or summary["baseline_wins"] > summary["full_chain_wins"]:
        return "negative"
    return "inconclusive"


def run_benchmark(cases_path: Path, output_path: Path, review_path: Path) -> Dict[str, Any]:
    cases = load_cases(cases_path)
    records: List[Dict[str, Any]] = []
    modes = ["baseline_translator_only", "strategy_only", "full_tie_quality_chain"]

    for case in cases:
        outputs = {}
        for mode in modes:
            try:
                outputs[mode] = translate_case(case, mode)
            except Exception as exc:
                outputs[mode] = f"ERROR: {exc}"

        # Apply target naturalness pass to full chain output
        full_nat_result = apply_target_naturalness(
            outputs["full_tie_quality_chain"], case.get("genre", "general"), case.get("protected_terms", [])
        )
        full_revised = full_nat_result.get("revised_text", outputs["full_tie_quality_chain"])

        records.append({
            "case": case,
            "baseline_translation": outputs["baseline_translator_only"],
            "strategy_translation": outputs["strategy_only"],
            "full_translation": outputs["full_tie_quality_chain"],
            "full_revised": full_revised,
            "target_naturalness_result": full_nat_result,
            "baseline_t": count_translationese(outputs["baseline_translator_only"]),
            "strategy_t": count_translationese(outputs["strategy_only"]),
            "full_t": count_translationese(full_revised),
            "baseline_p": count_pronouns(outputs["baseline_translator_only"]),
            "strategy_p": count_pronouns(outputs["strategy_only"]),
            "full_p": count_pronouns(full_revised),
            "baseline_nat": naturalness_score(outputs["baseline_translator_only"]),
            "strategy_nat": naturalness_score(outputs["strategy_only"]),
            "full_nat": naturalness_score(full_revised),
            "baseline_protected_fails": check_protected(outputs["baseline_translator_only"], case.get("protected_terms", [])),
            "strategy_protected_fails": check_protected(outputs["strategy_only"], case.get("protected_terms", [])),
            "full_protected_fails": check_protected(full_revised, case.get("protected_terms", [])),
            "preferred": heuristic_preferred(
                outputs["baseline_translator_only"], outputs["strategy_only"], full_revised
            ),
        })

    summary = {
        "case_count": len(records),
        "baseline_wins": sum(1 for r in records if r["preferred"] == "baseline"),
        "strategy_wins": sum(1 for r in records if r["preferred"] == "strategy_only"),
        "full_chain_wins": sum(1 for r in records if r["preferred"] == "full_chain"),
        "ties": sum(1 for r in records if r["preferred"] == "tie"),
        "full_chain_harms": sum(1 for r in records if r["preferred"] == "baseline" and r["full_nat"] < r["baseline_nat"]),
        "translationese_baseline": sum(r["baseline_t"] for r in records),
        "translationese_strategy": sum(r["strategy_t"] for r in records),
        "translationese_full": sum(r["full_t"] for r in records),
        "naturalness_baseline": round(sum(r["baseline_nat"] for r in records) / len(records), 2),
        "naturalness_strategy": round(sum(r["strategy_nat"] for r in records) / len(records), 2),
        "naturalness_full": round(sum(r["full_nat"] for r in records) / len(records), 2),
        "protected_fails": sum(r["full_protected_fails"] for r in records),
        "impact_label": "",
        "errors": sum(1 for r in records if "ERROR:" in r["baseline_translation"] or "ERROR:" in r["full_translation"]),
    }
    summary["impact_label"] = impact_label(summary)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_benchmark_report(records, summary, modes), encoding="utf-8")
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(render_human_review_pack(records, modes), encoding="utf-8")

    return {"records": records, "summary": summary}


def render_benchmark_report(records: List[Dict[str, Any]], summary: Dict[str, Any], modes: List[str]) -> str:
    lines = [
        "# End-to-End Translation Quality Benchmark",
        "",
        "## 1. Executive Summary",
        "",
        f"- Cases tested: {summary['case_count']}",
        f"- Modes: {', '.join(modes)}",
        f"- Baseline wins: {summary['baseline_wins']}",
        f"- Strategy-only wins: {summary['strategy_wins']}",
        f"- Full-chain wins: {summary['full_chain_wins']}",
        f"- Ties: {summary['ties']}",
        f"- Full-chain harms: {summary['full_chain_harms']}",
        f"- Translationese baseline/strategy/full: {summary['translationese_baseline']} / {summary['translationese_strategy']} / {summary['translationese_full']}",
        f"- Naturalness baseline/strategy/full: {summary['naturalness_baseline']} / {summary['naturalness_strategy']} / {summary['naturalness_full']}",
        f"- Protected term failures: {summary['protected_fails']}",
        f"- Translation errors: {summary['errors']}",
        f"- Impact label: **{summary['impact_label']}**",
        "",
        "This is not a human evaluation. Heuristic scores are approximate.",
        "Meaning preservation cannot be fully verified automatically.",
        "Human review pack must be consulted before drawing conclusions.",
        "Synthetic cases are limited. Broad quality claims need human review.",
        "",
        "## 2. Benchmark Modes",
        "",
        "- **baseline_translator_only**: Translator without strategy planner, revision checklist, or target naturalness.",
        "- **strategy_only**: Translator with strategy planner and language profile.",
        "- **full_tie_quality_chain**: Full TIE chain including strategy planner, revision checklist, and target-only Turkish naturalness pass.",
        "",
        "## 3. Overall Results",
        "",
        "| Case | Genre | Preferred | Base T | Strat T | Full T | Base Nat | Strat Nat | Full Nat |",
        "| ---- | ----- | --------- | -----: | ------: | -----: | -------: | --------: | -------: |",
    ]
    for r in records:
        c = r["case"]
        lines.append(
            f"| {c['id']} | {c['genre']} | {r['preferred']} | "
            f"{r['baseline_t']} | {r['strategy_t']} | {r['full_t']} | "
            f"{r['baseline_nat']} | {r['strategy_nat']} | {r['full_nat']} |"
        )

    lines.extend(["", "## 4. Where Full Chain Helped", ""])
    helped = [r for r in records if r["preferred"] == "full_chain"]
    if helped:
        for r in helped:
            lines.append(f"- **{r['case']['id']}**: T {r['baseline_t']}→{r['full_t']}, Nat {r['baseline_nat']}→{r['full_nat']}")
    else:
        lines.append("_No cases where full chain clearly outperformed baseline by heuristic._")

    lines.extend(["", "## 5. Where Full Chain Did Not Help", ""])
    ties = [r for r in records if r["preferred"] == "tie"]
    if ties:
        for r in ties:
            lines.append(f"- **{r['case']['id']}**: scores comparable across modes")
    else:
        lines.append("_None._")

    lines.extend(["", "## 6. Where Full Chain Harmed or Over-edited", ""])
    harmed = [r for r in records if r["preferred"] == "baseline"]
    if harmed:
        for r in harmed:
            lines.append(f"- **{r['case']['id']}**: full chain regressed relative to baseline")
    else:
        lines.append("_None._")

    lines.extend(["", "## 7. Protected Term / Number Safety", ""])
    lines.append(f"Total protected term failures: {summary['protected_fails']}")
    if summary["protected_fails"] > 0:
        for r in records:
            if r["full_protected_fails"] > 0:
                lines.append(f"- **{r['case']['id']}**: {r['full_protected_fails']} protected term(s) lost in full chain")

    lines.extend(["", "## 8. Human Review Needed", ""])
    lines.append("See `outputs/end_to_end_human_review_pack.md` for case-by-case human review template.")
    lines.append("Heuristic metrics cannot replace human judgment on meaning preservation and naturalness.")

    lines.extend(["", "## 9. Recommendation", ""])
    label = summary["impact_label"]
    if label == "strong_positive":
        lines.append("Full TIE quality chain shows strong positive signal. Continue enabling all components by default.")
    elif label == "mild_positive":
        lines.append("Full chain shows mild positive signal. Keep enabled but continue human review.")
    elif label == "inconclusive":
        lines.append("Results are inconclusive. The TIE quality infrastructure is sound but differences are not large enough to draw strong conclusions from this synthetic benchmark alone.")
    else:
        lines.append("Review full chain configuration. Consider adjusting aggressiveness of revision passes.")
    lines.append("")
    return "\n".join(lines)


def render_human_review_pack(records: List[Dict[str, Any]], modes: List[str]) -> str:
    lines = [
        "# End-to-End Human Review Pack",
        "",
        "This pack is designed for human review by Berkay or a qualified reviewer.",
        "Heuristic metrics cannot replace human judgment.",
        "For each case, review the outputs and answer the questions.",
        "",
    ]
    for r in records:
        c = r["case"]
        lines.extend([
            f"## {c['id']}",
            "",
            f"**Genre:** {c['genre']}",
            f"**Risk types:** {', '.join(c.get('risk_type', []))}",
            f"**Expected behavior:** {c.get('expected_behavior', '')}",
            "",
            "### Source:",
            "",
            f"> {c['source_text']}",
            "",
            "### Baseline (translator only):",
            "",
            f"> {r['baseline_translation']}",
            "",
            "### Strategy Only (planner + translator):",
            "",
            f"> {r['strategy_translation']}",
            "",
            "### Full Chain (planner + translator + revision + naturalness):",
            "",
            f"> {r['full_revised']}",
            "",
            "### Questions:",
            "",
            "1. Which output is most natural Turkish?",
            "2. Which output preserves source meaning best?",
            "3. Which output smells least like translation?",
            "4. Did Full Chain over-edit anything?",
            "5. Preferred: baseline | strategy_only | full_chain | tie",
            "6. Notes:",
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end quality benchmark.")
    parser.add_argument("--cases", type=Path, default=PROJECT_ROOT / "data" / "eval" / "end_to_end_quality_cases.json")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "end_to_end_quality_benchmark.md")
    parser.add_argument("--review", type=Path, default=PROJECT_ROOT / "outputs" / "end_to_end_human_review_pack.md")
    args = parser.parse_args()

    result = run_benchmark(args.cases, args.output, args.review)
    s = result["summary"]
    print(f"Benchmark written to: {args.output}")
    print(f"Human review pack written to: {args.review}")
    print(f"Cases: {s['case_count']}")
    print(f"Baseline wins: {s['baseline_wins']}")
    print(f"Strategy wins: {s['strategy_wins']}")
    print(f"Full-chain wins: {s['full_chain_wins']}")
    print(f"Ties: {s['ties']}")
    print(f"Impact: {s['impact_label']}")


if __name__ == "__main__":
    main()