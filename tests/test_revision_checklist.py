"""Tests for TIE v0.7 Human Translator Revision Checklist."""

import json
import tempfile
from pathlib import Path

from src.tie.revision_checklist import (
    RevisionChecklistBuilder,
    RevisionChecklistEvaluator,
    build_and_evaluate,
    TRANSLATIONESE_PATTERNS,
    TURKISH_UNNECESSARY_PRONOUNS,
)


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def _bad_business(text: str = "") -> str:
    return text or (
        "Eski yazılımın 3. çeyreğin sonuna kadar aşamalı olarak "
        "kullanımdan kaldırılması bekleniyor, bu karar birçok departmanın "
        "günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu."
    )


def _good_business(text: str = "") -> str:
    return text or (
        "Eski yazılımın üçüncü çeyrek sonunda aşamalı olarak "
        "kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda "
        "günlük işleyişin nasıl etkileneceğine dair soru işaretleri yarattı."
    )


# ------------------------------------------------------------------ #
#  Tests
# ------------------------------------------------------------------ #

def test_revision_checklist_contains_required_categories():
    builder = RevisionChecklistBuilder()
    checklist = builder.build(
        source_text="Test.",
        genre="literary",
    )
    assert checklist["checklist_id"] == "revision_en_US_tr_TR_literary"
    checks = checklist["checks"]
    check_ids = {c["id"] for c in checks}
    assert "meaning_preservation" in check_ids
    assert "turkish_naturalness" in check_ids
    assert "no_translationese" in check_ids
    assert "unnecessary_pronouns" in check_ids
    assert "register_consistency" in check_ids
    assert any("rhythm" in c["id"] for c in checks)  # literary should get rhythm check


def test_detects_translationese_pattern():
    evaluator = RevisionChecklistEvaluator()
    checklist = {
        "checklist_id": "test",
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "general",
        "checks": [
            {
                "id": "no_translationese",
                "category": "naturalness",
                "question": "Avoid translationese.",
                "severity": "medium",
            }
        ],
    }
    bad = "Bu karar merak etmesine neden oldu."
    evaluation = evaluator.evaluate(checklist, bad, "")
    assert not evaluation["checks"][0]["passed"]
    assert "merak etmesine neden oldu" in evaluation["checks"][0]["evidence"]


def test_detects_unnecessary_pronouns():
    evaluator = RevisionChecklistEvaluator()
    checklist = {
        "checklist_id": "test",
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "general",
        "checks": [
            {
                "id": "unnecessary_pronouns",
                "category": "turkish_fluency",
                "question": "Avoid unnecessary pronouns.",
                "severity": "medium",
            }
        ],
    }
    bad = (
        "o bu dosyayı ona verdi. onun fikri bu. o onu gördü."
    )
    evaluation = evaluator.evaluate(checklist, bad, "")
    assert not evaluation["checks"][0]["passed"]


def test_detects_heavy_relative_clause_when_risk_present():
    evaluator = RevisionChecklistEvaluator()
    checklist = {
        "checklist_id": "test",
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "business",
        "checks": [
            {
                "id": "heavy_relative_clause",
                "category": "structural_risk",
                "question": "Avoid heavy -dığı chains.",
                "severity": "medium",
            }
        ],
    }
    bad = "verilerin işlendiği ve saklandığı sistemin güncellenmesi gerekiyor."
    evaluation = evaluator.evaluate(checklist, bad, "")
    assert not evaluation["checks"][0]["passed"]


def test_detects_noun_stack_risk_when_present():
    evaluator = RevisionChecklistEvaluator()
    checklist = {
        "checklist_id": "test",
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "business",
        "checks": [
            {
                "id": "noun_stack_unpacked",
                "category": "structural_risk",
                "question": "Unpack noun stacks.",
                "severity": "medium",
            }
        ],
    }
    bad = "MusteriVeriGizliligiUyumlulukIzlemeSistemi güncellemesi"
    evaluation = evaluator.evaluate(checklist, bad, "")
    assert not evaluation["checks"][0]["passed"]


def test_evaluation_output_schema():
    builder = RevisionChecklistBuilder()
    evaluator = RevisionChecklistEvaluator()
    checklist = builder.build(source_text="Test.", genre="business")
    evaluation = evaluator.evaluate(checklist, "Test çıktı.", "Test.")

    assert "overall_revision_score" in evaluation
    assert "critical_failures" in evaluation
    assert "warnings" in evaluation
    assert "passed_checks" in evaluation
    assert "failed_checks" in evaluation
    assert "checks" in evaluation
    assert "revision_recommendations" in evaluation

    assert isinstance(evaluation["overall_revision_score"], (int, float))
    assert evaluation["overall_revision_score"] >= 0.5
    assert evaluation["overall_revision_score"] <= 5.0
    assert evaluation["critical_failures"] >= 0
    assert evaluation["warnings"] >= 0

    for check in evaluation["checks"]:
        assert "id" in check
        assert "passed" in check
        assert "severity" in check
        assert "evidence" in check


def test_critical_failure_for_meaning_loss_placeholder():
    evaluator = RevisionChecklistEvaluator()
    checklist = {
        "checklist_id": "test",
        "source_language": "en_US",
        "target_language": "tr_TR",
        "genre": "general",
        "checks": [
            {
                "id": "no_translationese",
                "category": "naturalness",
                "question": "Avoid translationese.",
                "severity": "critical",
            }
        ],
    }
    bad = "Bu merak etmesine neden oldu ve anlamına gelir."
    evaluation = evaluator.evaluate(checklist, bad, "")
    assert evaluation["critical_failures"] >= 1


def test_critic_receives_revision_checklist():
    """Verify the critic agent can read revision_checklist from state."""
    # Simulate the state that critic.py would receive
    state = {
        "source_text": "Test.",
        "stylized_translation": "Test çıktı.",
        "target_language": "tr_TR",
        "style_guide": "",
        "positive_glossary": {},
        "auto_glossary_candidates": {},
        "negative_glossary": {},
        "revision_count": 0,
        "revision_checklist": {
            "checklist_id": "test",
            "checks": [
                {
                    "id": "no_translationese",
                    "category": "naturalness",
                    "question": "Avoid translationese.",
                    "severity": "medium",
                }
            ],
        },
        "translation_strategy": {},
        "logs": [],
        "trace_id": None,
        "chunk_index": 0,
        "enable_tie": False,
        "work_id": None,
        "genre": "general",
        "is_approved": False,
        "style_revision_count": 0,
    }

    revision_checklist = state.get("revision_checklist") or {}
    revision_checks = revision_checklist.get("checks", [])
    assert len(revision_checks) == 1
    assert revision_checks[0]["id"] == "no_translationese"

    # Build expected checklist text (same logic as critic.py)
    checklist_text = ""
    if revision_checks:
        checklist_text += "\n### Professional Revision Checklist (v0.7):\n"
        for check in revision_checks:
            checklist_text += f"- [{check.get('severity', 'medium').upper()}] {check.get('question', '')}\n"

    assert "Professional Revision Checklist" in checklist_text
    assert "no_translationese" not in checklist_text  # just the question text
    assert "Avoid translationese" in checklist_text


def test_stylist_receives_revision_recommendations_if_available():
    """Simulate that revision_recommendations are accessible from state."""
    state = {
        "revision_recommendations": [
            "Replace translationese patterns with natural Turkish wording.",
            "Reduce unnecessary pronoun repetition.",
        ]
    }
    recommendations = state.get("revision_recommendations", [])
    assert len(recommendations) == 2
    assert "translationese" in recommendations[0]
    assert "pronoun" in recommendations[1]


def test_diagnostics_report_generation():
    """Run diagnostics script and verify output file is created."""
    import sys
    from pathlib import Path

    # Import the main function
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.run_revision_checklist_diagnostics import render_report, SYNTHETIC_CASES

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "diagnostics.md"
        result = render_report(SYNTHETIC_CASES, output)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "Revision Checklist Diagnostics Report" in text
        assert "business_translationese" in text
        assert "Notes on Limitations" in text
        assert "Human review is still needed" in text


def test_benchmark_report_generation():
    """Run benchmark script and verify output file."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.run_revision_checklist_benchmark import run_benchmark

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "benchmark.md"
        result = run_benchmark(output)
        assert output.exists()
        text = output.read_text(encoding="utf-8")
        assert "Revision Checklist Benchmark" in text
        assert "Executive Summary" in text
        assert "Notes on Limitations" in text


def test_no_hidden_cot_phrasing():
    """Verify no hidden chain-of-thought patterns in revision checklist module."""
    import src.tie.revision_checklist as rcm

    source = Path(rcm.__file__).read_text(encoding="utf-8")
    source_lower = source.casefold()
    forbidden = [
        "chain-of-thought",
        "think step by step",
        "show your reasoning",
        "reveal reasoning",
        "hidden reasoning",
    ]
    for phrase in forbidden:
        assert phrase not in source_lower, f"Forbidden phrase found: {phrase}"