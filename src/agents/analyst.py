from langchain_openai import ChatOpenAI
from src.core.config import Config
from src.core.state import TranslationState
from src.observability.langfuse_tracker import tracker

def analyze_style_and_culture(state: TranslationState) -> dict:
    """Analyze the style, tone, and cultural nuances of the source text."""
    trace_id = state.get("trace_id")
    chunk_index = state.get("chunk_index")
    span = tracker.create_span(trace_id, name="analyst_node", metadata={"chunk_index": chunk_index})

    llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=Config.MINI_MODEL,
        temperature=0
    )
    
    source_text = state["source_text"]
    style_guide = state["style_guide"]
    glossary = state["glossary"]
    idioms = state["idioms"]
    
    # Stateful translation support
    prev_context = state.get("previous_chunk_context", "None (This is the first chunk)")
    dyn_glossary = state.get("dynamic_glossary", [])
    
    prompt = f"""
You are a master literary analyst and translator. Your job is to analyze the following source text and create a comprehensive guide for the translation pipeline.

### Source Text:
{source_text}

### Narrative Context from Previous Chunk:
{prev_context}

### Dynamic Glossary of Terms (from previous chunks):
{dyn_glossary}

### Style Guide Rules:
{style_guide}

### Available Glossary of Terms:
{glossary}

### Reference Idioms:
{idioms}

Analyze the source text carefully and output a report covering:
1. **Genre & Tone:** What is the literary style, tone (e.g., dramatic, ironic, formal), and emotional impact of this text?
2. **Key Challenges:** Identify linguistic challenges, unusual word orders, or sentences that might sound robotic if translated literally.
3. **Idioms & Cultural Terms Detected:** Identify any idioms or cultural concepts present in the source text. Suggest natural Turkish equivalents from the reference list or your own knowledge.
4. **Glossary Alignment:** List any terms from the glossary and dynamic glossary that appear in the text and how they should be handled.
5. **Stylistic Instructions:** Specific instructions for the Stylist Agent on how to structure sentences in Turkish to maintain flow and continuity from the previous chunk.

Provide a clear and concise report in Turkish.
"""
    
    callbacks = []
    if trace_id:
        handler = tracker.get_callback_handler(trace_id)
        if handler:
            callbacks.append(handler)
            
    response = llm.invoke(prompt, config={"callbacks": callbacks})
    report = response.content
    
    tracker.end_span(span, output_data=report)

    # Create log trace
    log_entry = {
        "agent": "Style & Culture Analyst",
        "action": "Analyzed style and cultural nuances",
        "output": report
    }
    
    return {
        "style_analysis": report,
        "logs": state.get("logs", []) + [log_entry]
    }
