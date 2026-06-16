"""Synthetic benchmark for v0.8 target-only Turkish naturalness pass.

Compares before/after on 12 Turkish examples. Heuristic only. Not human evaluation.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.target_naturalness import TargetOnlyNaturalnessPass, TargetNaturalnessEvaluator

CASES = [
    {
        "id": "translationese_001",
        "text": "Bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu.",
        "genre": "business",
        "expected_improvement": True,
    },
    {
        "id": "clean_business",
        "text": "Yönetim, kullanıma sunma işleminin hızlı tamamlanmasını istiyor ancak müşteri güveninden ödün verilmemeli.",
        "genre": "business",
        "expected_improvement": False,
    },
    {
        "id": "translationese_002",
        "text": "Bu da projenin ertelendiği anlamına gelir.",
        "genre": "business",
        "expected_improvement": True,
    },
    {
        "id": "literary_fragment",
        "text": "Kapıda durdu. Sessiz. Bekleyerek.",
        "genre": "literary",
        "expected_improvement": False,
    },
    {
        "id": "with_numbers_001",
        "text": "25 Aralık 2024 tarihinde 150 TL ödendi.",
        "genre": "business",
        "expected_improvement": False,
    },
    {
        "id": "pronoun_heavy",
        "text": "O, ona onu gönderdi. Onun dosyası bu.",
        "genre": "general",
        "expected_improvement": False,
    },
    {
        "id": "clean_academic",
        "text": "Bu çalışma, dağıtık mühendislik ekiplerinde uzaktan iş birliğinin karar kalitesini nasıl etkilediğini incelemektedir.",
        "genre": "academic",
        "expected_improvement": False,
    },
    {
        "id": "translationese_003",
        "text": "Buna ek olarak, raporun zamanında teslim edilmediği anlamına gelmektedir.",
        "genre": "business",
        "expected_improvement": True,
    },
    {
        "id": "clean_literary",
        "text": "Pencereye geri döndü. Cevap yok. Sadece yağmur.",
        "genre": "literary",
        "expected_improvement": False,
    },
    {
        "id": "empty_input",
        "text": "",
        "genre": "general",
        "expected_improvement": False,
    },
    {
        "id": "non_turkish",
        "text": "This is an English sentence.",
        "genre": "general",
        "expected_improvement": False,
    },
    {
        "id": "mixed_pronouns",
        "text": "O, bu dosyayı onun için hazırladı ve ona gönderdi.",
        "genre": "general",
        "expected_improvement": False,
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "target_naturalness_benchmark.md")
    args = parser.parse_args()

    t_pass = TargetOnlyNaturalnessPass()
    evaluator = TargetNaturalnessEvaluator()
    records = []

    for case in CASES:
        result = t_pass.apply(turkish_text=case["text"], genre=case.get("genre"))
        ev = evaluator.evaluate(result)
        records.append({
            "case": case,
            "result": result,
            "eval": ev,
        })

    improved = sum(1 for r in records if r["result"]["naturalness_score_after"] > r["result"]["naturalness_score_before"])
    worsened = sum(1 for r in records if r["result"]["naturalness_score_after"] < r["result"]["naturalness_score_before"])
    unchanged = len(records) - improved - worsened
    t_before = sum(r["result"]["translationese_patterns_before"] for r in records)
    t_after = sum(r["result"]["translationese_patterns_after"] for r in records)
    p_before = sum(r["result"]["pronoun_count_before"] for r in records)
    p_after = sum(r["result"]["pronoun_count_after"] for r in records)
    nat_before = sum(r["result"]["naturalness_score_before"] for r in records) / len(records)
    nat_after = sum(r["result"]["naturalness_score_after"] for r in records) / len(records)
    accepts = sum(1 for r in records if r["result"]["recommendation"] == "accept")
    reviews = sum(1 for r in records if r["result"]["recommendation"] == "review")
    rejects = sum(1 for r in records if r["result"]["recommendation"] == "reject")

    lines = [
        "# Target-Only Naturalness Benchmark",
        "",
        "## 1. Executive Summary",
        "",
        f"- Cases: {len(records)}",
        f"- Improved: {improved}",
        f"- Worsened: {worsened}",
        f"- Unchanged: {unchanged}",
        f"- Translationese before: {t_before}",
        f"- Translationese after: {t_after}",
        f"- Pronouns before: {p_before}",
        f"- Pronouns after: {p_after}",
        f"- Avg naturalness before: {nat_before:.2f}",
        f"- Avg naturalness after: {nat_after:.2f}",
        f"- Accepts: {accepts}",
        f"- Reviews: {reviews}",
        f"- Rejects: {rejects}",
        "",
        "This is a small synthetic benchmark. Deterministic rewrites are limited.",
        "Naturalness scoring is approximate. Target-only pass cannot verify source meaning.",
        "Protected terms and numbers must be preserved. Human review is still needed.",
        "",
        "## 2. Case Results",
        "",
        "| Case | T Before | T After | P Before | P After | Nat Before | Nat After | Rec |",
        "| ---- | -------: | ------: | -------: | ------: | ---------: | --------: | --- |",
    ]

    for r in records:
        lines.append(
            f"| {r['case']['id']} | {r['result']['translationese_patterns_before']} | {r['result']['translationese_patterns_after']} | "
            f"{r['result']['pronoun_count_before']} | {r['result']['pronoun_count_after']} | "
            f"{r['result']['naturalness_score_before']:.1f} | {r['result']['naturalness_score_after']:.1f} | "
            f"{r['result']['recommendation']} |"
        )

    lines.extend(["", "## 3. Where It Helped", ""])
    helped = [r for r in records if r["result"]["changed"] and r["eval"]["safe_to_apply"]]
    if helped:
        for r in helped:
            lines.append(f"- **{r['case']['id']}**: {r['result']['changes']}")
    else:
        lines.append("_No cases where deterministic rewrite was safe and helpful._")

    lines.extend(["", "## 4. Where It Refused or Reviewed", ""])
    refused = [r for r in records if r["result"]["recommendation"] in {"review", "reject"}]
    if refused:
        for r in refused:
            lines.append(f"- **{r['case']['id']}**: {r['result']['risk_flags']}")
    else:
        lines.append("_None._")

    lines.extend(["", "## 5. Limitations", ""])
    lines.append("- All cases are synthetic; no copyrighted text is used.")
    lines.append("- Deterministic rewrites are high-confidence only; context may require different wording.")
    lines.append("- This pass cannot verify source meaning because it only sees Turkish text.")
    lines.append("- Human review is still needed.")
    lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Benchmark written to: {args.output}")
    print(f"Improved: {improved}/{len(records)}, Naturalness: {nat_before:.2f} → {nat_after:.2f}")


if __name__ == "__main__":
    main()