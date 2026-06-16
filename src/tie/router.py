import logging
import re
from typing import Dict, Any, List, Optional
from src.core.config import Config
from src.tie.memory_manager import MemoryManager
from src.tie.memory_ranker import MemoryAwareRanker

logger = logging.getLogger(__name__)

class ContextRouter:
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        enable_memory_aware: Optional[bool] = None,
        record_usage: bool = True,
    ):
        self.memory_manager = memory_manager or MemoryManager()
        self.enable_memory_aware = Config.ENABLE_MEMORY_AWARE_ROUTER if enable_memory_aware is None else enable_memory_aware
        self.record_usage = record_usage
        self.ranker = MemoryAwareRanker()
        self.last_loaded_count = 0
        self.last_used_count = 0
        self.last_loaded_memory_ids: List[str] = []
        self.last_injected_memory_ids: List[str] = []
        self.last_skipped_memory_ids: List[str] = []
        self.last_routing_decisions: List[Dict[str, Any]] = []
        self.last_routing_summary: Dict[str, Any] = {}
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
        self.last_loaded_memory_ids = [item.get("memory_id") for item in raw_items if item.get("memory_id")]
        if self.record_usage:
            try:
                self.memory_manager.record_memory_loaded(self.last_loaded_memory_ids)
            except Exception as e:
                logger.warning(f"Failed to record loaded memory ids: {e}")

        if self.enable_memory_aware:
            ranked = self.ranker.route(
                source_text=source_text,
                memory_items=raw_items,
                max_memory_items=max_memory_items,
            )
            result = ranked["injected"]
            self.last_used_count = len(result)
            self.last_injected_memory_ids = ranked["injected_memory_ids"]
            self.last_skipped_memory_ids = ranked["skipped_memory_ids"]
            self.last_routing_decisions = ranked["routing_decisions"]
            self.last_routing_summary = ranked["summary"]
            if self.record_usage:
                try:
                    self.memory_manager.record_memory_injected(self.last_injected_memory_ids)
                except Exception as e:
                    logger.warning(f"Failed to record injected memory ids: {e}")
            return result
            
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
        self.last_injected_memory_ids = [item.get("memory_id") for item in result if item.get("memory_id")]
        self.last_skipped_memory_ids = [
            item.get("memory_id")
            for item in sorted_items[max_memory_items:]
            if item.get("memory_id")
        ]
        self.last_routing_decisions = [
            {
                "memory_id": item.get("memory_id"),
                "key": item.get("key"),
                "scope": item.get("scope"),
                "type": item.get("type"),
                "final_score": item.get("importance_score", 0.5),
                "decision": "inject" if item in result else "skip",
                "reason": "Legacy router ordering by importance and confidence.",
            }
            for item in sorted_items
        ]
        self.last_routing_summary = self.ranker.summarize(self.last_routing_decisions)
        if self.record_usage:
            try:
                self.memory_manager.record_memory_injected(self.last_injected_memory_ids)
            except Exception as e:
                logger.warning(f"Failed to record injected memory ids: {e}")
        return result

    def generate_compact_context(self, relevant_items: List[Dict[str, Any]], work_id: Optional[str] = None) -> str:
        """
        Format the list of relevant memory items into a compact markdown string.
        """
        if not relevant_items and not work_id:
            return ""
            
        lines = []
        if relevant_items:
            lines.append("### Translation Intelligence Context")
            
            sections = [
                ("#### High-Confidence Work Memory", lambda item: item.get("scope") == "work"),
                ("#### User / Genre Preferences", lambda item: item.get("scope") in {"user", "genre"}),
                ("#### Global Rules", lambda item: item.get("scope") == "global"),
            ]
            for title, predicate in sections:
                grouped_items = [item for item in relevant_items if predicate(item)]
                if not grouped_items:
                    continue
                lines.append(title)
                for item in grouped_items:
                    lines.append(f"- {self._format_memory_line(item)}")
                    
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

    def _format_memory_line(self, item: Dict[str, Any]) -> str:
        scope = item.get("scope", "")
        itype = item.get("type", "")
        key = item.get("key", "")
        val = item.get("value", "")
        notes = item.get("notes", "")
        if itype in {"character_info", "terminology", "glossary", "idiom", "phrasal_verb", "correction_pattern"}:
            desc = f"{key} -> {val}"
        else:
            desc = f"[{scope.upper()}] {key}: {val}" if key and val else f"[{scope.upper()}] {key or val}"
        if notes:
            desc += f" ({notes})"
        routing = item.get("_routing_decision") or {}
        if routing.get("final_score") is not None:
            desc += f" [score: {routing['final_score']:.2f}]"
        return desc
