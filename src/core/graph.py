from langgraph.graph import StateGraph, END
from src.core.state import TranslationState
from src.agents.analyst import analyze_style_and_culture
from src.agents.translator import translate_draft
from src.agents.stylist import stylize_translation
from src.agents.critic import evaluate_translation
from src.agents.polisher import polish_translation

from src.agents.extractor import extract_terminology

def run_context_router(state: TranslationState) -> dict:
    """Determine and retrieve relevant memories based on genre, work_id, user_id."""
    if not state.get("enable_tie", False):
        return {
            "compact_memory_context": "",
            "relevant_memories": [],
            "loaded_memory_ids": [],
            "injected_memory_ids": [],
            "memory_provenance": []
        }
    
    from src.tie.router import ContextRouter
    from src.tie.memory_manager import MemoryManager
    from src.core.config import Config
    
    manager = MemoryManager(base_dir=Config.MEMORY_DIR)
    router = ContextRouter(memory_manager=manager)
    
    source_text = state.get("source_text", "")
    genre = state.get("genre", "literary")
    work_id = state.get("work_id")
    user_id = state.get("user_id")
    
    relevant = router.retrieve_relevant_memory(
        source_text=source_text,
        genre=genre,
        work_id=work_id,
        user_id=user_id
    )
    compact = router.generate_compact_context(relevant, work_id=work_id)
    memory_provenance = [
        {
            "memory_id": item.get("memory_id"),
            "key": item.get("key"),
            "type": item.get("type"),
            "scope": item.get("scope"),
            "scope_id": item.get("scope_id"),
            "confidence": item.get("confidence"),
            "importance_score": item.get("importance_score"),
            "source_path": item.get("_source_path"),
            "provenance": item.get("provenance"),
        }
        for item in relevant
        if item.get("memory_id")
    ]
    memory_id_text = ", ".join(item["memory_id"] for item in memory_provenance) or "None"
    
    log_entry = {
        "agent": "Context Router",
        "action": "Retrieved relevant translation memories",
        "output": f"Loaded {len(relevant)} memory item(s). Memory IDs used: {memory_id_text}. Compact Context:\n{compact}" if relevant else "No relevant memories found."
    }
    
    return {
        "relevant_memories": relevant,
        "compact_memory_context": compact,
        "loaded_memory_ids": router.last_loaded_memory_ids,
        "injected_memory_ids": router.last_injected_memory_ids,
        "memory_provenance": memory_provenance,
        "memory_loaded_count": router.last_loaded_count,
        "memory_used_count": router.last_used_count,
        "logs": state.get("logs", []) + [log_entry]
    }

def run_memory_effectiveness(state: TranslationState) -> dict:
    """Evaluate whether routed memories were reflected in the final translation."""
    if not state.get("enable_tie", False):
        return {}

    try:
        from src.core.config import Config
        from src.tie.memory_manager import MemoryManager
        from src.tie.memory_effectiveness import MemoryEffectivenessEvaluator

        source_text = state.get("source_text", "")
        final_translation = state.get("final_translation", "") or ""
        if not final_translation:
            for log in state.get("logs", []):
                if log.get("agent") == "Final Polisher":
                    final_translation = log.get("output", "")
                    break

        evaluator = MemoryEffectivenessEvaluator(
            enable_llm=Config.ENABLE_MEMORY_EFFECTIVENESS_LLM
        )
        records = evaluator.evaluate_chunk(
            source_text=source_text,
            translated_text=final_translation,
            loaded_memories=state.get("relevant_memories", []) or [],
            injected_memory_ids=state.get("injected_memory_ids", []) or [],
            genre=state.get("genre"),
            work_id=state.get("work_id"),
        )

        manager = MemoryManager(base_dir=Config.MEMORY_DIR)
        updated_count = manager.update_memory_effectiveness(records)
        summary = evaluator.summarize_records(records)

        trace_id = state.get("trace_id")
        if trace_id:
            try:
                from src.observability.langfuse_tracker import tracker

                span = tracker.create_span(
                    trace_id,
                    name="memory_effectiveness",
                    metadata={
                        "loaded_memory_ids": state.get("loaded_memory_ids", []) or [],
                        "detected_memory_ids": [
                            r.get("memory_id") for r in records if r.get("detected_in_output")
                        ],
                        "average_impact": summary["average_memory_impact"],
                        "harm_score": summary["average_harm_score"],
                        "decisions_summary": {
                            "promote": summary["promoted_memory_count"],
                            "keep": summary["kept_memory_count"],
                            "downgrade": summary["downgraded_memory_count"],
                            "retire": summary["retired_memory_count"],
                            "review": summary["review_memory_count"],
                        },
                    },
                )
                tracker.end_span(span, output_data=summary)
            except Exception:
                pass

        try:
            from src.observability.mlflow_tracker import mlflow_tracker

            mlflow_tracker.log_memory_effectiveness_metrics(summary)
        except Exception:
            pass

        log_entry = {
            "agent": "Memory Effectiveness",
            "action": "Measured routed memory usage in final translation",
            "output": (
                f"Evaluated {len(records)} memory item(s), updated {updated_count}. "
                f"Detected {summary['memory_detected_count']} in output. "
                f"Average impact {summary['average_memory_impact']:.2f}, "
                f"average harm {summary['average_harm_score']:.2f}."
            )
        }
        return {
            "memory_effectiveness_records": records,
            "memory_effectiveness_summary": summary,
            "logs": state.get("logs", []) + [log_entry],
        }
    except Exception as e:
        log_entry = {
            "agent": "Memory Effectiveness",
            "action": "Skipped memory effectiveness evaluation",
            "output": f"Fail-safe skip: {e}"
        }
        return {"logs": state.get("logs", []) + [log_entry]}

def run_memory_curator(state: TranslationState) -> dict:
    """Extract and persist new translation decisions, terminology, and patterns."""
    if not state.get("enable_tie", False):
        return {}
        
    from src.tie.curator import MemoryCurator
    from src.tie.memory_manager import MemoryManager
    from src.tie.reviewer import MemoryReviewer
    from src.core.config import Config
    
    manager = MemoryManager(base_dir=Config.MEMORY_DIR)
    curator = MemoryCurator(memory_manager=manager)
    reviewer = MemoryReviewer()
    
    source_text = state.get("source_text", "")
    draft_translation = state.get("raw_translation", "")
    critic_feedback = state.get("critique", "")
    final_translation = state.get("final_translation", "")
    
    # Try to resolve final translation if empty
    if not final_translation:
        for log in state.get("logs", []):
            if log.get("agent") == "Final Polisher":
                final_translation = log.get("output", "")
                
    genre = state.get("genre", "literary")
    work_id = state.get("work_id")
    user_id = state.get("user_id")
    trace_id = state.get("trace_id")
    chunk_index = state.get("chunk_index")
    
    # Extract candidate memories (but do not save directly)
    extracted = curator.run_curator(
        source_text=source_text,
        draft_translation=draft_translation,
        critic_feedback=critic_feedback,
        final_translation=final_translation,
        genre=genre,
        work_id=work_id,
        user_id=user_id,
        persist=False
    )
    
    accepted_count = 0
    rejected_count = 0
    pending_count = 0
    pollution_violations = 0
    
    for item in extracted:
        item.setdefault("created_by", "memory_curator")
        item.setdefault("source_chunk", chunk_index)
        item.setdefault("trace_id", trace_id)

        # Review candidate memory quality and scope isolation
        reviewed = reviewer.review_candidate(
            item=item,
            work_id=work_id or "",
            genre=genre or "",
            user_id=user_id or "",
            trace_id=trace_id
        )
        
        status = reviewed.get("status", "active")
        notes = reviewed.get("reviewer_notes", "")
        
        # Check if rejection notes indicate scope pollution/isolation breach
        if status == "rejected" and ("Work isolation breach" in notes or "Genre mismatch" in notes):
            pollution_violations += 1
            
        if status == "active":
            scope = reviewed.get("scope", "global")
            scope_id = None
            if scope == "genre":
                scope_id = genre or "literary"
            elif scope == "work":
                scope_id = work_id or "default_work"
            elif scope == "user":
                scope_id = user_id or "default_user"
                
            try:
                manager.add_memory_item(scope=scope, item=reviewed, scope_id=scope_id)
                accepted_count += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to add memory item to TIE: {e}")
        elif status == "pending":
            scope = reviewed.get("scope", "global")
            scope_id = None
            if scope == "genre":
                scope_id = genre or "literary"
            elif scope == "work":
                scope_id = work_id or "default_work"
            elif scope == "user":
                scope_id = user_id or "default_user"
                
            try:
                manager.add_memory_item(scope=scope, item=reviewed, scope_id=scope_id)
                pending_count += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to add pending memory item: {e}")
        else:
            rejected_count += 1
            
    log_entry = {
        "agent": "Memory Curator",
        "action": "Extracted and reviewed translation intelligence items",
        "output": f"Extracted {len(extracted)} candidate(s). Review decision: {accepted_count} accepted, {pending_count} pending, {rejected_count} rejected. Scope/pollution violations: {pollution_violations}."
    }
    
    return {
        "memory_candidates_count": len(extracted),
        "memory_accepted_count": accepted_count,
        "memory_rejected_count": rejected_count,
        "memory_pending_count": pending_count,
        "memory_pollution_violations": pollution_violations,
        "logs": state.get("logs", []) + [log_entry]
    }

def route_after_critic(state: TranslationState) -> str:
    """Determine whether to route to the polisher or loop back to the stylist."""
    if state.get("is_approved", False):
        return "polisher"
    else:
        return "stylist"

def create_translation_graph() -> StateGraph:
    """Create and compile the LangGraph workflow for cultural translation."""
    # Initialize the graph with our state definition
    workflow = StateGraph(TranslationState)
    
    # Add nodes (agents)
    workflow.add_node("router", run_context_router)
    workflow.add_node("extractor", extract_terminology)
    workflow.add_node("analyst", analyze_style_and_culture)
    workflow.add_node("translator", translate_draft)
    workflow.add_node("stylist", stylize_translation)
    workflow.add_node("critic", evaluate_translation)
    workflow.add_node("polisher", polish_translation)
    workflow.add_node("memory_effectiveness", run_memory_effectiveness)
    workflow.add_node("curator", run_memory_curator)
    
    # Define execution flow
    workflow.set_entry_point("router")
    
    # Connection mapping
    workflow.add_edge("router", "extractor")
    workflow.add_edge("extractor", "analyst")
    workflow.add_edge("analyst", "translator")
    workflow.add_edge("translator", "stylist")
    workflow.add_edge("stylist", "critic")
    
    # Conditional routing after evaluation
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "polisher": "polisher",
            "stylist": "stylist"
        }
    )
    
    # Final node connections
    workflow.add_edge("polisher", "memory_effectiveness")
    workflow.add_edge("memory_effectiveness", "curator")
    workflow.add_edge("curator", END)
    
    return workflow.compile()
