"""Tests for TIE v0.4.1 Memory Hygiene & Pruning."""

import copy
import json
import tempfile
import os
from pathlib import Path

from src.tie.memory_hygiene import MemoryHygieneManager
from src.tie.memory_manager import MemoryManager


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def _memory(
    memory_id,
    key,
    memory_type="terminology",
    scope="work",
    impact=0.0,
    harm=0.0,
    injected=0,
    detected=0,
    confidence=0.7,
    importance_score=0.5,
    sample_count=0,
):
    return {
        "memory_id": memory_id,
        "key": key,
        "value": "test_value",
        "type": memory_type,
        "scope": scope,
        "confidence": confidence,
        "importance_score": importance_score,
        "usage_count": 1,
        "times_loaded": 5,
        "times_injected": injected,
        "times_detected_in_output": detected,
        "estimated_quality_impact_avg": impact,
        "harm_score_avg": harm,
        "last_effectiveness_decision": None,
        "last_effectiveness_evidence": None,
        "effectiveness_updated_at": None,
        "effectiveness_sample_count": sample_count,
        "status": "active",
        "source_work": None,
        "source_genre": None,
        "source_user": None,
    }


# ------------------------------------------------------------------ #
#  Tests
# ------------------------------------------------------------------ #

def test_promote_high_impact_memory():
    hyg = MemoryHygieneManager(dry_run=True)
    mem = _memory("m1", "Judge Holden", scope="work", impact=0.95, harm=0.0, injected=3, detected=3)

    recs = hyg.evaluate([mem])
    assert len(recs) == 1
    assert recs[0]["decision"] == "promote"
    assert "High impact" in recs[0]["reason"]


def test_keep_medium_impact_memory():
    hyg = MemoryHygieneManager(dry_run=True)
    mem = _memory("m2", "Semicolon rule", scope="global", impact=0.66, harm=0.0, injected=3, detected=3)

    recs = hyg.evaluate([mem])
    assert len(recs) == 1
    assert recs[0]["decision"] == "keep"


def test_downgrade_unused_memory():
    hyg = MemoryHygieneManager(dry_run=True)
    mem = _memory("m3", "Newspaper name", scope="global", impact=0.0, harm=0.0, injected=4, detected=0)

    recs = hyg.evaluate([mem])
    assert len(recs) == 1
    assert recs[0]["decision"] == "downgrade"


def test_review_harmful_memory():
    hyg = MemoryHygieneManager(dry_run=True)
    mem = _memory("m4", "Bad term", scope="global", impact=0.5, harm=0.35, injected=2, detected=2)

    recs = hyg.evaluate([mem])
    assert len(recs) == 1
    assert recs[0]["decision"] == "review"
    assert "Harm score elevated" in recs[0]["reason"]


def test_retire_candidate_only_for_global_memory():
    hyg = MemoryHygieneManager(dry_run=True)

    # A work-scoped memory with the same stats should NOT be retire_candidate
    work_mem = _memory("w1", "Work memory", scope="work", impact=0.05, harm=0.0, injected=6, detected=0)
    recs = hyg.evaluate([work_mem])
    assert recs[0]["decision"] != "retire_candidate"

    # But a global memory with the same stats SHOULD be retire_candidate
    global_mem = _memory("g1", "Global noise", scope="global", impact=0.05, harm=0.0, injected=6, detected=0)
    recs = hyg.evaluate([global_mem])
    assert recs[0]["decision"] == "retire_candidate"


def test_dry_run_does_not_mutate_files():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = MemoryManager(base_dir=tmp_path / "memory")

        # Add a memory item
        manager.add_memory_item(
            scope="work",
            scope_id="test_work",
            item={
                "key": "Judge Holden",
                "value": "Yargic Holden",
                "type": "character_info",
                "confidence": 0.9,
            },
            work_id="test_work",
            genre="literary",
        )

        # Manually inject effectiveness data
        items_before = manager.all_memory_items()
        for item in items_before:
            item["times_injected"] = 3
            item["times_detected_in_output"] = 3
            item["estimated_quality_impact_avg"] = 0.95
            item["effectiveness_sample_count"] = 3

        # Run dry-run evaluation
        hyg = MemoryHygieneManager(dry_run=True, memory_dir=manager.base_dir)
        recs = hyg.evaluate(items_before)
        assert len(recs) == 1

        # Apply in dry-run mode (should return mutations count but NOT write to disk)
        updated, mutations = hyg.apply(copy.deepcopy(items_before), recs)
        assert mutations > 0

        # Reload from disk — files should be UNCHANGED
        items_after = manager.all_memory_items()
        assert len(items_after) == 1
        # No hygiene fields should be present
        for item in items_after:
            assert "hygiene_status" not in item or item.get("hygiene_status") is None


def test_apply_updates_metadata_without_deleting_memory():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = MemoryManager(base_dir=tmp_path / "memory")

        # Add two memories
        for i, (key, imp) in enumerate([("High value", 0.95), ("Low value", 0.0)]):
            manager.add_memory_item(
                scope="work",
                scope_id="test_work",
                item={
                    "key": key,
                    "value": "val",
                    "type": "terminology",
                    "confidence": 0.9,
                },
                work_id="test_work",
                genre="literary",
            )

        items_before = manager.all_memory_items()
        assert len(items_before) == 2

        # Inject effectiveness
        for item in items_before:
            if item["key"] == "High value":
                item["times_injected"] = 3
                item["times_detected_in_output"] = 3
                item["estimated_quality_impact_avg"] = 0.95
                item["effectiveness_sample_count"] = 3
            else:
                item["times_injected"] = 5
                item["times_detected_in_output"] = 0
                item["estimated_quality_impact_avg"] = 0.0
                item["effectiveness_sample_count"] = 5

        # Apply (not dry-run)
        hyg = MemoryHygieneManager(dry_run=False, memory_dir=manager.base_dir)
        recs = hyg.evaluate(items_before)

        updated, mutations = hyg.apply(items_before, recs)
        assert mutations == 2

        # Verify in-memory updates
        for item in updated:
            assert "hygiene_status" in item
            assert "hygiene_reason" in item
            assert "hygiene_updated_at" in item
            assert "previous_importance_score" in item
            assert "effectiveness_observation_count" in item

        # Verify both memories still exist (no deletion)
        items_after = manager.all_memory_items()
        assert len(items_after) == 2


def test_global_low_value_memory_downranked():
    hyg = MemoryHygieneManager(dry_run=True)
    mem = _memory("g2", "Date format", scope="global", impact=0.0, harm=0.0, injected=5, detected=0, importance_score=0.6)

    recs = hyg.evaluate([mem])
    assert recs[0]["decision"] in {"downgrade", "retire_candidate"}

    # Test importance score adjustment
    items = copy.deepcopy([mem])
    updated, mutations = hyg.apply(items, recs)
    assert mutations == 1
    # Importance should decrease
    assert updated[0]["importance_score"] < 0.6


def test_work_memory_not_retired_too_aggressively():
    hyg = MemoryHygieneManager(dry_run=True)

    # A work-scoped memory that's been injected many times but never detected
    # should NOT be retire_candidate (retire_candidate only for global)
    work_mem = _memory("w2", "Chapter title", scope="work", impact=0.05, harm=0.0, injected=6, detected=0)

    recs = hyg.evaluate([work_mem])
    # Should be "downgrade" not "retire_candidate" since it's not global
    assert recs[0]["decision"] in {"downgrade", "review"}
    assert recs[0]["decision"] != "retire_candidate"


def test_dry_run_does_not_create_backup_directory():
    """Prove that --dry-run mode (enable_backups=False) does not create memory_backup_*."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True)

        # Create a minimal memory file so MemoryManager finds the dir
        global_dir = memory_dir / "global"
        global_dir.mkdir(parents=True)
        rules_file = global_dir / "rules.json"
        rules_file.write_text(
            json.dumps(
                [
                    {
                        "key": "t1",
                        "value": "v1",
                        "type": "terminology",
                        "scope": "global",
                        "memory_id": "test1",
                        "times_injected": 0,
                        "times_detected_in_output": 0,
                        "estimated_quality_impact_avg": 0.0,
                        "harm_score_avg": 0.0,
                        "effectiveness_sample_count": 0,
                        "importance_score": 0.5,
                        "status": "active",
                        "confidence": 0.7,
                    }
                ]
            ),
            encoding="utf-8",
        )

        # Record existing folders before creating MemoryManager
        existing = set(os.listdir(tmp_path))

        # Create manager with enable_backups=False (dry-run mode)
        manager = MemoryManager(base_dir=memory_dir, enable_backups=False)
        items = manager.all_memory_items()
        assert len(items) >= 1

        # Check no memory_backup_* directory was created
        after = set(os.listdir(tmp_path))
        new_dirs = after - existing
        backup_dirs = [d for d in new_dirs if "memory_backup" in str(d)]
        assert not backup_dirs, f"Backup directory created in dry-run mode: {backup_dirs}"

        # Also explicitly check the parent of memory_dir
        parent_contents = os.listdir(tmp_path)
        backups_in_parent = [d for d in parent_contents if "memory_backup" in str(d)]
        assert not backups_in_parent, f"Backup directory found: {backups_in_parent}"