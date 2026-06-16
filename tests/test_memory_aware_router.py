from src.tie.memory_manager import MemoryManager
from src.tie.memory_ranker import MemoryAwareRanker
from src.tie.router import ContextRouter


def _memory(
    memory_id,
    key,
    value="val",
    memory_type="terminology",
    scope="work",
    hygiene_status="keep",
    impact=0.0,
    harm=0.0,
    injected=0,
    detected=0,
    importance=0.5,
    confidence=0.8,
):
    return {
        "memory_id": memory_id,
        "key": key,
        "value": value,
        "type": memory_type,
        "scope": scope,
        "scope_id": "scope1",
        "confidence": confidence,
        "importance_score": importance,
        "status": "active",
        "hygiene_status": hygiene_status,
        "hygiene_reason": "",
        "estimated_quality_impact_avg": impact,
        "harm_score_avg": harm,
        "times_loaded": 0,
        "times_injected": injected,
        "times_detected_in_output": detected,
        "last_effectiveness_decision": None,
        "effectiveness_observation_count": injected,
    }


def test_promoted_work_memory_prioritized():
    ranker = MemoryAwareRanker()
    source = "Judge Holden enters the room."
    memories = [
        _memory("g1", "Judge Holden", "Yargic Holden", scope="global", hygiene_status="keep", impact=0.2),
        _memory("w1", "Judge Holden", "Yargic Holden", scope="work", hygiene_status="promote", impact=0.95, detected=3),
    ]

    result = ranker.route(source, memories, max_memory_items=5)

    assert result["injected"][0]["memory_id"] == "w1"
    assert result["routing_decisions"][1]["reason"]


def test_global_retire_candidate_skipped():
    ranker = MemoryAwareRanker()
    memories = [
        _memory("g1", "Date format", "1 Ocak 2024", scope="global", hygiene_status="retire_candidate", impact=0.0),
    ]

    result = ranker.route("No matching date term here.", memories)

    assert result["injected"] == []
    assert result["routing_decisions"][0]["decision"] == "skip"
    assert "retire_candidate" in result["routing_decisions"][0]["reason"]


def test_downgraded_memory_downranked():
    ranker = MemoryAwareRanker()
    memories = [
        _memory("m1", "Chapter title", "Bolum basligi", scope="work", hygiene_status="downgrade", impact=0.0, injected=4),
    ]

    result = ranker.route("Chapter title appears.", memories)

    assert result["routing_decisions"][0]["decision"] in {"downrank", "skip"}
    assert "downgrade" in result["routing_decisions"][0]["reason"]


def test_high_harm_memory_skipped():
    ranker = MemoryAwareRanker()
    memories = [
        _memory("m1", "Bad term", "kotu terim", scope="work", impact=0.9, harm=0.5),
    ]

    result = ranker.route("Bad term appears.", memories)

    assert result["injected"] == []
    assert result["routing_decisions"][0]["decision"] == "skip"
    assert "harm" in result["routing_decisions"][0]["reason"]


def test_global_memory_share_capped():
    ranker = MemoryAwareRanker(global_share_cap=0.30)
    source = " ".join([f"term{i}" for i in range(20)])
    memories = []
    for idx in range(4):
        memories.append(
            _memory(f"w{idx}", f"term{idx}", scope="work", hygiene_status="promote", impact=0.8, detected=2)
        )
    for idx in range(4, 14):
        memories.append(
            _memory(f"g{idx}", f"term{idx}", scope="global", hygiene_status="keep", impact=0.8, detected=2)
        )

    result = ranker.route(source, memories, max_memory_items=10)
    injected = result["injected"]
    global_share = sum(1 for item in injected if item["scope"] == "global") / len(injected)

    assert global_share <= 0.30


def test_router_preserves_backward_compatibility(tmp_path):
    manager = MemoryManager(base_dir=tmp_path / "memory", enable_backups=False)
    manager.add_memory_item(
        scope="work",
        scope_id="test_work",
        work_id="test_work",
        item={"key": "Transformer", "value": "Transformer", "type": "terminology", "confidence": 0.9},
    )
    router = ContextRouter(memory_manager=manager, record_usage=False)

    relevant = router.retrieve_relevant_memory("The Transformer is useful.", work_id="test_work")
    context = router.generate_compact_context(relevant)

    assert isinstance(relevant, list)
    assert "Transformer" in context
    assert router.last_injected_memory_ids
    assert isinstance(router.last_routing_decisions, list)


def test_routing_decisions_include_reason():
    ranker = MemoryAwareRanker()
    memories = [_memory("m1", "Transformer", "Transformer", scope="work", impact=0.8)]

    result = ranker.route("Transformer model.", memories)

    assert result["routing_decisions"][0]["reason"]
    assert result["routing_decisions"][0]["final_score"] > 0


def test_missing_effectiveness_metadata_safe_defaults():
    ranker = MemoryAwareRanker()
    memory = {
        "memory_id": "old1",
        "key": "Alice",
        "value": "Alice",
        "type": "character_info",
        "scope": "work",
    }

    result = ranker.route("Alice looked around.", [memory])

    assert result["injected"]
    assert result["routing_decisions"][0]["decision"] == "inject"


def test_exact_match_can_allow_global_memory_when_safe():
    ranker = MemoryAwareRanker()
    memory = _memory(
        "g1",
        "ORANGE MARMALADE",
        "PORTAKAL RECELI",
        scope="global",
        hygiene_status="retire_candidate",
        impact=0.95,
        harm=0.0,
        detected=2,
        importance=0.9,
        confidence=0.95,
    )

    result = ranker.route("The jar said ORANGE MARMALADE.", [memory])

    assert result["injected"][0]["memory_id"] == "g1"
    assert "Retire candidate allowed" in result["routing_decisions"][0]["reason"]


def test_no_memory_case_returns_empty_context(tmp_path):
    router = ContextRouter(memory_manager=MemoryManager(base_dir=tmp_path / "memory", enable_backups=False), record_usage=False)

    context = router.generate_compact_context([])

    assert context == ""
    assert router.ranker.route("source", [], max_memory_items=5)["injected"] == []
