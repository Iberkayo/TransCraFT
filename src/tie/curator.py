import json
import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.tie.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryItemSchema(BaseModel):
    scope: str = Field(description="Must be 'global', 'genre', 'work', or 'user'. Determine where this knowledge should reside.")
    type: str = Field(description="Must be 'phrasal_verb', 'idiom', 'terminology', 'style_rule', 'correction_pattern', or 'character_info'.")
    key: str = Field(description="The source term, pattern, character name, or preference key.")
    value: str = Field(description="The target translation, rule description, or preferred value.")
    notes: Optional[str] = Field(description="Optional notes detailing usage context, justification, or errors corrected.")
    confidence: float = Field(description="A confidence score between 0.0 and 1.0 indicating how certain the extraction is.")

class MemoryCuratorOutput(BaseModel):
    extracted_knowledge: List[MemoryItemSchema] = Field(description="List of extracted translation intelligence knowledge items.")

class MemoryCurator:
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager or MemoryManager()

    def run_curator(self, 
                    source_text: str, 
                    draft_translation: str, 
                    critic_feedback: Optional[str], 
                    final_translation: str,
                    genre: Optional[str] = None,
                    work_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    persist: bool = True) -> List[Dict[str, Any]]:
        """
        Run the curator agent to extract and save translation intelligence.
        Returns the list of extracted items.
        """
        extracted_items = []
        
        # 1. Attempt LLM-based extraction if Config API Key is configured
        if Config.OPENAI_API_KEY:
            try:
                extracted_items = self._run_llm_extraction(
                    source_text=source_text,
                    draft_translation=draft_translation,
                    critic_feedback=critic_feedback or "No feedback provided.",
                    final_translation=final_translation,
                    genre=genre,
                    work_id=work_id,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to rule-based: {e}")
                extracted_items = self._run_fallback_extraction(
                    source_text=source_text,
                    draft_translation=draft_translation,
                    critic_feedback=critic_feedback,
                    final_translation=final_translation,
                    genre=genre,
                    work_id=work_id,
                    user_id=user_id
                )
        else:
            logger.info("OPENAI_API_KEY not set, using rule-based fallback extraction.")
            extracted_items = self._run_fallback_extraction(
                source_text=source_text,
                draft_translation=draft_translation,
                critic_feedback=critic_feedback,
                final_translation=final_translation,
                genre=genre,
                work_id=work_id,
                user_id=user_id
            )

        # 2. Persist extracted items via MemoryManager if persist is True
        if persist:
            for item in extracted_items:
                scope = item.get("scope", "global")
                # Determine appropriate scope_id
                scope_id = None
                if scope == "genre":
                    scope_id = genre or "literary"
                elif scope == "work":
                    scope_id = work_id or "default_work"
                elif scope == "user":
                    scope_id = user_id or "default_user"
                    
                try:
                    self.memory_manager.add_memory_item(scope=scope, item=item, scope_id=scope_id)
                except Exception as e:
                    logger.error(f"Failed to add memory item to TIE: {e}")
                
        return extracted_items

    def _run_llm_extraction(self,
                            source_text: str,
                            draft_translation: str,
                            critic_feedback: str,
                            final_translation: str,
                            genre: Optional[str],
                            work_id: Optional[str],
                            user_id: Optional[str]) -> List[Dict[str, Any]]:
        """Run LLM with structured output to extract translation intelligence."""
        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=Config.MINI_MODEL,
            temperature=0
        )
        
        structured_llm = llm.with_structured_output(MemoryCuratorOutput, method="function_calling")
        
        prompt = f"""
You are the Memory Curator Agent for a Translation Intelligence Platform.
Your task is to analyze the translation lifecycle of a single text block and extract reusable translation knowledge.

### Inputs:
- **Source English Text**: {source_text}
- **Draft Translation**: {draft_translation}
- **Critic Feedback (What was corrected/criticized)**: {critic_feedback}
- **Final Polished Translation**: {final_translation}

### Scopes for extracted items:
- **global**: General linguistic conversions (idioms, phrasal verbs, sentence restructuring patterns, common EN->TR transformations, spelling/grammar traps).
- **genre** (active genre: '{genre or "None"}'): Stylistic preferences or translation heuristics specific to the literary or technical genre.
- **work** (active work: '{work_id or "None"}'): Character names, special terminology, style constraints, or world-building terminology specific to this book/work.
- **user** (active user: '{user_id or "None"}'): Personal styling preferences, choices, or general translation guidelines preferred by the user.

### Extracted Item Types:
- `phrasal_verb`, `idiom`, `terminology`, `style_rule`, `correction_pattern`, `character_info`.

Analyze the changes made between the Draft Translation and the Final Translation under the guidance of the Critic Feedback.
Extract any valuable rules, patterns, terminology mappings, or style decisions.
Return a structured list of these items.
"""
        response = structured_llm.invoke(prompt)
        
        # Convert Pydantic objects back to dictionaries
        items = []
        for raw_item in response.extracted_knowledge:
            items.append({
                "scope": raw_item.scope,
                "type": raw_item.type,
                "key": raw_item.key,
                "value": raw_item.value,
                "notes": raw_item.notes,
                "confidence": raw_item.confidence
            })
        return items

    def _run_fallback_extraction(self,
                                 source_text: str,
                                 draft_translation: str,
                                 critic_feedback: Optional[str],
                                 final_translation: str,
                                 genre: Optional[str],
                                 work_id: Optional[str],
                                 user_id: Optional[str]) -> List[Dict[str, Any]]:
        """Rule-based extraction fallback when LLM is unavailable."""
        items = []
        
        # 1. Simple heuristic: extract characters/glossary items based on Critic Feedback regex.
        # Often critic feedback contains things like: "Judge Miller" -> "Yargıç Miller" or "should be translated as"
        if critic_feedback:
            # Look for patterns like 'X' should be 'Y' or 'X' -> 'Y' or X should be Y or X -> Y
            matches = re.findall(r"['\"]?([^'\"]+)['\"]?\s*(?:should be|->|MUST be)\s*['\"]?([^'\"]+)['\"]?", critic_feedback, re.IGNORECASE)
            for key, val in matches:
                key = key.strip()
                val = val.strip()
                # Clean up punctuation/conjunctions
                if len(key) < 40 and len(val) < 40 and " " not in key[:2] and " " not in val[:2]:
                    # Categorize key
                    if key[0].isupper() and any(c.isupper() for c in key[1:]):
                        # Proper noun / character name candidate
                        items.append({
                            "scope": "work" if work_id else "global",
                            "type": "character_info",
                            "key": key,
                            "value": val,
                            "notes": "Extracted from critic feedback using character heuristic",
                            "confidence": 0.7
                        })
                    else:
                        items.append({
                            "scope": "work" if work_id else "global",
                            "type": "terminology",
                            "key": key,
                            "value": val,
                            "notes": "Extracted from critic feedback using terms heuristic",
                            "confidence": 0.6
                        })

        # 2. Extract potential Phrasal Verbs/Idioms or Style rules from text comparison
        # (This is just a fallback, so keeping it safe and low-risk)
        # If we have genre/user, add a generic style rule preference as a default fallback rule
        if user_id:
            items.append({
                "scope": "user",
                "type": "style_rule",
                "key": "translation_preference",
                "value": "prefer natural flowing Turkish over literal phrasing",
                "notes": "Default user preference fallback",
                "confidence": 0.5
            })
            
        if genre == "literary":
            items.append({
                "scope": "genre",
                "type": "style_rule",
                "key": "natural_flow",
                "value": "prefer natural Turkish rhythm over literal syntax structure",
                "notes": "Default literary genre fallback rule",
                "confidence": 0.5
            })

        return items
