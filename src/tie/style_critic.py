import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.observability.langfuse_tracker import tracker

logger = logging.getLogger(__name__)

class StyleEvaluationSchema(BaseModel):
    style_preservation: int = Field(description="Score from 0 to 5 on how well the author's overall style was preserved.")
    rhythm_preservation: int = Field(description="Score from 0 to 5 on sentence fragments, coordinate clauses, and rhythm pacing.")
    voice_consistency: int = Field(description="Score from 0 to 5 on keeping the narrator voice consistent with author profile.")
    literary_force: int = Field(description="Score from 0 to 5 on atmospheric/literary weight of the translation.")
    issues: List[str] = Field(description="List of specific stylistic issues (e.g. explanatory words, suffix over-use).")
    suggestions: List[str] = Field(description="Actionable stylistic suggestions to improve the translation.")

class StyleConsistencyCritic:
    def evaluate(self, 
                 source_text: str, 
                 translated_text: str, 
                 author_style_profile: Dict[str, Any], 
                 style_contract: Dict[str, Any], 
                 trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate the style consistency of the translation against the style contract
        using a structured LLM call.
        """
        if not Config.OPENAI_API_KEY:
            return {
                "style_preservation": 5,
                "rhythm_preservation": 5,
                "voice_consistency": 5,
                "literary_force": 5,
                "issues": [],
                "suggestions": []
            }
            
        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=Config.MAIN_MODEL,
            temperature=0
        )
        
        prompt = f"""
You are an expert bilingual literary critic and editor.
Your task is to evaluate the style consistency of the translated text against the author's style profile and the style contract.

### Source Text:
{source_text}

### Translated Text:
{translated_text}

### Author Style Profile:
- Tone: {author_style_profile.get('attributes', {}).get('tone')}
- Rhythm: {author_style_profile.get('attributes', {}).get('sentence_rhythm')}
- Register: {author_style_profile.get('attributes', {}).get('language_register')}
- Punctuation/Dialogue: {author_style_profile.get('attributes', {}).get('dialogue_density')}

### Style Contract Rules:
{style_contract.get('rules', [])}

### Evaluation Areas:
1. **Fragment Preservation:** Check if the translator preserved sentence fragments, coordinate clauses, and short narrative pulses. Penalize unnecessary explanatory Turkish (like adding relative clauses or declarative '-dir' suffixes).
2. **Narrative Voice:** Check if the detached/observational narrative voice is preserved consistently with the author profile.
3. **Register Consistency:** Penalize overly modern or contemporary slang when the profile requests archaic/solemn register.
4. **Literary Force:** Evaluate imagery retention and atmospheric/emotional weight (e.g. word choices like 'karanlık sürülmüş' vs 'kara sürülmüş').

Rate each area from 0 to 5 (inclusive). Provide concrete issues and suggestions for revisions.
"""
        try:
            structured_llm = llm.with_structured_output(StyleEvaluationSchema, method="function_calling")
            callbacks = []
            if trace_id:
                handler = tracker.get_callback_handler(trace_id)
                if handler:
                    callbacks.append(handler)
            result = structured_llm.invoke(prompt, config={"callbacks": callbacks})
            return result.model_dump()
        except Exception as e:
            logger.error(f"Failed to run StyleConsistencyCritic: {e}")
            return {
                "style_preservation": 3,
                "rhythm_preservation": 3,
                "voice_consistency": 3,
                "literary_force": 3,
                "issues": [f"Critic execution failed: {e}"],
                "suggestions": ["Verify translation manual style alignment."]
            }
