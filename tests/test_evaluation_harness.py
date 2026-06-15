from src.evaluation.harness import (
    render_markdown_report,
    scan_forbidden_phrases,
    summarize_cases,
)


def test_summarize_cases_counts_pairwise_winners():
    summary = summarize_cases([
        {"expected_winner": "tie_on"},
        {"expected_winner": "tie_off"},
        {"expected_winner": "tie"},
    ])

    assert summary["total_cases"] == 3
    assert summary["tie_on_wins"] == 1
    assert summary["tie_off_wins"] == 1
    assert summary["ties"] == 1
    assert summary["tie_on_win_rate"] == 1 / 3


def test_scan_forbidden_phrases_reports_runtime_leakage(tmp_path):
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("prompt = 'generic rule only'", encoding="utf-8")
    leaky_file = tmp_path / "leaky.py"
    leaky_file.write_text("prompt = 'See the child.'", encoding="utf-8")

    findings = scan_forbidden_phrases([tmp_path], ["See the child."])

    assert findings == [{"path": str(leaky_file), "phrase": "See the child."}]


def test_render_markdown_report_includes_leak_status():
    report = render_markdown_report(
        {
            "total_cases": 1,
            "tie_on_wins": 1,
            "tie_off_wins": 0,
            "ties": 0,
            "tie_on_win_rate": 1.0,
        },
        [],
    )

    assert "TIE ON win rate: 100.00%" in report
    assert "leakage/provenance guardrail" in report
    assert "not yet a full blinded pairwise translation-quality benchmark" in report
    assert "No forbidden benchmark phrases" in report
