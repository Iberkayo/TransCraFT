from langgraph.graph import StateGraph, END
from src.core.state import TranslationState
from src.agents.analyst import analyze_style_and_culture
from src.agents.translator import translate_draft
from src.agents.stylist import stylize_translation
from src.agents.critic import evaluate_translation
from src.agents.polisher import polish_translation

from src.agents.extractor import extract_terminology

def run_context_router(state: TranslationState) -> dict:
    """Determine and retrieve relevant memories based on genre, work_id, user_id."""
    if not state.get("enable_tie", False):
        return {
            "compact_memory_context": "",
            "relevant_memories": []
        }
    
    from src.tie.router import ContextRouter
    from src.tie.memory_manager import MemoryManager
    from src.core.config import Config
    
    manager = MemoryManager(base_dir=Config.MEMORY_DIR)
    router = ContextRouter(memory_manager=manager)
    
    source_text = state.get("source_text", "")
    genre = state.get("genre", "literary")
    work_id = state.get("work_id")
    user_id = state.get("user_id")
    
    relevant = router.retrieve_relevant_memory(
        source_text=source_text,
        genre=genre,
        work_id=work_id,
        user_id=user_id
    )
    compact = router.generate_compact_context(relevant, work_id=work_id)
    
    log_entry = {
        "agent": "Context Router",
        "action": "Retrieved relevant translation memories",
        "output": f"Loaded {len(relevant)} memory item(s). Compact Context:\n{compact}" if relevant else "No relevant memories found."
    }
    
    return {
        "relevant_memories": relevant,
        "compact_memory_context": compact,
        "logs": state.get("logs", []) + [log_entry]
    }

def run_memory_curator(state: TranslationState) -> dict:
    """Extract and persist new translation decisions, terminology, and patterns."""
    if not state.get("enable_tie", False):
        return {}
        
    from src.tie.curator import MemoryCurator
    from src.tie.memory_manager import MemoryManager
    from src.core.config import Config
    
    manager = MemoryManager(base_dir=Config.MEMORY_DIR)
    curator = MemoryCurator(memory_manager=manager)
    
    source_text = state.get("source_text", "")
    draft_translation = state.get("raw_translation", "")
    critic_feedback = state.get("critique", "")
    final_translation = state.get("final_translation", "")
    
    # Try to resolve final translation if empty
    if not final_translation:
        for log in state.get("logs", []):
            if log.get("agent") == "Final Polisher":
                final_translation = log.get("output", "")
                
    genre = state.get("genre", "literary")
    work_id = state.get("work_id")
    user_id = state.get("user_id")
    
    extracted = curator.run_curator(
        source_text=source_text,
        draft_translation=draft_translation,
        critic_feedback=critic_feedback,
        final_translation=final_translation,
        genre=genre,
        work_id=work_id,
        user_id=user_id
    )
    
    log_entry = {
        "agent": "Memory Curator",
        "action": "Extracted and curated translation intelligence items",
        "output": f"Extracted {len(extracted)} item(s) and persisted to scopes." if extracted else "No new translation decisions met the criteria for curation."
    }
    
    return {
        "logs": state.get("logs", []) + [log_entry]
    }

def route_after_critic(state: TranslationState) -> str:
    """Determine whether to route to the polisher or loop back to the stylist."""
    if state.get("is_approved", False):
        return "polisher"
    else:
        return "stylist"

def create_translation_graph() -> StateGraph:
    """Create and compile the LangGraph workflow for cultural translation."""
    # Initialize the graph with our state definition
    workflow = StateGraph(TranslationState)
    
    # Add nodes (agents)
    workflow.add_node("router", run_context_router)
    workflow.add_node("extractor", extract_terminology)
    workflow.add_node("analyst", analyze_style_and_culture)
    workflow.add_node("translator", translate_draft)
    workflow.add_node("stylist", stylize_translation)
    workflow.add_node("critic", evaluate_translation)
    workflow.add_node("polisher", polish_translation)
    workflow.add_node("curator", run_memory_curator)
    
    # Define execution flow
    workflow.set_entry_point("router")
    
    # Connection mapping
    workflow.add_edge("router", "extractor")
    workflow.add_edge("extractor", "analyst")
    workflow.add_edge("analyst", "translator")
    workflow.add_edge("translator", "stylist")
    workflow.add_edge("stylist", "critic")
    
    # Conditional routing after evaluation
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "polisher": "polisher",
            "stylist": "stylist"
        }
    )
    
    # Final node connections
    workflow.add_edge("polisher", "curator")
    workflow.add_edge("curator", END)
    
    return workflow.compile()
