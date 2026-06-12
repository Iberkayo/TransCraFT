import json
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState
from src.observability.langfuse_tracker import tracker

class ExtractedTerms(BaseModel):
    terms: dict[str, str] = Field(description="A dictionary where the key is the English/source term and the value is the suggested Turkish/target translation.")

def extract_terminology(state: TranslationState) -> dict:
    """Pre-processing agent to extract terminology from the source text."""
    trace_id = state.get("trace_id")
    chunk_index = state.get("chunk_index")
    span = tracker.create_span(trace_id, name="extractor_node", metadata={"chunk_index": chunk_index})

    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.MINI_MODEL,
        temperature=0
    )
    
    # We want structured output
    structured_llm = llm.with_structured_output(ExtractedTerms)
    
    source_text = state["source_text"]
    source_lang = state["source_language"]
    target_lang = state["target_language"]
    
    prompt = f"""
You are a professional Localization Terminology Extractor.
Your task is to analyze the following source text in {source_lang} and extract key terminology that needs consistent translation into {target_lang}.

Focus on:
1. Technical terms or domain-specific vocabulary
2. Acronyms and abbreviations
3. Proper nouns (organizations, products, characters) if they require specific localization

Return a dictionary where keys are the source terms and values are your proposed translations in {target_lang}.

### Source Text:
{source_text}
"""
    
    callbacks = []
    if trace_id:
        handler = tracker.get_callback_handler(trace_id)
        if handler:
            callbacks.append(handler)
            
    try:
        response = structured_llm.invoke(prompt, config={"callbacks": callbacks})
        extracted_dict = response.terms
    except Exception as e:
        # Fallback to normalized rule-based extraction
        from src.core.utils import extract_fallback_terms
        
        final_candidates = extract_fallback_terms(source_text)
        
        extracted_dict = {}
        for term in final_candidates:
            extracted_dict[term] = "TBD"
                
        # If we found terms, quickly use normal LLM to translate them
        if extracted_dict:
            try:
                fallback_prompt = f"Translate these terms to {target_lang}. Return ONLY a valid JSON object {{'term': 'translation'}}:\n" + str(list(extracted_dict.keys()))
                fallback_response = llm.invoke(fallback_prompt).content
                import json
                cleaned = fallback_response.replace("```json", "").replace("```", "").strip()
                extracted_dict = json.loads(cleaned)
            except:
                pass

    tracker.end_span(span, output_data=str(extracted_dict))

    # Append to auto_glossary_candidates state, and optionally save to disk
    existing_candidates = state.get("auto_glossary_candidates", {})
    if existing_candidates is None:
        existing_candidates = {}
        
    existing_candidates.update(extracted_dict)

    # Save to data/runtime/auto_glossary_candidate.json
    runtime_dir = Config.DATA_DIR / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = runtime_dir / "auto_glossary_candidate.json"
    
    # Merge with existing file if it exists
    if candidate_path.exists():
        try:
            with open(candidate_path, "r", encoding="utf-8") as f:
                disk_candidates = json.load(f)
        except:
            disk_candidates = {}
    else:
        disk_candidates = {}
        
    disk_candidates.update(extracted_dict)
    
    with open(candidate_path, "w", encoding="utf-8") as f:
        json.dump(disk_candidates, f, ensure_ascii=False, indent=2)

    log_entry = {
        "agent": "Terminology Extractor",
        "action": "Extracted key terminology candidates",
        "output": json.dumps(extracted_dict, ensure_ascii=False, indent=2) if extracted_dict else "No terms extracted."
    }

    return {
        "auto_glossary_candidates": existing_candidates,
        "logs": state.get("logs", []) + [log_entry]
    }
