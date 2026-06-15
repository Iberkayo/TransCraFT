import pytest
import os
import shutil
from pathlib import Path
from src.tie.memory_manager import MemoryManager
from src.tie.style_profiler import AuthorStyleProfiler
from src.tie.style_contract import StyleContractGenerator
from src.tie.router import ContextRouter

@pytest.fixture
def temp_memory_dir(tmp_path):
    # Setup test memory structure
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_known_author_profile_loading(temp_memory_dir):
    authors_dir = temp_memory_dir / "global" / "authors"
    authors_dir.mkdir(parents=True)
    
    # Write a mock known author profile
    mock_profile = {
        "author_id": "cormac_mccarthy",
        "author_name": "Cormac McCarthy",
        "type": "author_style",
        "attributes": {
            "tone": "bleak, severe",
            "sentence_rhythm": "biblical, paratactic"
        },
        "inferred": False,
        "confidence": 1.0,
        "usage_count": 1
    }
    with open(authors_dir / "cormac_mccarthy.json", "w", encoding="utf-8") as f:
        import json
        json.dump(mock_profile, f)
        
    profiler = AuthorStyleProfiler(base_dir=temp_memory_dir)
    profile = profiler.load_or_infer_profile("cormac_mccarthy")
    
    assert profile["author_id"] == "cormac_mccarthy"
    assert profile["attributes"]["tone"] == "bleak, severe"
    assert profile["usage_count"] == 2  # Incremented usage

def test_unknown_author_profile_generation(temp_memory_dir):
    profiler = AuthorStyleProfiler(base_dir=temp_memory_dir)
    # Since we won't run full LLM inference in tests without API key, test the fallback
    profile = profiler.load_or_infer_profile("unknown_novelist", sample_chunks=[])
    
    assert profile["author_id"] == "unknown_novelist"
    assert profile["inferred"] is True
    assert "tone" in profile["attributes"]

def test_style_contract_generation(temp_memory_dir):
    contract_gen = StyleContractGenerator(base_dir=temp_memory_dir)
    author_profile = {
        "author_id": "cormac_mccarthy",
        "author_name": "Cormac McCarthy",
        "attributes": {
            "tone": "bleak",
            "sentence_rhythm": "fragmentary"
        }
    }
    
    contract = contract_gen.load_or_generate_contract("blood_meridian", author_profile)
    
    assert contract["tone"] != ""
    assert len(contract["rules"]) > 0
    assert any("See the child" in r or "Imperatives" in r or "presentation" in r for r in contract["rules"])
    
    # Verify contract was saved to disk
    contract_path = temp_memory_dir / "works" / "blood_meridian" / "style" / "style_contract.json"
    assert contract_path.exists()

def test_router_includes_style_context(temp_memory_dir):
    # Setup mock author profile and contract
    authors_dir = temp_memory_dir / "global" / "authors"
    authors_dir.mkdir(parents=True, exist_ok=True)
    
    mock_profile = {
        "author_id": "cormac_mccarthy",
        "author_name": "Cormac McCarthy",
        "type": "author_style",
        "attributes": {"tone": "bleak", "sentence_rhythm": "fragmentary"}
    }
    with open(authors_dir / "cormac_mccarthy.json", "w", encoding="utf-8") as f:
        import json
        json.dump(mock_profile, f)
        
    manager = MemoryManager(base_dir=temp_memory_dir)
    router = ContextRouter(memory_manager=manager)
    
    # Perform retrieval for blood_meridian
    relevant = router.retrieve_relevant_memory(
        source_text="See the child. He is pale and thin.",
        work_id="blood_meridian"
    )
    
    compact = router.generate_compact_context(relevant, work_id="blood_meridian")
    
    assert "### Style & Narrative Voice Guidelines" in compact
    assert "Tone" in compact
    assert "Sentence Rhythm" in compact
