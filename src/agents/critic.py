from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState

class EvaluationSchema(BaseModel):
    is_approved: bool = Field(
        description="True if the translation is beautiful, accurate, and ready for publication. False if it needs revisions."
    )
    critique: str = Field(
        description="Constructive critique in Turkish pointing out specific issues (e.g., mistranslations, awkward wording, idiom misuse). If approved, this should be 'None'."
    )

def evaluate_translation(state: TranslationState) -> dict:
    """Compare source text and stylized translation to evaluate accuracy and flow."""
    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=Config.MAIN_MODEL,  # Use main model for critical evaluation
        temperature=0
    )
    
    source_text = state["source_text"]
    stylized_translation = state["stylized_translation"]
    style_guide = state["style_guide"]
    revision_count = state.get("revision_count", 0)
    
    prompt = f"""
You are an expert bilingual critic and translation quality auditor. Your task is to compare the source text and the stylized translation, ensuring that the translation is beautiful and accurate.

### Source Text:
{source_text}

### Stylized Translation:
{stylized_translation}

### Style Guide Rules:
{style_guide}

### Instructions:
1. Check for **Accuracy**: Did the stylist omit any sentences or alter facts?
2. Check for **Flow & Naturalness**: Does the Turkish version read naturally, or are there clunky phrasing issues?
3. Check for **Idioms**: Were the idioms adapted appropriately, or did they get translated literally?
4. **Approval Logic**: If there are noticeable flow issues or errors, set `is_approved` to False and write a detailed constructive critique. If it is already high quality and ready to publish, set `is_approved` to True.

*Note: If this is Revision #{Config.MAX_REVISIONS}, be slightly more lenient to prevent infinite loops, and only reject if there are severe factual errors.*
"""

    structured_llm = llm.with_structured_output(EvaluationSchema)
    result = structured_llm.invoke(prompt)
    
    # Check if we hit the revision limit - if so, override approval to true to avoid loop
    is_approved = result.is_approved
    critique = result.critique
    
    if revision_count >= Config.MAX_REVISIONS:
        is_approved = True
        critique = f"Max revisions reached. Overriding approval. Original critique was: {critique}"
        
    # Create log trace
    log_entry = {
        "agent": "Translation Critic",
        "action": f"Evaluated translation (Approved: {is_approved})",
        "output": f"Approved: {is_approved}\nCritique: {critique}"
    }
    
    return {
        "is_approved": is_approved,
        "critique": critique,
        "revision_count": revision_count + 1,  # Increment revision count
        "logs": state.get("logs", []) + [log_entry]
    }
