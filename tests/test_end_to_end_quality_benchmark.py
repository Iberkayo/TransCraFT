"""Tests for v0.9 end-to-end translation quality benchmark."""

import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_cases() -> list:
    path = PROJECT_ROOT / "data" / "eval" / "end_to_end_quality_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_end_to_end_cases_file_loads():
    cases = _load_cases()
    assert len(cases) >= 20
    assert all(isinstance(c, dict) for c in cases)


def test_cases_have_required_fields():
    cases = _load_cases()
    for case in cases:
        assert "id" in case, f"Missing id in {case}"
        assert "genre" in case, f"Missing genre in {case['id']}"
        assert "source_language" in case, f"Missing source_language in {case['id']}"
        assert "target_language" in case, f"Missing target_language in {case['id']}"
        assert "source_text" in case, f"Missing source_text in {case['id']}"
        assert "risk_type" in case, f"Missing risk_type in {case['id']}"
        assert "expected_behavior" in case, f"Missing expected_behavior in {case['id']}"


def test_benchmark_runner_generates_report():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    from scripts.run_end_to_end_quality_benchmark import (
        load_cases,
        run_benchmark,
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cases_path = PROJECT_ROOT / "data" / "eval" / "end_to_end_quality_cases.json"
        # Use only first 3 cases for fast test; skip real LLM calls
        cases = load_cases(cases_path)[:3]
        # Simulate with empty outputs — the test validates report generation, not LLM calls
        from scripts.run_end_to_end_quality_benchmark import render_benchmark_report, render_human_review_pack

        records = []
        for case in cases:
            records.append({
                "case": case,
                "baseline_translation": "Baz çeviri.",
                "strategy_translation": "Stratejili çeviri.",
                "full_translation": "Tam zincir çeviri.",
                "full_revised": "Tam zincir çeviri.",
                "target_naturalness_result": {"recommendation": "accept"},
                "baseline_t": 0, "strategy_t": 0, "full_t": 0,
                "baseline_p": 1, "strategy_p": 1, "full_p": 1,
                "baseline_nat": 4.5, "strategy_nat": 4.6, "full_nat": 4.8,
                "baseline_protected_fails": 0, "strategy_protected_fails": 0, "full_protected_fails": 0,
                "preferred": "full_chain",
            })

        summary = {
            "case_count": len(records),
            "baseline_wins": 0, "strategy_wins": 0, "full_chain_wins": 3,
            "ties": 0, "full_chain_harms": 0,
            "translationese_baseline": 0, "translationese_strategy": 0, "translationese_full": 0,
            "naturalness_baseline": 4.5, "naturalness_strategy": 4.6, "naturalness_full": 4.8,
            "protected_fails": 0, "impact_label": "mild_positive", "errors": 0,
        }

        output = tmp_path / "bench.md"
        review = tmp_path / "review.md"
        output.write_text(render_benchmark_report(records, summary, ["baseline", "strategy", "full"]), encoding="utf-8")
        review.write_text(render_human_review_pack(records, ["baseline", "strategy", "full"]), encoding="utf-8")

        assert output.exists()
        assert review.exists()
        text = output.read_text(encoding="utf-8")
        assert "End-to-End Translation Quality Benchmark" in text
        assert "Executive Summary" in text


def test_human_review_pack_generated():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    from scripts.run_end_to_end_quality_benchmark import render_human_review_pack

    records = [{
        "case": {
            "id": "test_001",
            "genre": "business",
            "risk_type": ["test"],
            "expected_behavior": "test",
            "source_text": "Test source.",
        },
        "baseline_translation": "T1.",
        "strategy_translation": "T2.",
        "full_revised": "T3.",
    }]
    pack = render_human_review_pack(records, ["baseline", "strategy", "full"])
    assert "baseline | strategy_only | full_chain | tie" in pack
    assert "T1" in pack
    assert "T2" in pack
    assert "T3" in pack


def test_modes_are_present():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.run_end_to_end_quality_benchmark import build_state

    case = {"source_text": "Test.", "genre": "business", "source_language": "en_US", "target_language": "tr_TR"}
    assert "translation_strategy" not in build_state(case, "baseline_translator_only")
    assert "translation_strategy" in build_state(case, "strategy_only")
    assert "revision_checklist" in build_state(case, "full_tie_quality_chain")


def test_metrics_include_translationese_counts():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.run_end_to_end_quality_benchmark import count_translationese

    assert count_translationese("Bu merak etmesine neden oldu.") >= 1
    assert count_translationese("Bu doğal bir metindir.") == 0


def test_metrics_include_protected_term_failures():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.run_end_to_end_quality_benchmark import check_protected

    assert check_protected("Metin burada.", ["Metin"]) == 0
    assert check_protected("Farklı metin.", ["Metin"]) == 1


def test_impact_label_is_valid():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.run_end_to_end_quality_benchmark import impact_label

    labels = {"strong_positive", "mild_positive", "inconclusive", "negative"}
    for s in [
        {"case_count": 20, "full_chain_wins": 12, "baseline_wins": 2, "ties": 6, "full_chain_harms": 1},
        {"case_count": 20, "full_chain_wins": 3, "baseline_wins": 2, "ties": 15, "full_chain_harms": 0},
        {"case_count": 20, "full_chain_wins": 1, "baseline_wins": 8, "ties": 11, "full_chain_harms": 3},
    ]:
        assert impact_label(s) in labels


def test_report_contains_no_overclaiming():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.run_end_to_end_quality_benchmark import render_benchmark_report

    report = render_benchmark_report([], {"case_count": 0, "baseline_wins": 0, "strategy_wins": 0, "full_chain_wins": 0, "ties": 0, "full_chain_harms": 0, "translationese_baseline": 0, "translationese_strategy": 0, "translationese_full": 0, "naturalness_baseline": 0, "naturalness_strategy": 0, "naturalness_full": 0, "protected_fails": 0, "impact_label": "inconclusive", "errors": 0}, ["baseline", "strategy", "full"])
    assert "not a human evaluation" in report.casefold()
    assert "human review" in report.casefold()


def test_no_hidden_cot_phrasing():
    path = Path(__file__).resolve().parent.parent / "scripts" / "run_end_to_end_quality_benchmark.py"
    source = path.read_text(encoding="utf-8").casefold()
    forbidden = ["chain-of-thought", "think step by step", "show your reasoning", "reveal reasoning"]
    for phrase in forbidden:
        assert phrase not in source, f"Forbidden phrase found: {phrase}"