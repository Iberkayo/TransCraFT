"""Tests for v0.9.4 literary correction feedback."""

import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from src.tie.literary_feedback import (
    LiteraryCorrectionFeedbackStore,
    LiterarySuggestionGenerator,
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
    from src.tie.literary_feedback import write_suggested_edits_file

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "suggested_edits.md"
        chunks = [{
            "chunk_id": "test_001",
            "feedback_suggestion_count": 2,
            "literary_feedback_suggestions": [
                {"correction_id": "c1", "source_phrase": "test", "current_target": "bad", "suggested_target": "good", "severity": "major", "reason": "test reason", "apply_mode": "suggest_only"},
                {"correction_id": "c2", "source_phrase": "test2", "current_target": "bad2", "suggested_target": "good2", "severity": "minor", "reason": "test reason 2", "apply_mode": "suggest_only"},
            ],
        }]
        result = write_suggested_edits_file(output, chunks)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "c1" in text
        assert "c2" in text
        assert "accept / reject / modify" in text


def test_first5_suggested_edits_file_creates_file_when_no_suggestions():
    from src.tie.literary_feedback import write_suggested_edits_file

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "suggested_edits.md"
        chunks = [{"chunk_id": "test_001", "feedback_suggestion_count": 0, "literary_feedback_suggestions": []}]
        result = write_suggested_edits_file(output, chunks)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "No literary feedback suggestions were generated" in text


def test_suggested_edits_file_contains_reviewer_decision_placeholders():
    from src.tie.literary_feedback import write_suggested_edits_file

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "suggested_edits.md"
        chunks = [{
            "chunk_id": "test_001",
            "feedback_suggestion_count": 1,
            "literary_feedback_suggestions": [
                {"correction_id": "c1", "source_phrase": "test", "current_target": "bad", "suggested_target": "good", "severity": "major", "reason": "test", "apply_mode": "suggest_only"},
            ],
        }]
        result = write_suggested_edits_file(output, chunks)
        text = result.read_text(encoding="utf-8")
        assert "Reviewer decision:" in text
        assert "Reviewer notes:" in text
