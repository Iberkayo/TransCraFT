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
    
    is_approved = result.is_approved
    critique = result.critique
    
    # Check if we hit the revision limit - if so, override approval to true to avoid loop
    if revision_count >= Config.MAX_REVISIONS:
        is_approved = True
        critique = f"Max revisions reached. Overriding approval. Original critique was: {critique}"
        
    # TIE v0.3.1 Style Consistency Critic integration
    style_evaluation = {}
    style_revision_count = state.get("style_revision_count", 0)
    
    if state.get("enable_tie", False) and state.get("work_id"):
        try:
            from src.tie.style_profiler import AuthorStyleProfiler
            from src.tie.style_contract import StyleContractGenerator
            from src.tie.style_critic import StyleConsistencyCritic
            
            # Resolve author ID
            work_id = state.get("work_id")
            mapping = {
                "blood_meridian": "cormac_mccarthy",
                "alice_in_wonderland": "lewis_carroll",
                "attention_is_all_you_need": "vaswani_et_al"
            }
            work_key = work_id.lower().strip().replace(" ", "_")
            author_id = mapping.get(work_key, f"author_{work_key}")
            author_name = author_id.replace("_", " ").title()
            
            profiler = AuthorStyleProfiler(base_dir=Config.MEMORY_DIR)
            contract_gen = StyleContractGenerator(base_dir=Config.MEMORY_DIR)
            critic_instance = StyleConsistencyCritic()
            
            # Load or infer profile & contract
            profile = profiler.load_or_infer_profile(author_id, author_name)
            contract = contract_gen.load_or_generate_contract(work_key, profile)
            
            style_evaluation = critic_instance.evaluate(
                source_text=source_text,
                translated_text=stylized_translation,
                author_style_profile=profile,
                style_contract=contract,
                trace_id=trace_id
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to run StyleConsistencyCritic in evaluate_translation: {e}")
            
    # Integrate Style consistency score decisions
    style_log_str = ""
    if style_evaluation:
        style_pres = style_evaluation.get("style_preservation", 5)
        voice_cons = style_evaluation.get("voice_consistency", 5)
        
        style_log_str = f"\n[Style Critic Evaluation]\n" \
                        f"- Style Preservation: {style_pres}/5\n" \
                        f"- Rhythm Preservation: {style_evaluation.get('rhythm_preservation', 5)}/5\n" \
                        f"- Voice Consistency: {voice_cons}/5\n" \
                        f"- Literary Force: {style_evaluation.get('literary_force', 5)}/5\n"
                        
        if style_evaluation.get("issues"):
            style_log_str += "Issues:\n" + "\n".join(f"  - {issue}" for issue in style_evaluation["issues"]) + "\n"
        if style_evaluation.get("suggestions"):
            style_log_str += "Suggestions:\n" + "\n".join(f"  - {sug}" for sug in style_evaluation["suggestions"]) + "\n"
            
        # Trigger style feedback loop if threshold is violated (score < 3)
        # Maximum: 1 extra style revision
        if (style_pres < 3 or voice_cons < 3) and style_revision_count < 1:
            is_approved = False
            style_revision_count += 1
            critique = (critique or "") + "\n\n### Stylistic Criticism (Style Contract Non-Compliance):\n" + \
                       "\n".join(f"- {sug}" for sug in style_evaluation.get("suggestions", []))
            style_log_str += f"-> [REJECTED FOR STYLE] Triggers style revision loop. (Revision count: {style_revision_count})\n"
        else:
            style_log_str += f"-> [APPROVED / BYPASS] Style checks accepted or max style revision count reached.\n"
            
    tracker.end_span(span, output_data={"is_approved": is_approved, "critique": critique})

    # Create log trace
    log_entry = {
        "agent": "Translation Critic",
        "action": f"Evaluated translation (Approved: {is_approved})",
        "output": f"Approved: {is_approved}\nCritique: {critique}\n{style_log_str}"
    }
    
    return {
        "is_approved": is_approved,
        "critique": critique,
        "revision_count": revision_count + 1,  # Increment accuracy revision count
        "style_revision_count": style_revision_count,  # Update style revision count
        "logs": state.get("logs", []) + [log_entry]
    }

