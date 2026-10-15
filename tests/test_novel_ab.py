"""Offline A/B smoke tests; no model calls or API credentials required."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.benchmark.novel_ab import (
    _make_blind_review,
    _response_text,
    run_novel_ab,
)


def _fixture(tmp_path: Path) -> Path:
    novel = tmp_path / "fiction.txt"
    novel.write_text(
        "CHAPTER ONE\n\n"
        "Mara watched the empty pier as the ferry disappeared into the fog. "
        "She held the unopened letter and wondered whether anyone still remembered her. "
        "At dawn, the old clock sounded once, and she walked away without looking back.\n\n"
        "\"Are you coming?\" said Theo. \"We don't have all morning.\" "
        "She smiled without answering, then folded the letter into her coat.",
        encoding="utf-8",
    )
    return novel


def test_offline_ab_uses_identical_source_and_writes_blind_pack(tmp_path: Path):
    result = run_novel_ab(
        _fixture(tmp_path),
        first_words=200,
        chunk_chars=220,
        output_root=tmp_path / "runs",
        dry_run=True,
        start_at="beginning",
        seed=12,
    )
    root = Path(result["output_dir"])
    assert result["status"] == "dry_run_no_model_calls"
    assert result["passages"] >= 1
    assert result["full_langgraph_tie_included"] is False
    assert result["arms"]["baseline"]["chunks"] == result["arms"]["direct"]["chunks"]
    assert result["arms"]["baseline"]["source_words"] == result["arms"]["direct"]["source_words"]

    blind = (root / "blind_review.md").read_text(encoding="utf-8")
    assert "Candidate A" in blind and "Candidate B" in blind
    assert "DRY RUN ONLY" in blind
    assert "Human evaluation" in blind
    assert (root / "comparison.json").exists()
    assert (root / "answer_key.json").exists()

    baseline_root = Path(result["arms"]["baseline"]["metadata_path"])
    direct_root = Path(result["arms"]["direct"]["metadata_path"])
    baseline = json.loads(baseline_root.read_text(encoding="utf-8"))
    direct = json.loads(direct_root.read_text(encoding="utf-8"))
    assert [chunk["source_text"] for chunk in baseline["chunks"]] == [
        chunk["source_text"] for chunk in direct["chunks"]
    ]


def test_blind_labels_are_seeded_and_reversible():
    left = [{"translation": "Türkçe birinci.", "source_text": "First English."}]
    right = [{"translation": "Türkçe ikinci.", "source_text": "First English."}]
    review1, key1 = _make_blind_review(left, right, seed=7, dry_run=False)
    review2, key2 = _make_blind_review(left, right, seed=7, dry_run=False)
    assert review1 == review2 and key1 == key2
    assert sorted(key1["passage_001"].values()) == ["baseline", "direct"]
    assert "baseline" not in review1.lower()
    assert "direct" not in review1.lower()


def test_model_response_content_validation():
    assert _response_text(SimpleNamespace(content=" Tamam. ")) == "Tamam."
    assert _response_text(SimpleNamespace(content=[
        {"type": "text", "text": "Merhaba"},
        {"type": "thinking", "text": "private"},
    ])) == "Merhaba"
    with pytest.raises(ValueError):
        _response_text(SimpleNamespace(content="  "))
    with pytest.raises(TypeError):
        _response_text(SimpleNamespace(content=42))


@pytest.mark.parametrize("first_words,chunk_chars", [(0, 3200), (100, 10)])
def test_rejects_invalid_ranges(tmp_path, first_words, chunk_chars):
    with pytest.raises(ValueError):
        run_novel_ab(
            _fixture(tmp_path),
            first_words=first_words,
            chunk_chars=chunk_chars,
            output_root=tmp_path / "runs",
            dry_run=True,
        )


def test_missing_source_fails_before_creating_run(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_novel_ab(
            tmp_path / "missing.epub",
            output_root=tmp_path / "runs",
            dry_run=True,
        )
