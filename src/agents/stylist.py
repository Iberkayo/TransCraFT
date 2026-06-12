from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState
from src.observability.langfuse_tracker import tracker

def stylize_translation(state: TranslationState) -> dict:
    """Refine the raw translation to be culturally fluent, natural, and literary."""
    trace_id = state.get("trace_id")
    chunk_index = state.get("chunk_index")
    span = tracker.create_span(trace_id, name="stylist_node", metadata={"chunk_index": chunk_index, "revision_count": state.get("revision_count", 0)})

    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.MAIN_MODEL,  # Use main model (gpt-4o) for high-quality writing
        temperature=0.3
    )
    
    source_text = state["source_text"]
    raw_translation = state["raw_translation"]
    style_analysis = state["style_analysis"]
    style_guide = state["style_guide"]
    critique = state.get("critique")
    revision_count = state.get("revision_count", 0)
    
    # Stateful translation support
    prev_context = state.get("previous_chunk_context", "None (This is the first chunk)")
    dyn_glossary = state.get("dynamic_glossary", [])
    
    # Construct base prompt
    prompt = f"""
You are a master literary editor and stylist. Your goal is to rewrite the raw draft translation to make it sound completely natural, beautiful, and authentic in the target language. It must read like it was originally written by a talented native writer in that language, while preserving all the original meanings and characters.

### Source Text (For Reference):
{source_text}

### Narrative Context from Previous Chunk (For Continuity):
{prev_context}

### Dynamic Glossary of Terms (Must adhere to):
{dyn_glossary}

### Raw Draft Translation:
{raw_translation}

### Style & Culture Analysis Report:
{style_analysis}

### Style Guide Rules:
{style_guide}
"""

    # Add critique if we are in a revision loop
    if critique and revision_count > 0:
        prompt += f"""
### Feedback from the Critic Agent (MUST ADDRESS):
{critique}

Please rewrite the translation carefully, incorporating the Critic's feedback point-by-point.
"""
    
    prompt += """
Provide only the refined, beautiful translation in the target language, with no conversational preamble or notes.
"""

    callbacks = []
    if trace_id:
        handler = tracker.get_callback_handler(trace_id)
        if handler:
            callbacks.append(handler)

    response = llm.invoke(prompt, config={"callbacks": callbacks})
    stylized_translation = response.content.strip()
    
    tracker.end_span(span, output_data=stylized_translation)

    # Create log trace
    log_entry = {
        "agent": "Cultural Stylist",
        "action": f"Stylized translation (Revision {revision_count})",
        "output": stylized_translation
    }
    
    return {
        "stylized_translation": stylized_translation,
        "logs": state.get("logs", []) + [log_entry]
    }
