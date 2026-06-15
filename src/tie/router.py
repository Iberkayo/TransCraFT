import logging
from typing import Dict, Any, List, Optional
from src.tie.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class ContextRouter:
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager or MemoryManager()

    def retrieve_relevant_memory(self, 
                                 source_text: str, 
                                 genre: Optional[str] = None, 
                                 work_id: Optional[str] = None, 
                                 user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve memory records from all relevant scopes and filter them for the given source text.
        Returns a merged list of relevant memory item dicts.
        """
        raw_items = []
        
        # 1. Load Global Memory
        raw_items.extend(self.memory_manager.get_memory_items("global"))
        
        # 2. Load Genre Memory
        if genre:
            raw_items.extend(self.memory_manager.get_memory_items("genre", scope_id=genre))
            
        # 3. Load Work Memory
        if work_id:
            raw_items.extend(self.memory_manager.get_memory_items("work", scope_id=work_id))
            
        # 4. Load User Memory
        if user_id:
            raw_items.extend(self.memory_manager.get_memory_items("user", scope_id=user_id))
            
        # 5. Filter items to keep only relevant ones
        relevant_items = []
        source_lower = source_text.lower()
        
        for item in raw_items:
            key = str(item.get("key", "")).strip()
            item_type = item.get("type", "")
            
            # Non-targeted rules (like style_rule or general preference) apply broadly, so we include them if they have high confidence
            if item_type in ["style_rule", "preference"] or not key:
                if item.get("confidence", 0) >= 0.5:
                    relevant_items.append(item)
            else:
                # Keyed items (terminology, idiom, phrasal_verb, character_info) are checked against source_text
                if key.lower() in source_lower:
                    relevant_items.append(item)
                    
        return relevant_items

    def generate_compact_context(self, relevant_items: List[Dict[str, Any]], work_id: Optional[str] = None) -> str:
        """
        Format the list of relevant memory items into a compact markdown string.
        """
        if not relevant_items:
            return ""
            
        lines = ["### Translation Intelligence Context (Relevant Memories):"]
        
        # Group by type/scope to keep it clean
        characters = []
        terminology = []
        phrases = []
        rules = []
        
        for item in relevant_items:
            scope = item.get("scope", "")
            itype = item.get("type", "")
            key = item.get("key", "")
            val = item.get("value", "")
            notes = item.get("notes", "")
            
            # Format according to type
            if itype == "character_info":
                char_desc = f"'{key}' -> '{val}'"
                if notes:
                    char_desc += f" ({notes})"
                characters.append(char_desc)
            elif itype in ["terminology", "glossary"]:
                term_desc = f"'{key}' -> '{val}'"
                if notes:
                    term_desc += f" ({notes})"
                terminology.append(term_desc)
            elif itype in ["idiom", "phrasal_verb", "correction_pattern"]:
                phrase_desc = f"'{key}' -> '{val}'"
                if notes:
                    phrase_desc += f" ({notes})"
                phrases.append(phrase_desc)
            else:
                rule_desc = f"[{scope.upper()}] {key or val}"
                if key and val:
                    rule_desc = f"[{scope.upper()}] {key}: {val}"
                rules.append(rule_desc)
                
        # Build compact context blocks
        if characters:
            lines.append("Characters:")
            for c in characters:
                lines.append(f"  - {c}")
        if terminology:
            lines.append("Terminology:")
            for t in terminology:
                lines.append(f"  - {t}")
        if phrases:
            lines.append("Phrasal Verbs & Idioms:")
            for p in phrases:
                lines.append(f"  - {p}")
        if rules:
            lines.append("General Rules & Preferences:")
            for r in rules:
                lines.append(f"  - {r}")
                
        # Optional: Include style profile if work_id has one
        if work_id:
            profile = self.memory_manager.read_style_profile(work_id)
            if profile:
                # Add first 3 lines of style profile or summary to keep it compact
                lines.append("Work Style Profile:")
                summary = "\n".join(profile.splitlines()[:5])
                lines.append(f"  {summary}")
                
        return "\n".join(lines)
