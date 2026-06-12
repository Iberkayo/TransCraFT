import sys
from pathlib import Path
import pytest

# Setup path to import from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core.config import Config
from src.core.state import TranslationState
from src.core.graph import create_translation_graph

def test_config_initialization():
    """Test that default models and directories are set correctly."""
    assert isinstance(Config.MINI_MODEL, str) and len(Config.MINI_MODEL) > 0
    assert isinstance(Config.MAIN_MODEL, str) and len(Config.MAIN_MODEL) > 0
    assert Config.DATA_DIR.name == "data"
    assert Config.INPUTS_DIR.name == "inputs"
    assert Config.REFERENCE_DIR.name == "reference"

def test_graph_compilation():
    """Test that the LangGraph workflow compiles successfully."""
    graph = create_translation_graph()
    assert graph is not None
    # Verify nodes are added
    assert "analyst" in graph.nodes
    assert "translator" in graph.nodes
    assert "stylist" in graph.nodes
    assert "critic" in graph.nodes
    assert "polisher" in graph.nodes

def test_state_structure():
    """Verify TranslationState fields."""
    state_keys = TranslationState.__annotations__.keys()
    assert "source_text" in state_keys
    assert "target_language" in state_keys
    assert "style_analysis" in state_keys
    assert "final_translation" in state_keys
    assert "is_approved" in state_keys
    assert "previous_chunk_context" in state_keys
    assert "dynamic_glossary" in state_keys

def test_document_processor_smart_chunking():
    """Test smart chunking logic."""
    from src.core.document_processor import DocumentProcessor
    
    # Simple text with paragraphs
    text = "Paragraph one is short.\n\nParagraph two is also short.\n\nParagraph three is a bit longer."
    
    # Chunk with large limit (should be 1 chunk)
    chunks_large = DocumentProcessor.smart_chunk_text(text, max_chunk_size=1000)
    assert len(chunks_large) == 1
    assert chunks_large[0] == text
    
    # Chunk with small limit (should split)
    chunks_small = DocumentProcessor.smart_chunk_text(text, max_chunk_size=40)
    assert len(chunks_small) == 3
    assert chunks_small[0] == "Paragraph one is short."
    assert chunks_small[1] == "Paragraph two is also short."
    assert chunks_small[2] == "Paragraph three is a bit longer."

