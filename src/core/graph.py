from langgraph.graph import StateGraph, END
from src.core.state import TranslationState
from src.agents.analyst import analyze_style_and_culture
from src.agents.translator import translate_draft
from src.agents.stylist import stylize_translation
from src.agents.critic import evaluate_translation
from src.agents.polisher import polish_translation

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
    workflow.add_node("analyst", analyze_style_and_culture)
    workflow.add_node("translator", translate_draft)
    workflow.add_node("stylist", stylize_translation)
    workflow.add_node("critic", evaluate_translation)
    workflow.add_node("polisher", polish_translation)
    
    # Define execution flow
    workflow.set_entry_point("analyst")
    
    # Linear connections
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
    workflow.add_edge("polisher", END)
    
    return workflow.compile()
