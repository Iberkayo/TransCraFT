"""Scoring smoke tests with hand-created synthetic human scores."""
import json

import pytest

from scripts.score_novel_ab import score_novel_ab


def _fixture(tmp_path, *, dry_run=False):
    run = tmp_path / "run"
    run.mkdir()
    (run / "comparison.json").write_text(json.dumps({
        "status": "dry_run_no_model_calls" if dry_run else "awaiting_human_review",
        "direct_model": "test-direct",
        "baseline_model": "test-baseline",
    }), encoding="utf-8")
    (run / "answer_key.json").write_text(json.dumps({
        "passage_001": {"A": "baseline", "B": "direct"},
        "passage_002": {"A": "direct", "B": "baseline"},
    }), encoding="utf-8")
    scores = {
        "passages": [
            {
                "passage_id": "passage_001",
                "accuracy": {"A": 3, "B": 5},
                "naturalness": {"A": 3, "B": 4},
                "literary_voice": {"A": 2, "B": 5},
                "preference": "B",
                "notes": "Compared blindly.",
            },
            {
                "passage_id": "passage_002",
                "accuracy": {"A": 5, "B": 4},
                "naturalness": {"A": 5, "B": 2},
                "literary_voice": {"A": 5, "B": 4},
                "preference": "A",
                "notes": "Compared blindly.",
            },
        ],
    }
    path = tmp_path / "filled_scores.json"
    path.write_text(json.dumps(scores), encoding="utf-8")
    return run, path, scores


def test_aggregation_reveals_preference_only_after_score_file(tmp_path):
    run, scores_path, _ = _fixture(tmp_path)
    result = score_novel_ab(run, scores_path)
    assert result["most_preferred_arm"] == "direct"
    assert result["preference_counts"] == {"baseline": 0, "direct": 2, "tie": 0}
    assert result["mean_human_scores"]["direct"]["accuracy"] == 5
    assert result["mean_human_scores"]["baseline"]["accuracy"] == 3.5
    assert (run / "human_review_summary.json").exists()
    assert (run / "human_review_summary.md").exists()


def test_no_winner_allowed_for_dry_run(tmp_path):
    run, scores_path, _ = _fixture(tmp_path, dry_run=True)
    with pytest.raises(ValueError, match="Dry run"):
        score_novel_ab(run, scores_path)


@pytest.mark.parametrize("problem", ["missing", "score", "vote", "duplicate"])
def test_invalid_human_assessments_rejected(tmp_path, problem):
    run, scores_path, scores = _fixture(tmp_path)
    if problem == "missing":
        scores["passages"].pop()
    elif problem == "score":
        scores["passages"][0]["accuracy"]["B"] = None
    elif problem == "vote":
        scores["passages"][0]["preference"] = "direct"
    else:
        scores["passages"][1]["passage_id"] = "passage_001"
    scores_path.write_text(json.dumps(scores), encoding="utf-8")
    with pytest.raises(ValueError):
        score_novel_ab(run, scores_path)
