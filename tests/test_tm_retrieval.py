import json
from pathlib import Path

from scripts.query_translation_memory import main as query_main
from src.tie.tm_retrieval import (
    build_reference_pack,
    build_translation_reference_context,
    compute_similarity,
    load_tm_directory,
    load_tm_jsonl,
    normalize_retrieval_text,
    retrieve_translation_memory,
)


def synthetic_entry(
    tm_id: str,
    source: str,
    target: str,
    confidence: str = "high",
    pair_id: str = "synthetic_pair",
):
    return {
        "tm_id": tm_id,
        "pair_id": pair_id,
        "source_lang": "EN",
        "target_lang": "TR",
        "source_text": source,
        "target_text": target,
        "source_word_count": len(source.split()),
        "target_word_count": len(target.split()),
        "alignment_confidence": confidence,
        "domain_profile": {"detected_text_type": "literary", "detected_register": "plain"},
        "usage_policy": {"scope": "local_private_reference", "do_not_commit_full_text": True},
    }


def test_load_tm_jsonl(tmp_path):
    path = tmp_path / "sample_translation_memory.jsonl"
    entries = [
        synthetic_entry("tm_1", "The coach arrived.", "Araba geldi."),
        synthetic_entry("tm_2", "Night covered the road.", "Gece yolu kapladı."),
    ]
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in entries), encoding="utf-8")
    result = load_tm_jsonl(str(path))
    assert len(result) == 2
    assert result[0]["tm_id"] == "tm_1"
    assert result[0]["usage_policy"]["do_not_commit_full_text"] is True


def test_load_tm_directory_missing_returns_empty(tmp_path):
    result = load_tm_directory(str(tmp_path / "missing"))
    assert result == []


def test_normalize_retrieval_text():
    result = normalize_retrieval_text("  The COACH—arrived, late!  ")
    assert result == "the coach arrived late"


def test_similarity_scores_related_higher_than_unrelated():
    query = "The coach arrived late at night."
    related = compute_similarity(query, "The coach reached the town late at night.")
    unrelated = compute_similarity(query, "Data analytics improves company planning.")
    assert related > unrelated
    assert related > 0.25


def test_retrieve_filters_low_confidence_by_default():
    entries = [
        synthetic_entry("high", "The coach arrived late.", "Araba geç geldi.", "high"),
        synthetic_entry("low", "The coach arrived late at night.", "Araba gece geldi.", "low"),
    ]
    result = retrieve_translation_memory("The coach arrived late.", entries, min_score=0.0)
    assert [item["tm_id"] for item in result] == ["high"]


def test_retrieve_returns_top_k():
    entries = [
        synthetic_entry(f"tm_{index}", f"The coach arrived at hour {index}.", f"Araba {index}. saatte geldi.")
        for index in range(6)
    ]
    result = retrieve_translation_memory("The coach arrived.", entries, top_k=3, min_score=0.0)
    assert len(result) == 3
    assert result[0]["similarity_score"] >= result[1]["similarity_score"]


def test_reference_pack_schema():
    retrieved = retrieve_translation_memory(
        "The coach arrived.",
        [synthetic_entry("tm_1", "The coach arrived.", "Araba geldi.")],
        min_score=0.0,
    )
    pack = build_reference_pack("The coach arrived.", retrieved)
    assert {
        "query_text_hash",
        "query_word_count",
        "top_k",
        "references",
        "warnings",
    }.issubset(pack)
    reference = pack["references"][0]
    assert {"tm_id", "pair_id", "similarity_score", "source_preview", "target_preview", "usage_policy"}.issubset(reference)


def test_reference_pack_truncates_previews():
    source = "A" * 200
    target = "B" * 200
    retrieved = [
        {
            **synthetic_entry("tm_1", source, target),
            "similarity_score": 0.5,
        }
    ]
    pack = build_reference_pack("query", retrieved, max_chars_per_side=25)
    assert len(pack["references"][0]["source_preview"]) <= 25
    assert pack["references"][0]["source_preview"].endswith("...")


def test_reference_pack_marks_reference_only():
    retrieved = [
        {
            **synthetic_entry("tm_1", "A source sentence.", "Bir hedef cümle."),
            "similarity_score": 0.4,
        }
    ]
    reference = build_reference_pack("source", retrieved)["references"][0]
    assert reference["use_mode"] == "reference_only"
    assert reference["human_review_required"] is True
    assert reference["do_not_auto_copy"] is True


def test_build_translation_reference_context_handles_missing_tm_dir(tmp_path):
    pack = build_translation_reference_context("A source chunk.", tm_dir=str(tmp_path / "missing"))
    assert pack["references"] == []
    assert any("does not exist" in warning for warning in pack["warnings"])


def test_query_script_safe_preview_behavior(tmp_path, capsys):
    tm_dir = tmp_path / "tm"
    tm_dir.mkdir()
    long_source = "The coach arrived late at night. " + ("source-detail " * 50)
    long_target = "Posta arabası gece geç geldi. " + ("hedef-ayrıntı " * 50)
    path = tm_dir / "safe_translation_memory.jsonl"
    path.write_text(
        json.dumps(synthetic_entry("tm_safe", long_source, long_target), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    exit_code = query_main(
        [
            "--tm-dir",
            str(tm_dir),
            "--query",
            "The coach arrived late at night.",
            "--top-k",
            "1",
            "--max-chars-per-side",
            "40",
        ]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "source-detail source-detail source-detail source-detail source-detail" not in output
    assert "..." in output
    assert "References returned: 1" in output
