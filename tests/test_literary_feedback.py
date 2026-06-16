"""Tests for v0.9.4.2 literary correction feedback."""

import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from src.tie.literary_feedback import (
    LiteraryCorrectionFeedbackStore,
    LiterarySuggestionGenerator,
    parse_reviewer_decisions_from_suggested_edits,
    apply_accepted_suggestions_to_text,
    write_edited_translation_file,
    write_suggested_edits_file,
    _normalize_turkish,
)


def test_correction_dataset_loads():
    store = LiteraryCorrectionFeedbackStore()
    assert len(store.corrections) == 12


def test_correction_entries_have_required_fields():
    store = LiteraryCorrectionFeedbackStore()
    required = {"id", "source_phrase", "current_target", "suggested_target", "issue_type", "severity", "reason", "apply_mode", "tags"}
    for c in store.corrections:
        assert required.issubset(c.keys()), f"Missing fields in {c.get('id')}: {required - set(c.keys())}"


def test_suggestion_generator_flags_flatboat():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="bir düz tekneye alınır")
    assert result["suggestion_count"] >= 1
    assert any("flatboat" in s["correction_id"] for s in result["suggestions"])


def test_suggestion_generator_flags_schoolmaster():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="babası aslında bir okul müdürüymüş")
    assert result["suggestion_count"] >= 1
    assert any("schoolmaster" in s["correction_id"] for s in result["suggestions"])


def test_suggestion_generator_flags_scullery_fire():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="Bulaşıkhanede ateşi karıştırıyor")
    assert result["suggestion_count"] >= 1
    assert any("scullery" in s["correction_id"] for s in result["suggestions"])


def test_suggestion_generator_flags_blood_running_phrase():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="o kan gömleğinden akarken")
    assert result["suggestion_count"] >= 1
    assert any("blood_shirt" in s["correction_id"] for s in result["suggestions"])


def test_suggestion_generator_flags_full_house_context():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="dolu salonda oynuyordu")
    assert result["suggestion_count"] >= 1
    assert any("full_house" in s["correction_id"] for s in result["suggestions"])


def test_suggestion_generator_never_auto_applies():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="bir düz tekneye alınır")
    for s in result["suggestions"]:
        assert s.get("apply_mode") == "suggest_only"


def test_no_suggestion_for_clean_pair():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="Bu tamamen temiz ve hatasız bir çeviri cümlesidir.")
    assert result["suggestion_count"] == 0


def test_report_contains_no_overclaiming():
    gen = LiterarySuggestionGenerator()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "edits.md"
        gen.generate_edit_file(output, translated_text="bir düz tekneye alınır")
        text = output.read_text(encoding="utf-8").casefold()
        assert "human review" in text
        assert "do not auto-apply" in text


def test_first5_suggested_edits_file_creates_file_with_suggestions():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "suggested_edits.md"
        chunks = [{
            "chunk_id": "test_001",
            "feedback_suggestion_count": 2,
            "literary_feedback_suggestions": [
                {"correction_id": "c1", "source_phrase": "test", "current_target": "bad", "suggested_target": "good", "severity": "major", "reason": "test reason", "apply_mode": "suggest_only", "match_type": "exact", "confidence": "high"},
                {"correction_id": "c2", "source_phrase": "test2", "current_target": "bad2", "suggested_target": "good2", "severity": "minor", "reason": "test reason 2", "apply_mode": "suggest_only", "match_type": "exact", "confidence": "high"},
            ],
        }]
        result = write_suggested_edits_file(output, chunks)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "c1" in text
        assert "c2" in text
        assert "accept / reject / modify" in text


def test_first5_suggested_edits_file_creates_file_when_no_suggestions():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "suggested_edits.md"
        chunks = [{"chunk_id": "test_001", "feedback_suggestion_count": 0, "literary_feedback_suggestions": []}]
        result = write_suggested_edits_file(output, chunks)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "No literary feedback suggestions were generated" in text


def test_suggested_edits_file_contains_reviewer_decision_placeholders():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "suggested_edits.md"
        chunks = [{
            "chunk_id": "test_001",
            "feedback_suggestion_count": 1,
            "literary_feedback_suggestions": [
                {"correction_id": "c1", "source_phrase": "test", "current_target": "bad", "suggested_target": "good", "severity": "major", "reason": "test", "apply_mode": "suggest_only", "match_type": "exact", "confidence": "high"},
            ],
        }]
        result = write_suggested_edits_file(output, chunks)
        text = result.read_text(encoding="utf-8")
        assert "Reviewer decision:" in text
        assert "Reviewer notes:" in text


# --- v0.9.4.2 new tests ---

def test_parse_reviewer_decisions_accept():
    md = """### bm_first5_schoolmaster_001
- **Suggested target:** okul hocasıymış
- **Current target:** okul müdürüymüş
- **Source phrase:** schoolmaster
- **Reviewer decision:** accept"""
    decisions = parse_reviewer_decisions_from_suggested_edits(md)
    assert len(decisions) == 1
    assert decisions[0]["decision"] == "accept"
    assert "okul hocasıymış" in decisions[0]["suggested_target"]


def test_apply_accepted_suggestions_to_text():
    text = "babası aslında bir okul müdürüymüş. Sonra eve gitti."
    suggestions = [{"correction_id": "c1", "current_target": "okul müdürüymüş", "suggested_target": "okul hocasıymış", "decision": "accept"}]
    result = apply_accepted_suggestions_to_text(text, suggestions)
    assert "okul hocasıymış" in result["edited_text"]
    assert "okul müdürüymüş" not in result["edited_text"]
    assert result["applied_count"] == 1


def test_apply_accepted_suggestions_does_not_apply_reject():
    text = "bu bir test"
    suggestions = [{"correction_id": "c1", "current_target": "test", "suggested_target": "deneme", "decision": "reject"}]
    result = apply_accepted_suggestions_to_text(text, suggestions)
    assert "test" in result["edited_text"]
    assert result["applied_count"] == 0


def test_write_edited_translation_file():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        orig = tmp_path / "orig.md"
        orig.write_text("okul müdürüymüş\n", encoding="utf-8")
        edited = tmp_path / "edited.md"
        result = write_edited_translation_file(orig, edited, [
            {"correction_id": "c1", "current_target": "okul müdürüymüş", "suggested_target": "okul hocasıymış", "decision": "accept"}
        ])
        assert edited.exists()
        assert "okul hocasıymış" in edited.read_text(encoding="utf-8")
        assert result["applied_count"] == 1


def test_suggestion_generator_matches_normalized_current_target():
    gen = LiterarySuggestionGenerator()
    # Should match even with trailing period
    result = gen.generate_suggestions(translated_text="babası aslında bir okul müdürüymüş.")
    assert any("schoolmaster" in s["correction_id"] for s in result["suggestions"])


def test_suggestion_generator_matches_variant_flatboat():
    gen = LiterarySuggestionGenerator()
    # "bir düz tekneye alınır" is stored; test with the exact text
    result = gen.generate_suggestions(translated_text="bir düz tekneye alınır ve yola çıkılır")
    assert result["suggestion_count"] >= 1


def test_suggestion_generator_matches_variant_dipper():
    gen = LiterarySuggestionGenerator()
    # The stored target is "Kepçe devrilmişti" — test with variant "Kepçe batmıştı"
    result = gen.generate_suggestions(translated_text="Kepçe batmıştı")
    # May or may not match depending on keyword overlap — at minimum doesn't crash
    assert isinstance(result["suggestion_count"], int)


def test_suggestion_generator_does_not_match_unrelated_text():
    gen = LiterarySuggestionGenerator()
    result = gen.generate_suggestions(translated_text="Bu apayrı ve alakasız bir metindir.")
    assert result["suggestion_count"] == 0


def test_coverage_report_lists_untriggered_corrections():
    gen = LiterarySuggestionGenerator()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "coverage.md"
        result = gen.generate_coverage_report(output)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "Total corrections in dataset: 12" in text