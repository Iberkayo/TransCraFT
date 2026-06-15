import sys
import os
import shutil
import json
import pytest
from pathlib import Path

# Setup path to import from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.tie.memory_manager import MemoryManager
from src.tie.router import ContextRouter
from src.tie.reviewer import MemoryReviewer

@pytest.fixture
def temp_memory_dir(tmp_path):
    """Fixture to create a temporary memory directory and clean it up."""
    memory_dir = tmp_path / "memory"
    yield memory_dir
    if memory_dir.exists():
        shutil.rmtree(memory_dir)

def test_work_memory_isolation(temp_memory_dir):
    """Test that Alice's memory is not loaded during an Attention paper run."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    router = ContextRouter(memory_manager=manager)
    
    # Save a character in Alice in Wonderland
    item_alice = {
        "key": "Mad Hatter",
        "value": "Çılgın Şapkacı",
        "type": "character_info",
        "confidence": 0.9,
        "notes": "Mad Hatter character"
    }
    manager.add_memory_item(scope="work", item=item_alice, scope_id="alice_in_wonderland")
    
    # Test loading memory for Attention run containing the term 'Mad Hatter'
    relevant_for_attention = router.retrieve_relevant_memory(
        source_text="The Mad Hatter sat at the table.",
        genre="tech",
        work_id="attention_is_all_you_need"
    )
    # Mad Hatter should NOT be returned because of work_id isolation
    assert not any(item["key"] == "Mad Hatter" for item in relevant_for_attention)
    
    # Test loading memory for Alice run containing the term 'Mad Hatter'
    relevant_for_alice = router.retrieve_relevant_memory(
        source_text="The Mad Hatter sat at the table.",
        genre="literary",
        work_id="alice_in_wonderland"
    )
    # Mad Hatter SHOULD be returned
    assert any(item["key"] == "Mad Hatter" for item in relevant_for_alice)

def test_genre_memory_isolation(temp_memory_dir):
    """Test that technical genre rules do not leak into literary context."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    router = ContextRouter(memory_manager=manager)
    
    # Save a technical term
    item_tech = {
        "key": "self-attention",
        "value": "öz-dikkat",
        "type": "terminology",
        "confidence": 0.9
    }
    manager.add_memory_item(scope="genre", item=item_tech, scope_id="tech")
    
    # Retrieve relevant memories for literary translation containing "self-attention"
    relevant_literary = router.retrieve_relevant_memory(
        source_text="He gave self-attention to his health.",
        genre="literary"
    )
    assert not any(item["key"] == "self-attention" for item in relevant_literary)
    
    # Retrieve relevant memories for tech translation
    relevant_tech = router.retrieve_relevant_memory(
        source_text="We use self-attention layers here.",
        genre="tech"
    )
    assert any(item["key"] == "self-attention" for item in relevant_tech)

def test_reviewer_rejects_wrong_scope(temp_memory_dir):
    """Test that MemoryReviewer rejects or flags incorrect scope/pollution."""
    reviewer = MemoryReviewer()
    
    # Scenario A: Ebook licensing / Gutenberg noise is rejected by prefilter
    noise_item = {
        "key": "Project Gutenberg License",
        "value": "Tüm hakları saklıdır",
        "type": "style_rule",
        "confidence": 0.8
    }
    result_noise = reviewer.review_candidate(noise_item)
    assert result_noise["status"] == "rejected"
    assert "Gutenberg" in result_noise["reviewer_notes"] or "metadata noise" in result_noise["reviewer_notes"]
    
    # Scenario B: Alice terms in Attention run (isolation breach)
    alice_in_tech_item = {
        "key": "Alice",
        "value": "Alice",
        "type": "character_info",
        "confidence": 0.9
    }
    result_breach = reviewer.review_candidate(
        alice_in_tech_item,
        work_id="attention_is_all_you_need"
    )
    assert result_breach["status"] == "rejected"
    assert "Work isolation breach" in result_breach["reviewer_notes"]

def test_pending_memory_created(temp_memory_dir):
    """Test that items with low confidence are marked pending and stored in pending_memory.jsonl."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    reviewer = MemoryReviewer()
    
    # Lower confidence item (heuristics will make status="pending" since style_rule confidence < 0.85)
    candidate = {
        "key": "custom style rule",
        "value": "always format in uppercase",
        "type": "style_rule",
        "confidence": 0.6
    }
    
    # Run evaluation
    reviewed = reviewer.review_candidate(candidate)
    assert reviewed["status"] == "pending"
    
    # Add to manager
    manager.add_memory_item(scope="global", item=reviewed)
    
    # Verify not in global active rules
    global_active = manager.get_memory_items(scope="global")
    assert len(global_active) == 0
    
    # Verify in pending_memory.jsonl
    pending_file = temp_memory_dir / "pending" / "pending_memory.jsonl"
    assert pending_file.exists()
    
    with open(pending_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]
        
    assert len(lines) == 1
    assert lines[0]["key"] == "custom style rule"
    assert lines[0]["status"] == "pending"

def test_memory_dedup_merge(temp_memory_dir):
    """Test that duplicates are merged rather than duplicated, updating usage_count, confidence."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    
    item1 = {
        "key": "break down",
        "value": "bozulmak",
        "type": "phrasal_verb",
        "confidence": 0.8,
        "importance_score": 0.6
    }
    manager.add_memory_item(scope="global", item=item1)
    
    # Add duplicate (same key, type, scope) with different translation and higher confidence
    item2 = {
        "key": "break down",
        "value": "parçalanmak",
        "type": "phrasal_verb",
        "confidence": 0.95,
        "importance_score": 0.8
    }
    manager.add_memory_item(scope="global", item=item2)
    
    global_items = manager.get_memory_items("global")
    assert len(global_items) == 1
    
    merged = global_items[0]
    assert merged["value"] == "parçalanmak"
    assert merged["usage_count"] == 2
    assert merged["confidence"] == 0.95
    assert merged["importance_score"] == 0.8

def test_router_max_memory_items(temp_memory_dir):
    """Test that ContextRouter respects max_memory_items parameter and sorts properly."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    router = ContextRouter(memory_manager=manager)
    
    # Add 25 rules with varying importance and confidence to global scope
    for idx in range(25):
        rule = {
            "key": f"rule {idx}",
            "value": f"value {idx}",
            "type": "style_rule",
            "confidence": 0.5 + (idx % 5) * 0.1,         # 0.5 to 0.9
            "importance_score": 0.5 + (idx // 5) * 0.1   # 0.5 to 0.9
        }
        manager.add_memory_item(scope="global", item=rule)
        
    relevant = router.retrieve_relevant_memory(
        source_text="any random source text to match style rules",
        max_memory_items=10
    )
    
    # Length check
    assert len(relevant) == 10
    
    # Sort check: first item should have the highest importance and confidence
    first = relevant[0]
    last = relevant[-1]
    
    assert first["importance_score"] >= last["importance_score"]
    if first["importance_score"] == last["importance_score"]:
        assert first["confidence"] >= last["confidence"]

def test_memory_metadata_schema(temp_memory_dir):
    """Test that saved items have all TIE v0.2 metadata fields."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    
    item = {
        "key": "gaze at",
        "value": "süzmek",
        "type": "phrasal_verb",
        "confidence": 0.8
    }
    manager.add_memory_item(scope="global", item=item, work_id="test_work", genre="literary", user_id="test_user")
    
    dest_file = temp_memory_dir / "global" / "rules.json"
    assert dest_file.exists()
    
    with open(dest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    saved_item = data[0]
    required_fields = [
        "importance_score", "usage_count", "status", "confidence", 
        "created_at", "updated_at", "source_work", "source_genre", "source_user"
    ]
    
    for field in required_fields:
        assert field in saved_item
        
    assert saved_item["source_work"] == "test_work"
    assert saved_item["source_genre"] == "literary"
    assert saved_item["source_user"] == "test_user"
