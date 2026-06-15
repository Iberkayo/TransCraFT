import logging
import re
from typing import Dict, Any, List, Optional
from src.tie.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class ContextRouter:
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager or MemoryManager()
        self.last_loaded_count = 0
        self.last_used_count = 0
        self.current_source_text = None

    def retrieve_relevant_memory(self, 
                                 source_text: str, 
                                 genre: Optional[str] = None, 
                                 work_id: Optional[str] = None, 
                                 user_id: Optional[str] = None,
                                 max_memory_items: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve memory records from all relevant scopes and filter them for the given source text.
        Returns a merged list of relevant memory item dicts.
        """
        self.current_source_text = source_text
        raw_items = []
        loaded_sources = []
        
        # 1. Load Global Memory
        global_items = self.memory_manager.get_memory_items("global")
        raw_items.extend(global_items)
        loaded_sources.append(f"global ({len(global_items)} items)")
        
        # 2. Load Genre Memory
        if genre:
            genre_items = self.memory_manager.get_memory_items("genre", scope_id=genre)
            raw_items.extend(genre_items)
            loaded_sources.append(f"genre:{genre} ({len(genre_items)} items)")
            
        # 3. Load Work Memory
        if work_id:
            work_items = self.memory_manager.get_memory_items("work", scope_id=work_id)
            raw_items.extend(work_items)
            loaded_sources.append(f"work:{work_id} ({len(work_items)} items)")
            
        # 4. Load User Memory
        if user_id:
            user_items = self.memory_manager.get_memory_items("user", scope_id=user_id)
            raw_items.extend(user_items)
            loaded_sources.append(f"user:{user_id} ({len(user_items)} items)")
            
        logger.info(f"ContextRouter loaded sources: {', '.join(loaded_sources)}")
        self.last_loaded_count = len(raw_items)
            
        # 5. Filter items to keep only relevant ones
        relevant_items = []
        
        # Normalize source text to alphanumeric characters for matching
        norm_source = re.sub(r'[^a-zA-Z0-9]', '', source_text.lower())
        
        for item in raw_items:
            key = str(item.get("key", "")).strip()
            item_type = item.get("type", "")
            
            # Non-targeted rules (like style_rule or general preference) apply broadly
            if item_type in ["style_rule", "preference"] or not key:
                if item.get("confidence", 0) >= 0.5:
                    relevant_items.append(item)
            else:
                # Keyed items check against source_text using normalized key
                norm_key = re.sub(r'[^a-zA-Z0-9]', '', key.lower())
                if norm_key and norm_key in norm_source:
                    relevant_items.append(item)
                    
        # 6. Deduplicate & Merge duplicates from different scopes (prioritize user/work over genre/global)
        unique_items = {}
        for item in relevant_items:
            key_val = str(item.get("key", "")).strip()
            norm_key = re.sub(r'[^a-zA-Z0-9]', '', key_val.lower())
            itype = item.get("type", "")
            
            if not norm_key:
                norm_key = re.sub(r'[^a-zA-Z0-9]', '', str(item.get("value", "")).lower())
                
            dup_key = (norm_key, itype)
            
            if dup_key in unique_items:
                existing = unique_items[dup_key]
                existing["confidence"] = max(existing.get("confidence", 0.7), item.get("confidence", 0.7))
                existing["importance_score"] = max(existing.get("importance_score", 0.5), item.get("importance_score", 0.5))
                # Merge values if dict, otherwise keep existing/fresher value
                if isinstance(existing.get("value"), dict) and isinstance(item.get("value"), dict):
                    existing["value"].update(item["value"])
                existing["usage_count"] = existing.get("usage_count", 1) + item.get("usage_count", 1)
            else:
                unique_items[dup_key] = item.copy()
                
        # 7. Sort items by importance_score descending, then confidence descending
        sorted_items = sorted(
            unique_items.values(),
            key=lambda x: (x.get("importance_score", 0.5), x.get("confidence", 0.7)),
            reverse=True
        )
        
        # 8. Limit to max_memory_items
        result = sorted_items[:max_memory_items]
        self.last_used_count = len(result)
        return result

    def generate_compact_context(self, relevant_items: List[Dict[str, Any]], work_id: Optional[str] = None) -> str:
        """
        Format the list of relevant memory items into a compact markdown string.
        """
        if not relevant_items and not work_id:
            return ""
            
        lines = []
        if relevant_items:
            lines.append("### Translation Intelligence Context (Relevant Memories):")
            
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
                    
        # TIE v0.3 Style Contract Integration
        if work_id:
            try:
                from src.tie.style_profiler import AuthorStyleProfiler
                from src.tie.style_contract import StyleContractGenerator
                
                from src.tie.author_mapping import resolve_author_for_work

                author_info = resolve_author_for_work(work_id)
                if not author_info:
                    return "\n".join(lines)

                work_key = author_info["work_key"]
                author_id = author_info["author_id"]
                author_name = author_info["author_name"]
                
                profiler = AuthorStyleProfiler(base_dir=self.memory_manager.base_dir)
                contract_gen = StyleContractGenerator(base_dir=self.memory_manager.base_dir)
                
                # Get sample chunk if available
                sample_chunks = [self.current_source_text] if self.current_source_text else []
                
                profile = profiler.load_or_infer_profile(
                    author_id=author_id,
                    author_name=author_name,
                    sample_chunks=sample_chunks
                )
                
                contract = contract_gen.load_or_generate_contract(
                    work_id=work_key,
                    author_profile=profile
                )
                
                if contract:
                    lines.append("\n### Style & Narrative Voice Guidelines")
                    lines.append(f"* **Tone**: {contract.get('tone')}")
                    lines.append(f"* **Sentence Rhythm**: {contract.get('sentence_rhythm')}")
                    lines.append("* **Directives**:")
                    for rule in contract.get("rules", []):
                        lines.append(f"  - {rule}")
            except Exception as e:
                logger.error(f"Error resolving style contract in ContextRouter: {e}")
                
        return "\n".join(lines)
