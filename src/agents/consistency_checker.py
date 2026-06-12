import json
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from src.core.config import Config

class ConsistencyIssue(BaseModel):
    type: str = Field(description="Type of issue (e.g., Terminology, Formatting, Tone Shift, Untranslated)")
    description: str = Field(description="Description of the inconsistency")
    location: str = Field(description="Approximate location or quote from the text")
    recommendation: str = Field(description="Suggested correction")

class GlossaryRecommendation(BaseModel):
    source_term: str
    target_term: str
    reason: str

class ConsistencyReport(BaseModel):
    issues_found: int = Field(description="Total number of issues found")
    issues: List[ConsistencyIssue]
    glossary_candidates: List[GlossaryRecommendation] = Field(description="Recommended terminology to add to auto_glossary_candidate.json based on this document.")

def run_consistency_check(full_source: str, full_translation: str, positive_glossary: dict) -> dict:
    """Post-processing agent to audit the full document."""
    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.MINI_MODEL,
        temperature=0
    )
    
    structured_llm = llm.with_structured_output(ConsistencyReport)
    
    pos_glossary_text = ""
    if positive_glossary:
        pos_glossary_text = "\n### Positive Glossary (MUST USE):\n"
        for k, v in positive_glossary.items():
            pos_glossary_text += f"- '{k}' MUST be '{v}'\n"
            
    prompt = f"""
You are an Enterprise Localization Consistency Checker.
Your task is to audit the entirely translated document against the source document.

Check for:
1. Terminology consistency (especially ensuring the Positive Glossary was respected).
2. Character/Product name consistency.
3. Tone shifts or style inconsistencies.
4. Untranslated fragments (e.g., English text left in Turkish output).
5. Formatting consistency (quotation marks, spacing, headers).

Additionally, extract a list of highly repeated or important terms that should be added to the terminology glossary for future runs.

{pos_glossary_text}

### Source Document:
{full_source}

### Translated Document:
{full_translation}
"""

    try:
        report = structured_llm.invoke(prompt)
        return report.dict()
    except Exception as e:
        # Fallback to normalized rule-based terminology extraction
        from src.core.utils import extract_fallback_terms
        
        final_candidates = extract_fallback_terms(full_source)
        
        glossary_candidates = []
        for term in final_candidates:
            glossary_candidates.append({
                "source_term": term,
                "target_term": "TBD (Extracted via Fallback)",
                "reason": f"Repeated technical term."
            })
                
        if glossary_candidates:
            # Attempt to translate these candidates using standard LLM (without structured output)
            terms_to_translate = [c["source_term"] for c in glossary_candidates]
            fallback_prompt = f"Given the Turkish translation provided earlier, find the Turkish translations used for the following English terms: {terms_to_translate}. Return ONLY a valid JSON dictionary mapping English term to Turkish term."
            try:
                fallback_response = llm.invoke(fallback_prompt).content
                import json
                cleaned = fallback_response.replace("```json", "").replace("```", "").strip()
                translations = json.loads(cleaned)
                for cand in glossary_candidates:
                    if cand["source_term"] in translations:
                        cand["target_term"] = translations[cand["source_term"]]
            except:
                pass
                
        return {
            "issues_found": 0, 
            "issues": [], 
            "glossary_candidates": glossary_candidates, 
            "error": "Structured output failed, utilized fallback extraction."
        }
