"""Tests for v0.9.1 human review calibration and error taxonomy."""

import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_schema() -> dict:
    return json.loads((PROJECT_ROOT / "data" / "eval" / "human_review_schema.json").read_text(encoding="utf-8"))


def test_human_review_schema_loads():
    schema = _load_schema()
    assert schema["version"] == "0.9.1"
    assert "fields" in schema
    assert "allowed_error_tags" in schema
    assert len(schema["allowed_error_tags"]) >= 20


def test_review_template_generator_outputs_json_and_md():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.generate_human_review_template import generate

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        json_out = tmp_path / "template.json"
        md_out = tmp_path / "template.md"
        # Use a minimal cases override
        cases_path = tmp_path / "cases.json"
        cases_path.write_text(json.dumps([{"id": "test_001", "genre": "general", "source_text": "Test.", "risk_type": ["test"], "expected_behavior": "test", "protected_terms": [], "source_language": "en_US", "target_language": "tr_TR"}]), encoding="utf-8")
        pack_path = tmp_path / "pack.md"
        pack_path.write_text("", encoding="utf-8")

        class Args:
            cases = cases_path
            pack = pack_path
            json_output = json_out
            md_output = md_out
        generate(Args)

        assert json_out.exists()
        assert md_out.exists()
        template = json.loads(json_out.read_text(encoding="utf-8"))
        assert len(template) == 1
        assert template[0]["case_id"] == "test_001"


def test_review_template_contains_all_cases():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    cases = json.loads((PROJECT_ROOT / "data" / "eval" / "end_to_end_quality_cases.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        json_out = tmp_path / "template.json"
        md_out = tmp_path / "template.md"
        pack_path = tmp_path / "pack.md"
        pack_path.write_text("", encoding="utf-8")

        class Args:
            cases = PROJECT_ROOT / "data" / "eval" / "end_to_end_quality_cases.json"
            pack = pack_path
            json_output = json_out
            md_output = md_out

        from scripts.generate_human_review_template import generate
        generate(Args)

        template = json.loads(json_out.read_text(encoding="utf-8"))
        assert len(template) == len(cases)


def test_review_template_does_not_fabricate_missing_outputs():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.generate_human_review_template import generate

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        json_out = tmp_path / "template.json"
        md_out = tmp_path / "template.md"
        cases_path = tmp_path / "cases.json"
        cases_path.write_text(json.dumps([{"id": "test", "genre": "general", "source_text": "Test.", "risk_type": ["test"], "expected_behavior": "test", "protected_terms": [], "source_language": "en_US", "target_language": "tr_TR"}]), encoding="utf-8")
        pack_path = tmp_path / "pack.md"
        pack_path.write_text("", encoding="utf-8")

        class Args:
            cases = cases_path
            pack = pack_path
            json_output = json_out
            md_output = md_out
        generate(Args)

        md_text = md_out.read_text(encoding="utf-8")
        assert "Not available" in md_text or "run the benchmark" in md_text.casefold()


def test_error_taxonomy_normalizes_tags():
    from src.tie.error_taxonomy import TranslationErrorTaxonomy

    tags = ["translationese", "UNKNOWN_TAG", "pronoun_overuse", "  meaning_loss  "]
    normalized = TranslationErrorTaxonomy.normalize_error_tags(tags)
    assert "translationese" in normalized
    assert "pronoun_overuse" in normalized
    assert "meaning_loss" in normalized
    assert "unknown_tag" not in normalized


def test_error_taxonomy_counts_tags():
    from src.tie.error_taxonomy import ErrorTaxonomyAnalyzer

    reviews = [
        {"error_tags": ["translationese", "pronoun_overuse"]},
        {"error_tags": ["translationese", "meaning_loss"]},
    ]
    counts = ErrorTaxonomyAnalyzer.count_error_tags(reviews)
    assert counts["translationese"] == 2
    assert counts["pronoun_overuse"] == 1


def test_error_taxonomy_summarizes_severity():
    from src.tie.error_taxonomy import ErrorTaxonomyAnalyzer

    reviews = [{"severity": "minor"}, {"severity": "critical"}, {"severity": "minor"}]
    sev = ErrorTaxonomyAnalyzer.summarize_severity(reviews)
    assert sev["minor"] == 2
    assert sev["critical"] == 1


def test_error_taxonomy_recommends_next_fixes():
    from src.tie.error_taxonomy import ErrorTaxonomyAnalyzer

    counts = {"translationese": 5, "pronoun_overuse": 3, "meaning_loss": 2}
    recs = ErrorTaxonomyAnalyzer.recommend_next_fixes(counts)
    assert any("naturalness" in r.casefold() for r in recs)
    assert any("accuracy" in r.casefold() for r in recs)


def test_analyzer_handles_missing_real_results():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.analyze_human_review_results import render_report

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "report.md"
        render_report([], output)
        assert output.exists()
        text = output.read_text(encoding="utf-8")
        assert "No Real Human Review Results Found" in text


def test_calibration_report_generation():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.tie.error_taxonomy import ErrorTaxonomyAnalyzer

    reviews = [
        {"preferred_output": "full_chain", "over_editing_detected": False, "protected_term_issue": False, "error_tags": ["translationese"], "severity": "minor"},
        {"preferred_output": "tie", "over_editing_detected": False, "protected_term_issue": False, "error_tags": ["no_clear_difference"], "severity": "none"},
    ]
    summary = ErrorTaxonomyAnalyzer.summarize_calibration(reviews)
    assert summary["total_reviewed"] == 2
    assert summary["full_chain_wins"] == 1
    assert summary["full_chain_win_rate"] == 0.5
    assert "translationese" in summary["error_tag_frequency"]


def test_report_contains_no_overclaiming():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.analyze_human_review_results import render_report

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "report.md"
        render_report([], output)
        text = output.read_text(encoding="utf-8").casefold()
        assert "human review is required" in text or "not a human evaluation" in text or "no real human review" in text


def test_no_hidden_cot_phrasing():
    path = PROJECT_ROOT / "src" / "tie" / "error_taxonomy.py"
    source = path.read_text(encoding="utf-8").casefold()
    for phrase in ["chain-of-thought", "think step by step", "show your reasoning", "reveal reasoning"]:
        assert phrase not in source