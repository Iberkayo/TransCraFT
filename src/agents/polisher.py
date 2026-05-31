from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState

def polish_translation(state: TranslationState) -> dict:
    """Perform a final proofreading and editorial polish on the stylized translation."""
    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=Config.MINI_MODEL,
        temperature=0.1
    )
    
    stylized_translation = state["stylized_translation"]
    
    prompt = f"""
You are a professional copyeditor and proofreader. Your task is to perform a final editorial polish on the translation below.

### Translation to Polish:
{stylized_translation}

### Instructions:
1. Correct any spelling, punctuation, or grammar mistakes in Turkish.
2. Ensure the formatting (paragraphs, quotes, indentations) is clean and consistent.
3. Do not make large rewrites; respect the stylized translation's vocabulary and syntax unless it is incorrect.

Provide only the polished, final translated text. Do not include any notes, explanations, or introduction.
"""

    response = llm.invoke(prompt)
    final_translation = response.content.strip()
    
    # Create log trace
    log_entry = {
        "agent": "Final Polisher",
        "action": "Completed final proofreading and polish",
        "output": final_translation
    }
    
    return {
        "final_translation": final_translation,
        "logs": state.get("logs", []) + [log_entry]
    }
