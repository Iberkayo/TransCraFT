import os
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.observability.langfuse_tracker import tracker

logger = logging.getLogger(__name__)

class ReviewResultSchema(BaseModel):
    relevance_score: float = Field(description="Score from 0.0 to 1.0 on how relevant this item is to translation.")
    generality_score: float = Field(description="Score from 0.0 to 1.0 on how generally applicable this is.")
    scope_correctness_score: float = Field(description="Score from 0.0 to 1.0 on whether the curator assigned the correct scope.")
    duplication_score: float = Field(description="Score from 0.0 to 1.0 on if this represents a redundant/low-value copy of a standard rule.")
    contradiction_risk: float = Field(description="Score from 0.0 to 1.0 on whether this contradicts common target language rules.")
    suggested_scope: str = Field(description="The validated scope: 'global', 'genre', 'work', or 'user'.")
    importance_score: float = Field(description="Overall importance score from 0.0 to 1.0.")
    final_decision: str = Field(description="Decision: 'accept', 'reject', or 'pending'.")
    justification: str = Field(description="Brief explanation for the decision.")

class MemoryReviewer:
    def __init__(self):
        # Read reviewer LLM flag from Config or env
        self.enable_llm_reviewer = getattr(Config, "ENABLE_TIE_REVIEWER_LLM", False)

    def prefilter_candidate(self, 
                            item: Dict[str, Any], 
                            work_id: str = "", 
                            genre: str = "") -> Tuple[str, str]:
        """
        Apply rule-based prefiltering to immediately reject or classify known noise.
        Returns a tuple of (final_decision, justification).
        If decision is 'evaluate', it means the item should proceed to LLM/heuristic evaluation.
        """
        key = str(item.get("key", "")).strip()
        val = str(item.get("value", "")).strip()
        itype = str(item.get("type", "")).strip()
        scope = str(item.get("scope", "")).strip()
        notes = str(item.get("notes", "")).strip()
        
        combined_text = f"{key} {val} {notes}".lower()

        # 1. Reject formatting noise and ebook licensing metadata
        noise_keywords = [
            "gutenberg", "ebook", "http", "license", "copyright", "isbn", "issn", "trademark",
            "release date", "most recently updated", "credits", "transcribe", "produced by", "project gutenberg"
        ]
        for kw in noise_keywords:
            if kw in combined_text:
                return "reject", f"Contains metadata noise keyword: '{kw}'"

        # Reject pure page formatting strings
        if re.search(r"\b(page|chapter|ch\.)\s*\d+", combined_text):
            return "reject", "Represents document layout/page number noise"

        # 2. Reject extremely generic punctuation rules
        generic_punc_patterns = [
            r"exclamation mark", r"question mark", r"comma placement", r"space before",
            r"apostrophe rules", r"spelling of", r"ellipsis spacing", r"punctuation style",
            r"noktalama işareti", r"virgül kullanımı", r"soru işareti", r"ünlem işareti"
        ]
        for pat in generic_punc_patterns:
            if re.search(pat, combined_text):
                return "reject", f"Represents a generic punctuation rule: '{pat}'"

        # 3. Work & Genre Scope Mismatch Check
        # If active work is Attention (technical), reject Alice-specific names/terms
        if work_id == "attention_is_all_you_need":
            alice_terms = ["alice", "rabbit", "hatter", "wonderland", "dinah", "caterpillar", "mock turtle"]
            for term in alice_terms:
                if term in combined_text:
                    return "reject", f"Work isolation breach: Alice term '{term}' detected in Attention run"
                    
        # If active work is Alice (literary), reject Transformer/attention-specific terms
        if work_id == "alice_in_wonderland":
            tech_terms = ["transformer", "attention mechanism", "encoder-decoder", "neural network", "transduction model"]
            for term in tech_terms:
                if term in combined_text:
                    return "reject", f"Work isolation breach: ML term '{term}' detected in Alice run"

        # If genre is technical, reject soft literary style heuristics or names
        if genre == "tech" and scope == "genre":
            literary_heuristics = ["literary rhythm", "poetic", "rhythm over literal", "storyteller"]
            for heur in literary_heuristics:
                if heur in combined_text:
                    return "reject", f"Genre mismatch: Literary rule '{heur}' detected in technical genre"

        # 4. Reject duplicate/trivial empty rules
        if not key and not val:
            return "reject", "Empty key and value"
            
        if itype == "style_rule" and len(val) < 15 and not key:
            return "reject", "Trivial or low-value style rule under 15 characters"

        return "evaluate", "Passes prefilter, needs evaluation"

    def review_candidate(self, 
                         item: Dict[str, Any], 
                         work_id: str = "", 
                         genre: str = "", 
                         user_id: str = "",
                         trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate a memory candidate using rule-based prefiltering, 
        followed by either Heuristic rules or LLM Evaluation.
        """
        # Step 1: Rule-based Prefilter
        decision, justification = self.prefilter_candidate(item, work_id=work_id, genre=genre)
        if decision == "reject":
            logger.info(f"Reviewer REJECTED candidate '{item.get('key')}' via prefilter. Reason: {justification}")
            reviewed_item = item.copy()
            reviewed_item.update({
                "status": "rejected",
                "importance_score": 0.0,
                "reviewer_notes": justification
            })
            return reviewed_item

        # Step 2: Main Evaluation
        if self.enable_llm_reviewer and Config.OPENAI_API_KEY:
            # Run LLM-based evaluation
            try:
                evaluation = self._run_llm_evaluation(item, work_id, genre, user_id, trace_id)
                status = evaluation.get("final_decision", "pending")
                # Normalize status
                if status not in ["active", "pending", "rejected"]:
                    status = "active" if status == "accept" else ("rejected" if status == "reject" else "pending")
                
                reviewed_item = item.copy()
                reviewed_item.update({
                    "status": status,
                    "importance_score": evaluation.get("importance_score", 0.5),
                    "scope": evaluation.get("suggested_scope", item.get("scope", "global")),
                    "reviewer_notes": evaluation.get("justification", "LLM Reviewed"),
                    "confidence": min(1.0, max(0.0, item.get("confidence", 0.7)))
                })
                logger.info(f"Reviewer LLM evaluated '{item.get('key')}': {status} (Importance: {reviewed_item['importance_score']})")
                return reviewed_item
            except Exception as e:
                logger.warning(f"Reviewer LLM failed, falling back to heuristics: {e}")
                
        # Heuristic-based fallback evaluation (Default when LLM Reviewer is disabled)
        confidence = item.get("confidence", 0.7)
        itype = item.get("type", "")
        key = item.get("key", "")
        scope = item.get("scope", "global")
        
        # Calculate heuristics
        importance_score = 0.5
        status = "pending"
        suggested_scope = scope
        notes = "Heuristic evaluated (LLM Reviewer Disabled)"

        if itype in ["terminology", "character_info"]:
            importance_score = 0.8
            # High confidence terms are immediately active
            status = "active" if confidence >= 0.8 else "pending"
            # Characters/Terms in a work should strictly be work scoped
            if work_id and suggested_scope == "global":
                suggested_scope = "work"
                notes += " -> Forced scope to work to prevent global pollution"
        elif itype in ["idiom", "phrasal_verb", "correction_pattern"]:
            importance_score = 0.7
            status = "active" if confidence >= 0.7 else "pending"
        elif itype == "style_rule":
            importance_score = 0.6
            # Style rules are more subjective, require higher confidence
            status = "active" if confidence >= 0.85 else "pending"
            if work_id and suggested_scope == "global" and "style" in key.lower():
                suggested_scope = "work"
                notes += " -> Forced style rule to work scope"
                
        reviewed_item = item.copy()
        reviewed_item.update({
            "status": status,
            "importance_score": importance_score,
            "scope": suggested_scope,
            "reviewer_notes": notes,
            "confidence": confidence
        })
        logger.info(f"Reviewer heuristic evaluated '{item.get('key')}': {status} (Importance: {importance_score})")
        return reviewed_item

    def _run_llm_evaluation(self, 
                            item: Dict[str, Any], 
                            work_id: str, 
                            genre: str, 
                            user_id: str,
                            trace_id: Optional[str]) -> Dict[str, Any]:
        """Call LLM with structured schema to review the candidate."""
        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=Config.MINI_MODEL,
            temperature=0
        )
        structured_llm = llm.with_structured_output(ReviewResultSchema, method="function_calling")
        
        prompt = f"""
You are the Memory Reviewer Agent for a Translation Intelligence Platform.
Evaluate the following translation memory candidate for quality control.

### Candidate Details:
- Key (Source pattern/term): {item.get('key')}
- Value (Target translation/rule): {item.get('value')}
- Type: {item.get('type')}
- Original Curator Scope: {item.get('scope')}
- Curator Confidence: {item.get('confidence')}
- Notes: {item.get('notes')}

### Context:
- Active Work: {work_id or 'None'}
- Active Genre: {genre or 'None'}
- Active User: {user_id or 'None'}

### Isolation & Quality Rules:
1. **Work Isolation:** Specific proper nouns, characters, names, locations, and title translations unique to the active work MUST remain in the 'work' scope. They must NEVER be global.
2. **Genre Isolation:** Technical terms (e.g., from ML/Transformer) must not bleed into literary contexts, and vice versa. Keep them in the 'genre' or 'work' scope.
3. **No Formatting Noise:** Reject items representing raw Gutenberg license files, line wrapping, pagination, transcribers' notes, web links, or raw system formatting codes.
4. **Deduplication:** Reject items that are trivial, empty, or redundant copies of standard dictionary rules.
5. **Pending:** Set decision to 'pending' if you are unsure or if the rule is highly subjective and needs human verification. Set to 'accept' only if high quality and correct scope.
"""
        callbacks = []
        if trace_id:
            handler = tracker.get_callback_handler(trace_id)
            if handler:
                callbacks.append(handler)
                
        result = structured_llm.invoke(prompt, config={"callbacks": callbacks})
        return {
            "relevance_score": result.relevance_score,
            "generality_score": result.generality_score,
            "scope_correctness_score": result.scope_correctness_score,
            "duplication_score": result.duplication_score,
            "contradiction_risk": result.contradiction_risk,
            "suggested_scope": result.suggested_scope,
            "importance_score": result.importance_score,
            "final_decision": result.final_decision,
            "justification": result.justification
        }
