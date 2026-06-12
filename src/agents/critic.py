from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState
from src.observability.langfuse_tracker import tracker

class EvaluationSchema(BaseModel):
    is_approved: bool = Field(
        description="True if the translation is beautiful, accurate, and ready for publication. False if it needs revisions."
    )
    critique: str = Field(
        description="Constructive critique in Turkish pointing out specific issues (e.g., mistranslations, awkward wording, idiom misuse). If approved, this should be 'None'."
    )

def evaluate_translation(state: TranslationState) -> dict:
    """Compare source text and stylized translation to evaluate accuracy and flow."""
    trace_id = state.get("trace_id")
    chunk_index = state.get("chunk_index")
    span = tracker.create_span(trace_id, name="critic_node", metadata={"chunk_index": chunk_index, "revision_count": state.get("revision_count", 0)})

    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.MAIN_MODEL,  # Use main model for critical evaluation
        temperature=0
    )
    
    source_text = state["source_text"]
    stylized_translation = state["stylized_translation"]
    style_guide = state["style_guide"]
    positive_glossary = state.get("positive_glossary", {})
    auto_candidates = state.get("auto_glossary_candidates", {})
    negative_glossary = state.get("negative_glossary", {})
    revision_count = state.get("revision_count", 0)

    pos_glossary_text = ""
    if positive_glossary:
        pos_glossary_text = "\n### Positive Glossary (MUST USE):\n"
        for k, v in positive_glossary.items():
            pos_glossary_text += f"- '{k}' MUST be '{v}'\n"
    
    prompt = f"""
You are an expert bilingual critic. Your task is to evaluate the stylized translation against the source text.
You are extremely strict. If there are factual errors, omitted sentences, or major style guide violations, you must reject it.

### Strict Validation Rules:
1. Verify that all terms in the Positive Glossary were used exactly. If any are missing or translated differently, REJECT.
2. Verify that NO terms from the Negative Glossary were used. If any are present, REJECT.
3. Check Auto-Extracted Terminology Candidates (optional, but good to have).

### Positive Glossary:
{pos_glossary_text}

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

    structured_llm = llm.with_structured_output(EvaluationSchema, method="function_calling")
    
    callbacks = []
    if trace_id:
        handler = tracker.get_callback_handler(trace_id)
        if handler:
            callbacks.append(handler)

    result = structured_llm.invoke(prompt, config={"callbacks": callbacks})
    
    # Check if we hit the revision limit - if so, override approval to true to avoid loop
    is_approved = result.is_approved
    critique = result.critique
    
    if revision_count >= Config.MAX_REVISIONS:
        is_approved = True
        critique = f"Max revisions reached. Overriding approval. Original critique was: {critique}"
        
    tracker.end_span(span, output_data={"is_approved": is_approved, "critique": critique})

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
