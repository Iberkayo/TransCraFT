from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState

def translate_draft(state: TranslationState) -> dict:
    """Perform a high-fidelity literal and semantic draft translation."""
    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=Config.MINI_MODEL,
        temperature=0
    )
    
    source_text = state["source_text"]
    source_lang = state["source_language"]
    target_lang = state["target_language"]
    glossary = state["glossary"]
    
    prompt = f"""
You are a high-fidelity semantic translator. Your goal is to translate the source text from {source_lang} to {target_lang} with maximum accuracy, ensuring no meaning, detail, or nuances are lost.

### Rules:
1. Translate accurately. Do not try to make it highly poetic or loose yet; focus on accuracy.
2. Adhere strictly to the Glossary below. If a term is in the glossary, you MUST use the specified translation.

### Glossary:
{glossary}

### Source Text:
{source_text}

Provide only the translated text, with no preamble or explanations.
"""
    
    response = llm.invoke(prompt)
    raw_translation = response.content.strip()
    
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
