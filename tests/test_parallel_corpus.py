import json
from pathlib import Path

import pytest

from src.tie.parallel_corpus import (
    align_parallel_units,
    build_parallel_style_profile,
    build_translation_memory,
    discover_parallel_candidates,
    extract_glossary_candidates,
    normalize_parallel_text,
    segment_text_units,
)


def test_discover_parallel_candidates_with_manifest(tmp_path):
    manifest = {
        "pairs": [
            {
                "pair_id": "example_pair",
                "source_path": "data/inputs/EN/example.pdf",
                "target_path": "data/inputs/TR/ornek.pdf",
                "source_lang": "EN",
                "target_lang": "TR",
            }
        ]
    }
    (tmp_path / "parallel_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = discover_parallel_candidates(str(tmp_path), "EN", "TR")
    assert len(result) == 1
    assert result[0]["pair_id"] == "example_pair"
    assert result[0]["match_reason"] == "manifest"
    assert result[0]["match_confidence"] == "high"


def test_discover_parallel_candidates_auto_filename_similarity(tmp_path):
    source_dir = tmp_path / "EN"
    target_dir = tmp_path / "TR"
    source_dir.mkdir()
    target_dir.mkdir()
    (source_dir / "Shared Title Author.pdf").write_bytes(b"not-a-real-pdf")
    (target_dir / "Shared Title Author Turkish.pdf").write_bytes(b"not-a-real-pdf")
    result = discover_parallel_candidates(str(tmp_path), "EN", "TR")
    assert len(result) == 1
    assert result[0]["match_reason"].startswith("filename_similarity")
    assert result[0]["match_confidence"] in {"high", "medium"}


def test_normalize_parallel_text_removes_noise():
    text = "A soft\u00adword and zero\u200bwidth.\r\nHyphen-\nated text.\n\n\nNext."
    result = normalize_parallel_text(text)
    assert "\u00ad" not in result
    assert "\u200b" not in result
    assert "Hyphenated" in result
    assert "\n\n\n" not in result


def test_segment_text_units_paragraph_mode():
    text = "FIRST HEADING\n\nFirst paragraph has a sentence.\n\nSecond paragraph continues."
    result = segment_text_units(text, mode="paragraph")
    assert len(result) == 3
    assert result[0]["is_heading"] is True
    assert result[1]["page_number"] == 1
    assert result[2]["unit_id"] == "unit_000003"


def test_align_parallel_units_conservative():
    source = synthetic_units(["CHAPTER ONE", "A short source paragraph.", "Another source paragraph closes."])
    target = synthetic_units(["BÖLÜM BİR", "Kısa bir hedef paragraf.", "Bir başka hedef paragraf biter."])
    result = align_parallel_units(source, target, pair_id="synthetic")
    assert len(result["aligned_units"]) == 3
    assert sum(result["alignment_quality"].values()) == 3
    assert all(item["alignment_method"] == "sequence_length_heading" for item in result["aligned_units"])


def test_build_translation_memory_schema():
    alignment = align_parallel_units(
        synthetic_units(["A source sentence."]),
        synthetic_units(["Bir hedef cümle."]),
        pair_id="schema_pair",
    )
    result = build_translation_memory(alignment)
    assert len(result) == 1
    entry = result[0]
    assert {
        "tm_id",
        "pair_id",
        "source_lang",
        "target_lang",
        "source_text",
        "target_text",
        "source_word_count",
        "target_word_count",
        "alignment_confidence",
        "domain_profile",
        "usage_policy",
    }.issubset(entry)
    assert entry["usage_policy"]["do_not_commit_full_text"] is True


def test_glossary_candidates_schema():
    alignment = {
        "pair_id": "glossary_pair",
        "aligned_units": [
            {
                "source_text": "Count entered the room.",
                "target_text": "Kont odaya girdi.",
                "alignment_confidence": "high",
            },
            {
                "source_text": "Count opened the door.",
                "target_text": "Kont kapıyı açtı.",
                "alignment_confidence": "high",
            },
            {
                "source_text": "Count waited outside.",
                "target_text": "Kont dışarıda bekledi.",
                "alignment_confidence": "medium",
            },
        ],
    }
    result = extract_glossary_candidates(alignment)
    assert result
    candidate = next(item for item in result if item["source_term"] == "Count")
    assert candidate["target_candidates"] == ["Kont"]
    assert candidate["review_required"] is True


def test_style_profile_schema():
    alignment = align_parallel_units(
        synthetic_units(["He said, “Wait here.” Then he left.", "A second paragraph follows."]),
        synthetic_units(["“Burada bekle,” dedi. Sonra gitti.", "İkinci paragraf gelir."]),
        pair_id="style_pair",
    )
    result = build_parallel_style_profile(alignment)
    assert result["pair_id"] == "style_pair"
    assert {
        "average_source_sentence_length",
        "average_target_sentence_length",
        "dialogue_density",
        "paragraph_length_ratio",
        "target_punctuation_style",
    }.issubset(result["observations"])
    assert result["human_review_required"] is True


def test_alignment_marks_low_confidence_when_lengths_diverge():
    long_source = " ".join(["source"] * 100) + "."
    target = "Kısa hedef."
    result = align_parallel_units(
        synthetic_units([long_source]),
        synthetic_units([target]),
        pair_id="divergent",
    )
    assert result["alignment_quality"]["low"] == 1
    assert result["aligned_units"][0]["alignment_confidence"] == "low"


def test_local_parallel_pdf_discovery_smoke():
    root = Path("data/inputs")
    if not (root / "EN").exists() or not (root / "TR").exists():
        pytest.skip("Local EN/TR fixture directories are not available.")
    result = discover_parallel_candidates(str(root), "EN", "TR")
    assert isinstance(result, list)
    assert result


def synthetic_units(texts):
    units = []
    for index, text in enumerate(texts, start=1):
        units.append(
            {
                "unit_id": f"unit_{index:06d}",
                "text": text,
                "page_number": 1,
                "order": index - 1,
                "word_count": len(text.split()),
                "char_count": len(text),
                "sentence_count": 1,
                "is_heading": text.isupper(),
            }
        )
    return units
