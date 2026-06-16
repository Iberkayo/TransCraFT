"""Run a small synthetic revision checklist benchmark comparing base vs checklist-guided output.

Heuristic comparison only. Not a human evaluation.
"""

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.revision_checklist import (
    RevisionChecklistBuilder,
    RevisionChecklistEvaluator,
    TRANSLATIONESE_PATTERNS,
    TURKISH_UNNECESSARY_PRONOUNS,
    TURKISH_HEAVY_RELATIVE_MARKERS,
    TURKISH_PASSIVE_MARKERS,
)


BENCHMARK_CASES = [
    {
        "id": "business_translationese_001",
        "genre": "business",
        "source": "The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.",
        "base": "Eski yazılımın 3. çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor, bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu.",
        "revised": "Eski yazılımın üçüncü çeyrek sonunda aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük işleyişin nasıl etkileneceğine dair soru işaretleri yarattı.",
    },
    {
        "id": "noun_stack_001",
        "genre": "business",
        "source": "The customer data privacy compliance monitoring system needs to be updated before the audit.",
        "base": "Müşteri veri gizliliği uyumluluk izleme sisteminin denetimden önce güncellenmesi gerekiyor.",
        "revised": "Müşteri verilerinin gizliliğini denetleyen uyum sisteminin denetimden önce güncellenmesi gerekiyor.",
    },
    {
        "id": "passive_voice_001",
        "genre": "business",
        "source": "The report was reviewed by the committee and was approved after several minor revisions.",
        "base": "Rapor, komite tarafından incelenmiş ve birkaç küçük düzeltmeden sonra onaylanmıştır.",
        "revised": "Komite raporu inceledi ve birkaç küçük düzeltmenin ardından onayladı.",
    },
    {
        "id": "pronoun_heavy_001",
        "genre": "general",
        "source": "She told him that she would send him the file when she finished reviewing it.",
        "base": "O, ona dosyayı incelemeyi bitirdiğinde onu ona göndereceğini söyledi.",
        "revised": "Dosyayı inceledikten sonra göndereceğini söyledi.",
    },
    {
        "id": "idiom_metaphor_001",
        "genre": "general",
        "source": "The announcement threw cold water on the team's optimism.",
        "base": "Duyuru takımın iyimserliğine soğuk su attı.",
        "revised": "Duyuru, ekibin iyimserliğini kursağında bıraktı.",
    },
    {
        "id": "literary_fragment_001",
        "genre": "literary",
        "source": "Went back to the window. No answer. Only the rain.",
        "base": "Pencereye geri döndü. Cevap yok. Sadece yağmur.",
        "revised": "Pencereye geri döndü. Cevap yok. Sadece yağmur.",
    },
    {
        "id": "phrasal_verb_001",
        "genre": "business",
        "source": "The support team will follow up with each regional office after the migration is complete.",
        "base": "Destek takımı geçiş tamamlandıktan sonra her bölgesel ofisi takip edecek.",
        "revised": "Destek ekibi, geçiş tamamlandıktan sonra her bölge ofisiyle iletişime geçecek.",
    },
    {
        "id": "business_translationese_002",
        "genre": "business",
        "source": "Management wants the rollout to be completed quickly, but not at the expense of customer trust.",
        "base": "Yönetim dağıtımın hızlı tamamlanmasını istiyor, ama müşteri güveni pahasına değil.",
        "revised": "Yönetim, kullanıma sunma işleminin hızlı tamamlanmasını istiyor ancak bu süreç müşteri güveninden ödün verilmesine yol açmamalı.",
    },
    {
        "id": "preposition_heavy_001",
        "genre": "business",
        "source": "The update from the finance team about the delay in the payment process arrived after the meeting.",
        "base": "Finans takımından ödeme sürecindeki gecikme hakkındaki güncelleme toplantıdan sonra geldi.",
        "revised": "Finans ekibinden, ödeme sürecindeki gecikmeyle ilgili güncelleme toplantıdan sonra geldi.",
    },
    {
        "id": "clear_split_001",
        "genre": "business",
        "source": "The new policy applies to all vendors who process customer records, which means the procurement team must update every active contract this month.",
        "base": "Yeni politika müşteri kayıtlarını işleyen tüm satıcılar için geçerlidir, bu da satın alma ekibinin bu ay tüm aktif sözleşmeleri güncellemesi gerektiği anlamına gelir.",
        "revised": "Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.",
    },
]


def count_translationese(text: str) -> int:
    lower = f" {text.casefold()} "
    return sum(1 for pattern, _ in TRANSLATIONESE_PATTERNS if pattern in lower)


def count_pronouns(text: str) -> int:
    lower = f" {text.casefold()} "
    return sum(lower.count(p) for p in TURKISH_UNNECESSARY_PRONOUNS if p in lower)


def count_passive_markers(text: str) -> int:
    lower = text.casefold()
    return sum(1 for m in TURKISH_PASSIVE_MARKERS if m in lower)


def count_relative_chains(text: str) -> int:
    return len([p for p in TURKISH_HEAVY_RELATIVE_MARKERS if re.search(p, text, re.IGNORECASE)])


def heuristic_naturalness(text: str) -> float:
    t_count = count_translationese(text)
    p_count = count_pronouns(text)
    r_count = count_relative_chains(text)
    pas_count = count_passive_markers(text)
    raw = 5.0 - (t_count * 0.4) - (min(p_count, 5) * 0.3) - (r_count * 0.3) - (min(pas_count - 1, 3) * 0.2)
    return max(0.5, min(5.0, raw))


def run_benchmark(output_path: Path) -> Dict[str, Any]:
    builder = RevisionChecklistBuilder()
    evaluator = RevisionChecklistEvaluator()
    records = []

    for case in BENCHMARK_CASES:
        checklist = builder.build(
            source_text=case["source"],
            genre=case.get("genre", "general"),
        )
        base_eval = evaluator.evaluate(checklist, case["base"], case["source"])
        rev_eval = evaluator.evaluate(checklist, case["revised"], case["source"])

        base_t = count_translationese(case["base"])
        rev_t = count_translationese(case["revised"])
        base_p = count_pronouns(case["base"])
        rev_p = count_pronouns(case["revised"])
        base_r = count_relative_chains(case["base"])
        rev_r = count_relative_chains(case["revised"])
        base_pas = count_passive_markers(case["base"])
        rev_pas = count_passive_markers(case["revised"])
        base_nat = heuristic_naturalness(case["base"])
        rev_nat = heuristic_naturalness(case["revised"])

        records.append({
            "case": case,
            "base_score": base_eval["overall_revision_score"],
            "revised_score": rev_eval["overall_revision_score"],
            "base_translationese": base_t,
            "revised_translationese": rev_t,
            "base_pronouns": base_p,
            "revised_pronouns": rev_p,
            "base_relative_chain": base_r,
            "revised_relative_chain": rev_r,
            "base_passive": base_pas,
            "revised_passive": rev_pas,
            "base_naturalness": base_nat,
            "revised_naturalness": rev_nat,
            "base_critical_fails": base_eval["critical_failures"],
            "revised_critical_fails": rev_eval["critical_failures"],
            "revised_improved": rev_eval["overall_revision_score"] > base_eval["overall_revision_score"],
        })

    summary = {
        "case_count": len(records),
        "improved_count": sum(1 for r in records if r["revised_improved"]),
        "worsened_count": sum(1 for r in records if r["revised_score"] < r["base_score"]),
        "unchanged_count": sum(1 for r in records if r["revised_score"] == r["base_score"]),
        "base_translationese_total": sum(r["base_translationese"] for r in records),
        "revised_translationese_total": sum(r["revised_translationese"] for r in records),
        "base_pronouns_total": sum(r["base_pronouns"] for r in records),
        "revised_pronouns_total": sum(r["revised_pronouns"] for r in records),
        "base_avg_naturalness": sum(r["base_naturalness"] for r in records) / len(records),
        "revised_avg_naturalness": sum(r["revised_naturalness"] for r in records) / len(records),
        "base_avg_score": sum(r["base_score"] for r in records) / len(records),
        "revised_avg_score": sum(r["revised_score"] for r in records) / len(records),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(records, summary), encoding="utf-8")
    return {"records": records, "summary": summary, "output_path": output_path}


def render_report(records: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    lines = [
        "# Revision Checklist Benchmark",
        "",
        "## 1. Executive Summary",
        "",
        f"- Cases tested: {summary['case_count']}",
        f"- Improved after revision: {summary['improved_count']}",
        f"- Worsened after revision: {summary['worsened_count']}",
        f"- Unchanged: {summary['unchanged_count']}",
        f"- Base translationese total: {summary['base_translationese_total']}",
        f"- Revised translationese total: {summary['revised_translationese_total']}",
        f"- Base pronoun count: {summary['base_pronouns_total']}",
        f"- Revised pronoun count: {summary['revised_pronouns_total']}",
        f"- Base average naturalness: {summary['base_avg_naturalness']:.2f}",
        f"- Revised average naturalness: {summary['revised_avg_naturalness']:.2f}",
        f"- Base average checklist score: {summary['base_avg_score']:.2f}",
        f"- Revised average checklist score: {summary['revised_avg_score']:.2f}",
        "",
        "This is a small synthetic benchmark. Checklist heuristics are not perfect.",
        "Naturalness scoring is approximate. Human review is still needed.",
        "",
        "## 2. Case-by-Case Results",
        "",
        "| Case | Base T | Rev T | Base P | Rev P | Base Nat | Rev Nat | Base Score | Rev Score | Improved? |",
        "| ---- | -----: | ----: | -----: | ----: | -------: | ------: | ---------: | --------: | --------- |",
    ]

    for r in records:
        case = r["case"]
        lines.append(
            "| {id} | {bt} | {rt} | {bp} | {rp} | {bn:.1f} | {rn:.1f} | {bs:.1f} | {rs:.1f} | {imp} |".format(
                id=case["id"],
                bt=r["base_translationese"],
                rt=r["revised_translationese"],
                bp=r["base_pronouns"],
                rp=r["revised_pronouns"],
                bn=r["base_naturalness"],
                rn=r["revised_naturalness"],
                bs=r["base_score"],
                rs=r["revised_score"],
                imp="yes" if r["revised_improved"] else "no",
            )
        )

    lines.extend([
        "",
        "## 3. Case Details",
        "",
    ])
    for r in records:
        case = r["case"]
        lines.extend([
            f"### {case['id']}",
            "",
            f"Source: {case['source']}",
            "",
            f"Base: {case['base']}",
            "",
            f"Revised: {case['revised']}",
            "",
            f"Translationese: {r['base_translationese']} -> {r['revised_translationese']}",
            f"Pronouns: {r['base_pronouns']} -> {r['revised_pronouns']}",
            f"Naturalness: {r['base_naturalness']:.1f} -> {r['revised_naturalness']:.1f}",
            f"Checklist score: {r['base_score']:.1f} -> {r['revised_score']:.1f}",
            f"Improved: {'yes' if r['revised_improved'] else 'no'}",
            "",
        ])

    lines.extend([
        "## 4. Notes on Limitations",
        "",
        "- All cases are synthetic; no copyrighted text is used.",
        "- Heuristic evaluation cannot verify meaning preservation or register consistency.",
        "- Translationese detection uses a fixed pattern list; it may miss novel patterns.",
        "- Pronoun counting is approximate; context-dependent pronoun necessity is not modeled.",
        "- Human review remains essential before accepting any checklist-driven revision.",
    ])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run revision checklist benchmark.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "revision_checklist_benchmark.md",
    )
    args = parser.parse_args()

    result = run_benchmark(args.output)
    summary = result["summary"]
    print(f"Revision checklist benchmark written to: {result['output_path']}")
    print(f"Cases: {summary['case_count']}")
    print(f"Improved: {summary['improved_count']}")
    print(f"Worsened: {summary['worsened_count']}")
    print(f"Base naturalness: {summary['base_avg_naturalness']:.2f}")
    print(f"Revised naturalness: {summary['revised_avg_naturalness']:.2f}")


if __name__ == "__main__":
    main()