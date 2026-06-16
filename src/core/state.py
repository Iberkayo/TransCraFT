from typing import TypedDict, List, Dict, Any, Optional

class TranslationState(TypedDict):
    # Inputs
    source_text: str
    source_language: str
    target_language: str
    
    # Context / References loaded at start
    style_preset: str
    style_guide: str
    glossary: List[Dict[str, str]]
    positive_glossary: Dict[str, str]
    negative_glossary: Dict[str, str]
    idioms: List[Dict[str, Any]]
    auto_glossary_candidates: Dict[str, str]
    
    # Intermediate Outputs from Agents
    style_analysis: Optional[str]
    raw_translation: Optional[str]
    stylized_translation: Optional[str]
    critique: Optional[str]
    
    # Control Flags
    is_approved: bool
    revision_count: int
    style_revision_count: Optional[int]

    
    # Final Output
    final_translation: Optional[str]
    
    # Execution Trace logs for console visualization
    logs: List[Dict[str, Any]]
    
    # Stateful / Chunked Translation memory
    previous_chunk_context: Optional[str]
    dynamic_glossary: List[Dict[str, str]]

    # Observability
    trace_id: Optional[str]
    chunk_index: Optional[int]

    # Translation Intelligence Engine (TIE) fields
    user_id: Optional[str]
    work_id: Optional[str]
    genre: Optional[str]
    enable_tie: Optional[bool]
    relevant_memories: Optional[List[Dict[str, Any]]]
    compact_memory_context: Optional[str]
    memory_provenance: Optional[List[Dict[str, Any]]]
    loaded_memory_ids: Optional[List[str]]
    injected_memory_ids: Optional[List[str]]
    skipped_memory_ids: Optional[List[str]]
    routing_decisions: Optional[List[Dict[str, Any]]]
    routing_summary: Optional[Dict[str, Any]]
    memory_effectiveness_records: Optional[List[Dict[str, Any]]]
    memory_effectiveness_summary: Optional[Dict[str, Any]]

    # TIE v0.6 translation strategy planning
    translation_strategy: Optional[Dict[str, Any]]
    language_profile: Optional[Dict[str, Any]]
    source_language_profile: Optional[Dict[str, Any]]
    target_language_profile: Optional[Dict[str, Any]]
    strategy_planner_fallback_used: Optional[bool]

    # TIE v0.7 human translator revision checklist
    revision_checklist: Optional[Dict[str, Any]]
    revision_evaluation: Optional[Dict[str, Any]]
    revision_recommendations: Optional[List[str]]
