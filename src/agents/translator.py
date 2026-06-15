from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState
from src.observability.langfuse_tracker import tracker

def translate_draft(state: TranslationState) -> dict:
    """Perform a high-fidelity literal and semantic draft translation."""
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
    tie_context = f"\n### Translation Intelligence (Previous Decisions/Rules):\n{compact_memory_context}\n" if compact_memory_context else ""

    prompt = f"""
You are a high-fidelity semantic translator. Your goal is to translate the source text from {source_lang} to {target_lang} with maximum accuracy, ensuring no meaning, detail, or nuances are lost.

### Rules:
1. Translate accurately. Do not try to make it highly poetic or loose yet; focus on accuracy.
2. Adhere strictly to the Positive Glossary. It has the HIGHEST priority.
3. Adhere to the standard Glossary and Auto-Extracted Terminology.
4. Obey the Negative Glossary. DO NOT use prohibited words.
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
