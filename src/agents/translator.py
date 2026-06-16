from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState
from src.observability.langfuse_tracker import tracker
from src.tie.strategy_planner import build_strategy_prompt_context

def translate_draft(state: TranslationState) -> dict:
    """Perform a high-fidelity strategy-guided draft translation."""
    trace_id = state.get("trace_id")
    chunk_index = state.get("chunk_index")
    span = tracker.create_span(trace_id, name="translator_node", metadata={"chunk_index": chunk_index})

    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.MINI_MODEL,
        temperature=0
    )
    
    source_text = state["source_text"]
    source_lang = state["source_language"]
    target_lang = state["target_language"]
    glossary = state["glossary"]
    positive_glossary = state.get("positive_glossary", {})
    auto_candidates = state.get("auto_glossary_candidates", {})
    negative_glossary = state.get("negative_glossary", {})
    
    # Format glossaries
    pos_glossary_text = ""
    if positive_glossary:
        pos_glossary_text = "\n### Positive Glossary (HIGHEST PRIORITY - MUST USE):\n"
        for k, v in positive_glossary.items():
            pos_glossary_text += f"- Translate '{k}' exactly as: '{v}'\n"

    auto_glossary_text = ""
    if auto_candidates:
        auto_glossary_text = "\n### Auto-Extracted Terminology Candidates (Use if appropriate):\n"
        for k, v in auto_candidates.items():
            auto_glossary_text += f"- '{k}': '{v}'\n"

    neg_glossary_text = ""
    if negative_glossary:
        neg_glossary_text = "\n### Negative Glossary (DO NOT USE):\n"
        for k, v in negative_glossary.items():
            neg_glossary_text += f"- DO NOT translate '{k}' as its standard meaning. Instead use: '{v}'\n"

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
            style_guidelines_text = f"\n### High-Priority Style & Narrative Voice Guidelines (CRITICAL):\n{style_part}\n"
    else:
        if compact_memory_context:
            tie_context = f"\n### Translation Intelligence (Previous Decisions/Terminology):\n{compact_memory_context}\n"

    strategy_context = build_strategy_prompt_context(
        state.get("translation_strategy"),
        state.get("language_profile") or state.get("target_language_profile"),
    )
    if strategy_context:
        strategy_context = f"\n{strategy_context}\n"

    prompt = f"""
You are a professional literary and technical translator. Translate the source text from {source_lang} to {target_lang} with full meaning preserved and natural target-language reconstruction.

### CRITICAL INSTRUCTIONS:
1. Preserve the full source meaning. Do not omit details, facts, images, or sentence-level implications.
2. Avoid literal English word order; reconstruct naturally in Turkish when Turkish is the target language.
3. Follow the genre, register, tone, and literalness guidance in the Translation Strategy Plan when provided.
4. Apply target language profile rules, especially pronoun economy, natural sentence rhythm, and anti-translationese guidance.
5. Adhere strictly to the Positive Glossary. It has the HIGHEST priority.
6. Adhere to the standard Glossary and Auto-Extracted Terminology.
7. Obey the Negative Glossary. DO NOT use prohibited words.
8. Use only relevant memory context already routed into this prompt.
9. If "High-Priority Style & Narrative Voice Guidelines" are provided below, you MUST respect them in this draft. Pay close attention to author sentence rhythm, narrative tone, fragment preservation, register, and any work-specific rendering rules.
{strategy_context}
{style_guidelines_text}
{tie_context}
### Standard Glossary:
{glossary}
{pos_glossary_text}
{auto_glossary_text}
{neg_glossary_text}
### Source Text:
{source_text}

Provide only the translated text, with no preamble or explanations.
"""

    
    callbacks = []
    if trace_id:
        handler = tracker.get_callback_handler(trace_id)
        if handler:
            callbacks.append(handler)
            
    response = llm.invoke(prompt, config={"callbacks": callbacks})
    raw_translation = response.content.strip()
    
    tracker.end_span(span, output_data=raw_translation)

    # Create log trace
    log_entry = {
        "agent": "Draft Translator",
        "action": "Generated raw translation draft",
        "output": raw_translation
    }
    
    return {
        "raw_translation": raw_translation,
        "logs": state.get("logs", []) + [log_entry]
    }
