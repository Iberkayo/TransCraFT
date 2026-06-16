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