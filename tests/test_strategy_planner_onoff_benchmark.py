import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.run_strategy_planner_onoff_benchmark import (
    VALID_PREFERENCES,
    build_benchmark_state,
    detect_translationese_patterns,
    load_cases,
    run_benchmark,
    translate_case,
)


CASES_PATH = Path("data/eval/strategy_planner_onoff_cases.json")


def test_onoff_cases_file_loads():
    cases = load_cases(CASES_PATH)

    assert 8 <= len(cases) <= 12
    assert all(case["source_text"] for case in cases)
    assert {"genre", "source_language", "target_language", "risk_type"}.issubset(cases[0].keys())


def test_benchmark_runner_generates_report(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(json.dumps(load_cases(CASES_PATH)[:2]), encoding="utf-8")
    output_path = tmp_path / "report.md"

    result = run_benchmark(cases_path, output_path, translator=fake_translator)

    assert output_path.exists()
    assert result["summary"]["case_count"] == 2
    assert "Strategy Planner ON/OFF Benchmark" in output_path.read_text(encoding="utf-8")


def test_strategy_toggle_off_removes_strategy_context():
    case = load_cases(CASES_PATH)[0]
    state = build_benchmark_state(case, strategy_enabled=False)

    assert "translation_strategy" not in state
    assert "language_profile" not in state

    prompt = capture_translator_prompt(case, strategy_enabled=False)
    assert "### Translation Strategy Plan" not in prompt


def test_strategy_toggle_on_includes_strategy_context():
    case = load_cases(CASES_PATH)[0]
    state = build_benchmark_state(case, strategy_enabled=True)

    assert state["translation_strategy"]
    assert state["language_profile"]

    prompt = capture_translator_prompt(case, strategy_enabled=True)
    assert "### Translation Strategy Plan" in prompt
    assert "Target language profile rules" in prompt
    assert "Target-language reconstruction notes" in prompt


def test_translationese_patterns_detected():
    text = "Bu karar departmanlarin merak etmesine neden oldu ve rapor komite tarafindan incelendi."
    patterns = detect_translationese_patterns(text)

    assert "neden oldu" in patterns
    assert "merak etmesine neden oldu" in patterns
    assert "tarafindan" in patterns


def test_report_contains_off_and_on_outputs(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(json.dumps(load_cases(CASES_PATH)[:1]), encoding="utf-8")
    output_path = tmp_path / "report.md"

    run_benchmark(cases_path, output_path, translator=fake_translator)
    report = output_path.read_text(encoding="utf-8")

    assert "Strategy OFF translation" in report
    assert "Strategy ON translation" in report
    assert "OFF literal translation neden oldu" in report
    assert "ON natural translation" in report


def test_preferred_field_is_valid(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(json.dumps(load_cases(CASES_PATH)[:3]), encoding="utf-8")

    result = run_benchmark(cases_path, tmp_path / "report.md", translator=fake_translator)

    assert all(record["preferred"] in VALID_PREFERENCES for record in result["records"])


def test_no_copyrighted_required_inputs():
    forbidden = {"alice", "white rabbit", "judge holden", "blood meridian", "cormac"}
    combined = " ".join(case["source_text"].casefold() for case in load_cases(CASES_PATH))

    assert not any(term in combined for term in forbidden)


def fake_translator(state):
    if state.get("translation_strategy"):
        return {"raw_translation": "ON natural translation. Anlam korunur ve cumle yapisi dogal kalir."}
    return {"raw_translation": "OFF literal translation neden oldu ve olan ifade tarafindan uzatildi."}


def capture_translator_prompt(case, strategy_enabled: bool) -> str:
    with patch("src.agents.translator.ChatOpenAI") as mock_chat:
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="ceviri")
        mock_chat.return_value = llm

        translate_case(case, strategy_enabled=strategy_enabled)

    return llm.invoke.call_args.args[0]
