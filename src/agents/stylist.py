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
    negative_glossary = state.get("negative_glossary", {})
    positive_glossary = state.get("positive_glossary", {})
    auto_candidates = state.get("auto_glossary_candidates", {})
    
    # Format glossaries
    pos_glossary_text = ""
    if positive_glossary:
        pos_glossary_text = "\n### Positive Glossary (HIGHEST PRIORITY - MUST PRESERVE):\n"
        for k, v in positive_glossary.items():
            pos_glossary_text += f"- '{k}' MUST remain '{v}'\n"

    auto_glossary_text = ""
    if auto_candidates:
        auto_glossary_text = "\n### Auto-Extracted Terminology Candidates:\n"
        for k, v in auto_candidates.items():
            auto_glossary_text += f"- '{k}': '{v}'\n"

    neg_glossary_text = ""
    if negative_glossary:
        neg_glossary_text = "\n### Negative Glossary (DO NOT USE):\n"
        for k, v in negative_glossary.items():
            neg_glossary_text += f"- Avoid translating '{k}' as its standard meaning. DO NOT use prohibited translations. Instead use: '{v}'\n"
    
    compact_memory_context = state.get("compact_memory_context", "")
    
    # Separate terminology context from style contract context for clearer structured prompts
    tie_context = ""
    style_guidelines_text = ""
    
    if "### Style & Narrative Voice Guidelines" in compact_memory_context:
        parts = compact_memory_context.split("### Style & Narrative Voice Guidelines")
        term_part = parts[0].strip()
        style_part = parts[1].strip()
        
        if term_part:
            tie_context = f"\n### Translation Intelligence (Previous Decisions/Terminology):\n{term_part}\n"
        if style_part:
            style_guidelines_text = f"\n### CRITICAL STYLE CONTRACT & VOICE DIRECTIVES (MAXIMUM PRIORITY):\n{style_part}\n"
    else:
        if compact_memory_context:
            tie_context = f"\n### Translation Intelligence (Previous Decisions/Terminology):\n{compact_memory_context}\n"

    # Construct base prompt
    prompt = f"""
You are a master literary editor and stylist. Your goal is to rewrite the raw draft translation to make it sound completely natural, beautiful, and authentic in the target language. It must read like it was originally written by a talented native writer in that language, while preserving all the original meanings and characters.

### CRITICAL STYLE ENFORCEMENT RULES:
1. You MUST strongly prioritize style, narrative tone preservation, voice consistency, and sentence rhythm adaptation.
2. If the style directives specify preserving sentence fragments, coordinate clauses, or bleak atmospheric rhythm, you MUST enforce this in the Turkish text. DO NOT combine stark fragments or split sentences unless explicitly allowed.
3. Pay close attention to any work-specific scenic, rhetorical, register, or punctuation directives supplied in the style contract.
4. Do not insert modern Turkish conversational filler words or explanatory conjunctions (like 'çünkü', 'fakat', 'ise') to bridge coordinate paratactic clauses if the style contract forbids them.
{style_guidelines_text}

### Source Text (For Reference):
{source_text}

### Narrative Context from Previous Chunk (For Continuity):
{prev_context}
{tie_context}
### Glossaries and Terminology (Must adhere to):
{dyn_glossary}
{pos_glossary_text}
{auto_glossary_text}
{neg_glossary_text}

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
