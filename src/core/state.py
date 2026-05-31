from typing import TypedDict, List, Dict, Any, Optional

class TranslationState(TypedDict):
    # Inputs
    source_text: str
    source_language: str
    target_language: str
    
    # Context / References loaded at start
    style_guide: str
    glossary: List[Dict[str, str]]
    idioms: List[Dict[str, Any]]
    
    # Intermediate Outputs from Agents
    style_analysis: Optional[str]
    raw_translation: Optional[str]
    stylized_translation: Optional[str]
    critique: Optional[str]
    
    # Control Flags
    is_approved: bool
    revision_count: int
    
    # Final Output
    final_translation: Optional[str]
    
    # Execution Trace logs for console visualization
    logs: List[Dict[str, Any]]
    
    # Stateful / Chunked Translation memory
    previous_chunk_context: Optional[str]
    dynamic_glossary: List[Dict[str, str]]
