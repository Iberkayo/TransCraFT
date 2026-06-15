import sys
from pathlib import Path
import pytest
import shutil

# Setup path to import from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.tie.memory_manager import MemoryManager
from src.tie.router import ContextRouter
from src.tie.curator import MemoryCurator
from src.tie.handoff import HandoffGenerator

@pytest.fixture
def temp_memory_dir(tmp_path):
    """Fixture to create a temporary memory directory and clean it up."""
    memory_dir = tmp_path / "memory"
    yield memory_dir
    if memory_dir.exists():
        shutil.rmtree(memory_dir)

def test_memory_load_save(temp_memory_dir):
    """Test memory manager CRUD and duplicate prevention."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    
    # 1. Add global memory item
    item_global = {
        "key": "look up to",
        "value": "hayranlık duymak",
        "type": "phrasal_verb",
        "confidence": 0.9,
        "notes": "respect someone"
    }
    manager.add_memory_item(scope="global", item=item_global)
    
    # Verify save
    global_items = manager.get_memory_items(scope="global")
    assert len(global_items) == 1
    assert global_items[0]["key"] == "look up to"
    assert global_items[0]["value"] == "hayranlık duymak"
    assert global_items[0]["confidence"] == 0.9
    
    # 2. Add duplicate item with higher confidence
    item_dup = {
        "key": "look up to",
        "value": "saygı duymak",
        "type": "phrasal_verb",
        "confidence": 0.95,
        "notes": "updated translation"
    }
    manager.add_memory_item(scope="global", item=item_dup)
    
    # Verify duplicate prevention / update
    global_items_updated = manager.get_memory_items(scope="global")
    assert len(global_items_updated) == 1
    assert global_items_updated[0]["value"] == "saygı duymak"
    assert global_items_updated[0]["confidence"] == 0.95

    # 3. Add work memory items
    item_char = {
        "key": "Buck",
        "value": "Buck",
        "type": "character_info",
        "confidence": 1.0,
        "notes": "Main character dog"
    }
    manager.add_memory_item(scope="work", item=item_char, scope_id="blood_meridian")
    
    work_items = manager.get_memory_items(scope="work", scope_id="blood_meridian")
    assert len(work_items) == 1
    assert work_items[0]["key"] == "Buck"
    
    # 4. Write and read style profile
    style_md = "# Blood Meridian Style\nUse dark and poetic phrasing."
    manager.write_style_profile(work_id="blood_meridian", markdown_content=style_md)
    assert manager.read_style_profile(work_id="blood_meridian") == style_md

def test_context_router(temp_memory_dir):
    """Test context router loading and relevance filtering."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    
    # Populate memory
    manager.add_memory_item(scope="global", item={
        "key": "break down",
        "value": "bozulmak / parçalanmak",
        "type": "phrasal_verb",
        "confidence": 0.8
    })
    
    manager.add_memory_item(scope="genre", scope_id="literary", item={
        "key": "",
        "value": "prefer natural rhythm over literal translation",
        "type": "style_rule",
        "confidence": 0.9
    })
    
    manager.add_memory_item(scope="work", scope_id="call_of_wild", item={
        "key": "Judge Miller",
        "value": "Yargıç Miller",
        "type": "character_info",
        "confidence": 1.0
    })
    
    router = ContextRouter(memory_manager=manager)
    
    # Source text containing "Judge Miller" but NOT "break down"
    source_text = "Buck lived at a big house in the sun-kissed Santa Clara Valley. Judge Miller's place, it was called."
    
    relevant = router.retrieve_relevant_memory(
        source_text=source_text,
        genre="literary",
        work_id="call_of_wild",
        user_id="berkay"
    )
    
    # 'Judge Miller' and the genre style rule should be retrieved, but 'break down' should not be.
    keys = [item.get("key") for item in relevant]
    types = [item.get("type") for item in relevant]
    
    assert "Judge Miller" in keys
    assert "break down" not in keys
    assert "style_rule" in types
    
    # Generate compact context
    context = router.generate_compact_context(relevant, work_id="call_of_wild")
    assert "Yargıç Miller" in context
    assert "prefer natural rhythm" in context

def test_memory_curator_fallback(temp_memory_dir):
    """Test curator fallback rule-based extraction."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    curator = MemoryCurator(memory_manager=manager)
    
    # Test curator run with no API key, triggering fallback
    source_text = "The dog lived with Judge Miller."
    draft_translation = "Köpek Yargıç Miller ile yaşadı."
    critic_feedback = "The name 'Judge Miller' MUST be translated as 'Yargıç Miller'."
    final_translation = "Köpek Yargıç Miller ile yaşadı."
    
    # Temporarily clear API Key if any, to ensure fallback runs
    import os
    from src.core.config import Config
    old_key = Config.OPENAI_API_KEY
    Config.OPENAI_API_KEY = None
    
    try:
        extracted = curator.run_curator(
            source_text=source_text,
            draft_translation=draft_translation,
            critic_feedback=critic_feedback,
            final_translation=final_translation,
            genre="literary",
            work_id="call_of_wild",
            user_id="berkay"
        )
        
        # Check extraction matches fallback heuristic
        assert len(extracted) > 0
        
        # At least the proper noun candidate from critic feedback should be extracted
        keys = [item["key"] for item in extracted]
        assert "Judge Miller" in keys
        
        # Check if saved to work memory
        saved_items = manager.get_memory_items(scope="work", scope_id="call_of_wild")
        assert len(saved_items) > 0
        assert any(item["key"] == "Judge Miller" for item in saved_items)
        
    finally:
        Config.OPENAI_API_KEY = old_key

def test_handoff_generation(temp_memory_dir):
    """Test generating handoff files from memories."""
    manager = MemoryManager(base_dir=temp_memory_dir)
    
    # Add items to memory
    manager.add_memory_item(scope="work", scope_id="call_of_wild", item={
        "key": "Spitz",
        "value": "Spitz",
        "type": "character_info",
        "confidence": 1.0,
        "notes": "rival dog"
    })
    manager.add_memory_item(scope="global", item={
        "key": "look up to",
        "value": "saygı duymak",
        "type": "correction_pattern",
        "confidence": 0.9,
        "notes": "not literal look up"
    })
    
    handoff_gen = HandoffGenerator(memory_manager=manager)
    handoff_file = temp_memory_dir / "translation_handoff.md"
    
    handoff_gen.generate_handoff_file(
        output_path=handoff_file,
        work_id="call_of_wild",
        genre="literary",
        user_id="berkay"
    )
    
    assert handoff_file.exists()
    content = handoff_file.read_text(encoding="utf-8")
    assert "Spitz" in content
    assert "look up to" in content
    assert "Continuation Instructions" in content
