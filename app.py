import streamlit as st
import os
import json
import tempfile
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from src.core.config import Config
from src.core.graph import create_translation_graph
from src.core.document_processor import DocumentProcessor
from src.core.evaluator import TranslationEvaluator
from src.observability.langfuse_tracker import tracker
from langchain_openai import ChatOpenAI

st.set_page_config(page_title="TransCraft Web", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for dark aesthetic
st.markdown("""
<style>
    /* Styling adjustments */
    .stApp {
        background-color: #0E1117;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton>button {
        background: linear-gradient(90deg, #4A00E0 0%, #8E2DE2 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        opacity: 0.9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✨ TransCraft Web</div>', unsafe_allow_html=True)
st.markdown("*Autonomous Multi-Agent Literary & Cultural Translation System*")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    target_lang = st.text_input("Target Language", value="Turkish")
    source_lang = st.text_input("Source Language", value="English")
    genre = st.selectbox("Genre / Domain", options=["literary", "tech"])
    
    style_preset = st.selectbox("Style Preset", options=[
        "modern_turkish", 
        "classic_literary", 
        "childrens_book", 
        "academic_technical", 
        "publisher_editor"
    ])
    
    chunk_size = st.slider("Chunk Size (chars)", min_value=1000, max_value=8000, value=3000, step=500)

st.write("---")

input_method = st.radio("Input Method", ["Text Input", "File Upload"], horizontal=True)

input_text = ""
if input_method == "Text Input":
    input_text = st.text_area("Paste your text here", height=200)
else:
    uploaded_file = st.file_uploader("Upload Document (.txt, .pdf, .epub)", type=["txt", "pdf", "epub"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)
        input_text = DocumentProcessor.load_document(tmp_path)
        os.unlink(tmp_path)

if st.button("🚀 Start Translation", use_container_width=True):
    if not input_text.strip():
        st.error("Please provide text to translate.")
        st.stop()
        
    try:
        Config.validate()
    except Exception as e:
        st.error(f"Configuration Error: {e}")
        st.stop()

    # Process text
    with st.spinner("Processing document..."):
        chunks = DocumentProcessor.smart_chunk_text(input_text, max_chunk_size=chunk_size)
    
    st.success(f"Document split into {len(chunks)} chunk(s).")
    
    # Load references
    _, glossary_path = Config.get_genre_paths(genre)
    style_guide_path = Config.get_style_path(style_preset)
    
    style_guide = ""
    if style_guide_path.exists():
        with open(style_guide_path, "r", encoding="utf-8") as f:
            style_guide = f.read()
    
    glossary = []
    if glossary_path.exists():
        with open(glossary_path, "r", encoding="utf-8") as f:
            glossary = json.load(f)
            
    idioms = []
    if Config.IDIOMS_PATH.exists():
        with open(Config.IDIOMS_PATH, "r", encoding="utf-8") as f:
            idioms = json.load(f)
            
    # Load Negative Glossary
    negative_glossary_path = Config.REFERENCE_DIR / "yanlis_ceviriler.json"
    negative_glossary = {}
    if negative_glossary_path.exists():
        with open(negative_glossary_path, "r", encoding="utf-8") as f:
            negative_glossary = json.load(f)

    # Load Positive Glossary
    positive_glossary_path = Config.REFERENCE_DIR / "positive_glossary.json"
    positive_glossary = {}
    if positive_glossary_path.exists():
        with open(positive_glossary_path, "r", encoding="utf-8") as f:
            positive_glossary = json.load(f)

    # Initialize Translation Memory
    from src.core.memory import TranslationMemory
    tm = TranslationMemory()

    graph = create_translation_graph()
    summary_llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL, model=Config.MINI_MODEL, temperature=0)

    # Langfuse Trace
    run_name = "translation_streamlit"
    trace_id = tracker.create_trace(
        name=run_name,
        metadata={
            "genre": genre,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
    )

    translated_chunks = []
    previous_chunk_context = ""
    dynamic_glossary = []

    progress_bar = st.progress(0)
    
    for i, chunk_text in enumerate(chunks):
        st.subheader(f"Translating Chunk {i+1}/{len(chunks)}")
        
        # Check Cache!
        cached_translation = tm.get_translation(chunk_text)
        if cached_translation:
            st.info(f"✅ Chunk {i+1} found in Translation Memory! Skipped LLM processing to save costs and tokens.")
            translated_chunks.append(cached_translation)
            progress_bar.progress((i + 1) / len(chunks))
            continue
        
        initial_state = {
            "source_text": chunk_text,
            "source_language": source_lang,
            "target_language": target_lang,
            "style_preset": style_preset,
            "style_guide": style_guide,
            "glossary": glossary,
            "positive_glossary": positive_glossary,
            "negative_glossary": negative_glossary,
            "auto_glossary_candidates": {},
            "idioms": idioms,
            "style_analysis": None,
            "raw_translation": None,
            "stylized_translation": None,
            "critique": None,
            "is_approved": False,
            "revision_count": 0,
            "final_translation": None,
            "logs": [],
            "previous_chunk_context": previous_chunk_context,
            "dynamic_glossary": dynamic_glossary,
            "trace_id": trace_id,
            "chunk_index": i
        }

        current_log_index = 0
        final_translation = None
        
        # Display logs beautifully
        log_container = st.container()
        
        for output in graph.stream(initial_state):
            node_name = list(output.keys())[0]
            node_state = output[node_name]
            
            logs = node_state.get("logs", [])
            while current_log_index < len(logs):
                log = logs[current_log_index]
                agent_name = log["agent"]
                action = log["action"]
                content = log["output"]
                
                with log_container:
                    with st.expander(f"🤖 {agent_name} - {action}", expanded=False):
                        st.markdown(content)
                        
                current_log_index += 1
                
            if "final_translation" in node_state and node_state["final_translation"]:
                final_translation = node_state["final_translation"]

        # Double check fallback
        if not final_translation:
            for log in logs:
                if log["agent"] == "Final Polisher":
                    final_translation = log["output"]

        # Save to cache
        if final_translation:
            tm.save_translation(chunk_text, final_translation)

        translated_chunks.append(final_translation)
        
        if i < len(chunks) - 1:
            try:
                summary_prompt = f"Provide a brief 2-sentence summary in English of the following translated narrative to be used as context for translating the next section: {final_translation}"
                previous_chunk_context = summary_llm.invoke(summary_prompt).content.strip()
            except:
                previous_chunk_context = ""
                
        progress_bar.progress((i + 1) / len(chunks))

    # Assembly
    st.write("---")
    st.header("🎉 Final Translation")
    full_translation = "\n\n".join(translated_chunks)
    st.markdown(f"> {full_translation}")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        st.download_button("📥 Download as TXT", full_translation, file_name="translated_document.txt", mime="text/plain", use_container_width=True)
    
    with col_dl2:
        with st.spinner("Generating PDF..."):
            import urllib.request
            from fpdf import FPDF
            font_path = Config.REFERENCE_DIR / "DejaVuSans.ttf"
            if not font_path.exists():
                urllib.request.urlretrieve("https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf", font_path)
            
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('DejaVu', '', str(font_path), uni=True)
            pdf.set_font('DejaVu', '', 12)
            pdf.multi_cell(0, 10, full_translation)
            pdf_bytes = pdf.output(dest='S')
            
        st.download_button("📥 Download as PDF", pdf_bytes, file_name="translated_document.pdf", mime="application/pdf", use_container_width=True)

    # Consistency Check
    with st.spinner("Running Enterprise Consistency Checker..."):
        from src.agents.consistency_checker import run_consistency_check
        consistency_report = run_consistency_check(input_text, full_translation, positive_glossary)
        
        if consistency_report.get("issues_found", 0) > 0:
            st.warning(f"Found {consistency_report['issues_found']} potential inconsistencies.")
            for issue in consistency_report.get("issues", []):
                st.markdown(f"- **{issue['type']}**: {issue['description']}")
                
        if consistency_report.get("glossary_candidates"):
            st.info(f"Extracted {len(consistency_report['glossary_candidates'])} terminology recommendations.")
            # Save candidates
            runtime_dir = Config.DATA_DIR / "runtime"
            runtime_dir.mkdir(parents=True, exist_ok=True)
            candidate_path = runtime_dir / "auto_glossary_candidate.json"
            try:
                if candidate_path.exists():
                    with open(candidate_path, "r", encoding="utf-8") as f:
                        disk_candidates = json.load(f)
                else:
                    disk_candidates = {}
                    
                for rec in consistency_report["glossary_candidates"]:
                    disk_candidates[rec["source_term"]] = rec["target_term"]
                    
                with open(candidate_path, "w", encoding="utf-8") as f:
                    json.dump(disk_candidates, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # Evaluation
    with st.spinner("Running AI Quality Evaluation..."):
        eval_source = input_text[:4000] + "\n... [truncated] ...\n" + input_text[-4000:] if len(input_text) > 8000 else input_text
        eval_translation = full_translation[:4000] + "\n... [truncated] ...\n" + full_translation[-4000:] if len(full_translation) > 8000 else full_translation
        
        evaluation = TranslationEvaluator.evaluate_translation(eval_source, eval_translation, genre=genre)
        
        st.subheader("📊 AI-as-a-Judge Evaluation")
        st.markdown(f"**Overall Quality Score:** {evaluation['overall_score']:.1f}/5.0")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{evaluation['accuracy']}/5")
        col2.metric("Fluency", f"{evaluation['fluency']}/5")
        col3.metric("Grammar", f"{evaluation['grammar']}/5")
        col4.metric("Consistency", f"{evaluation['consistency']}/5")
        
        st.info(evaluation['summary'])
        
    if Config.ENABLE_MLFLOW:
        try:
            from src.observability.mlflow_tracker import mlflow_tracker
            mlflow_tracker.log_translation_experiment(
                run_name="translation_streamlit",
                params={
                    "genre": genre,
                    "style_preset": style_preset,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                },
                metrics={
                    "overall_score": float(evaluation.get('overall_score', 0.0)),
                    "accuracy": float(evaluation.get('accuracy', 0.0)),
                    "fluency": float(evaluation.get('fluency', 0.0)),
                    "grammar": float(evaluation.get('grammar', 0.0)),
                    "consistency": float(evaluation.get('consistency', 0.0))
                }
            )
        except Exception as e:
            # Silently pass or warn without breaking the UI flow
            st.toast(f"MLflow logging warning: {e}")
    
    try:
        tracker.flush()
    except:
        pass
