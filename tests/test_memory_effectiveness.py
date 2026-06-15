import json

from src.tie.memory_effectiveness import MemoryEffectivenessEvaluator
from src.tie.memory_manager import MemoryManager


def _memory(memory_id, key, value, memory_type="terminology", scope="work"):
    return {
        "memory_id": memory_id,
        "key": key,
        "value": value,
        "type": memory_type,
        "scope": scope,
        "confidence": 0.9,
        "importance_score": 0.8,
    }


def test_terminology_memory_detected_in_output():
    evaluator = MemoryEffectivenessEvaluator()
    memory = _memory("m1", "Transformer", "Transformer")

    records = evaluator.evaluate_chunk(
        source_text="The Transformer uses attention.",
        translated_text="Transformer dikkat kullanir.",
        loaded_memories=[memory],
        injected_memory_ids=["m1"],
        genre="tech",
        work_id="attention_is_all_you_need",
    )

    assert records[0]["detected_in_output"] is True
    assert records[0]["usage_score"] > 0.6
    assert records[0]["decision"] in {"keep", "promote"}


def test_character_memory_detected_in_output():
    evaluator = MemoryEffectivenessEvaluator()
    memory = _memory("m2", "Judge Holden", "Yargic Holden", memory_type="character_info")

    records = evaluator.evaluate_chunk(
        source_text="Judge Holden entered.",
        translated_text="Yargic Holden iceri girdi.",
        loaded_memories=[memory],
        injected_memory_ids=["m2"],
        genre="literary",
        work_id="blood_meridian",
    )

    assert records[0]["detected_in_output"] is True
    assert records[0]["estimated_quality_impact"] > 0.6


def test_unused_memory_gets_low_usage_score():
    evaluator = MemoryEffectivenessEvaluator()
    memory = _memory("m3", "Rabbit", "Tavsan", memory_type="character_info")

    records = evaluator.evaluate_chunk(
        source_text="Rabbit ran away.",
        translated_text="Hayvan uzaklasti.",
        loaded_memories=[memory],
        injected_memory_ids=["m3"],
    )

    assert records[0]["detected_in_output"] is False
    assert records[0]["usage_score"] < 0.2
    assert records[0]["decision"] == "downgrade"


def test_harmful_forbidden_term_detected():
    evaluator = MemoryEffectivenessEvaluator()
    memory = _memory("m4", "literal bad term", "yanlis terim", memory_type="forbidden_term")

    records = evaluator.evaluate_chunk(
        source_text="Avoid the literal bad term.",
        translated_text="Bu ceviri yanlis terim kullaniyor.",
        loaded_memories=[memory],
        injected_memory_ids=["m4"],
    )

    assert records[0]["harm_score"] >= 0.8
    assert records[0]["decision"] == "retire"


def test_memory_metadata_update(tmp_path):
    manager = MemoryManager(base_dir=tmp_path / "memory")
    manager.add_memory_item(
        scope="work",
        scope_id="test_work",
        item={
            "key": "Transformer",
            "value": "Transformer",
            "type": "terminology",
            "confidence": 0.9,
        },
        work_id="test_work",
        genre="tech",
    )
    saved = manager.get_memory_items("work", "test_work")[0]
    memory_id = saved["memory_id"]

    assert manager.record_memory_loaded([memory_id]) == 1
    assert manager.record_memory_injected([memory_id]) == 1
    manager.update_memory_effectiveness(
        [
            {
                "memory_id": memory_id,
                "detected_in_output": True,
                "estimated_quality_impact": 0.8,
                "harm_score": 0.0,
                "decision": "promote",
                "evidence": "Detected in output.",
            }
        ]
    )

    updated = manager.get_memory_items("work", "test_work")[0]
    assert updated["times_loaded"] == 1
    assert updated["times_injected"] == 1
    assert updated["times_detected_in_output"] == 1
    assert updated["estimated_quality_impact_avg"] == 0.8
    assert updated["last_effectiveness_decision"] == "promote"
    assert updated["effectiveness_updated_at"]


def test_report_generation(tmp_path):
    evaluator = MemoryEffectivenessEvaluator()
    records = [
        {
            "memory_id": "m1",
            "key": "Transformer",
            "type": "terminology",
            "scope": "work",
            "loaded": True,
            "injected": True,
            "detected_in_output": True,
            "estimated_quality_impact": 0.8,
            "harm_score": 0.0,
            "decision": "promote",
            "source_work": "attention_is_all_you_need",
            "source_genre": "tech",
        }
    ]
    output_path = evaluator.generate_report(records, tmp_path / "memory_effectiveness_report.md")

    assert output_path.exists()
    report = output_path.read_text(encoding="utf-8")
    assert "Top 20 Most Useful Memories" in report
    assert "Memory Usage by Scope" in report
    assert "Transformer" in report


def test_fail_safe_when_no_memories():
    evaluator = MemoryEffectivenessEvaluator()

    records = evaluator.evaluate_chunk(
        source_text="A sentence.",
        translated_text="Bir cumle.",
        loaded_memories=[],
        injected_memory_ids=[],
    )

    assert records == []
    summary = evaluator.summarize_records(records)
    assert summary["memory_loaded_count"] == 0
    assert summary["memory_use_rate"] == 0.0
