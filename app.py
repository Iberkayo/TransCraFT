import streamlit as st
import json
import tempfile
from pathlib import Path
from langchain_openai import ChatOpenAI

# Import project logic
from src.core.config import Config
from src.core.graph import create_translation_graph
from src.core.document_processor import DocumentProcessor
from src.core.evaluator import TranslationEvaluator

# Set page configuration
st.set_page_config(
    page_title="TransCraft AI - Multi-Agent Translation Playground",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark-sleek premium theme and glassmorphism cards
st.markdown("""
<style>
    .main {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .stButton>button {
        background: linear-gradient(90deg, #3B82F6 0%, #10B981 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .agent-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
    }
    .agent-name {
        font-weight: bold;
        color: #60A5FA;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Description
st.title("✨ TransCraft AI Playground")
st.caption("Çoklu Ajan Tabanlı Otonom Edebi ve Teknik Çeviri Sistemi")

# 1. Sidebar - Configuration
st.sidebar.header("⚙️ Sistem Yapılandırması")

# API Key handling
api_key_input = st.sidebar.text_input(
    "OpenAI API Anahtarı",
    value=Config.OPENAI_API_KEY or "",
    type="password",
    help="Anahtar girilmezse varsa .env dosyasındaki anahtar kullanılacaktır."
)

# If user input a key, override config value
if api_key_input:
    Config.OPENAI_API_KEY = api_key_input

genre = st.sidebar.selectbox(
    "Metin Türü (Genre)",
    options=["literary", "tech"],
    index=0,
    format_func=lambda x: "📚 Edebi Eser (Literary)" if x == "literary" else "💻 Teknik Makale (Tech)"
)

source_lang = st.sidebar.text_input("Kaynak Dil", value="English")
target_lang = st.sidebar.text_input("Hedef Dil", value="Turkish")

chunk_size = st.sidebar.slider(
    "Maksimum Parça Boyutu (Karakter)",
    min_value=1000,
    max_value=8000,
    value=3000,
    step=500
)

st.sidebar.divider()
st.sidebar.markdown("""
### Nasıl Çalışır?
1. OpenAI API Anahtarınızı girin.
2. Bir **PDF** veya **TXT** belgesi yükleyin.
3. Çeviriyi başlatın ve ajanların (Analist, Çevirmen, Stilist, Eleştirmen, Cilalayıcı) canlı tartışmalarını sol sütundan izleyin!
""")

# Check API Key validity
if not Config.OPENAI_API_KEY:
    st.warning("⚠️ Lütfen devam etmek için sol menüden veya .env dosyasından OpenAI API Anahtarınızı girin.")
    st.stop()

# 2. Document Upload Area
uploaded_file = st.file_uploader("Çevrilecek Belgeyi Seçin (.pdf, .txt)", type=["pdf", "txt"])

if uploaded_file is not None:
    # Save uploaded file to temp file to read
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = Path(tmp_file.name)

    try:
        # Load and chunk
        full_text = DocumentProcessor.load_document(tmp_path)
        chunks = DocumentProcessor.smart_chunk_text(full_text, max_chunk_size=chunk_size)
        st.info(f"📄 Dosya yüklendi: **{uploaded_file.name}** | Metin uzunluğu: **{len(full_text)}** karakter | Toplam **{len(chunks)}** parça belirlendi.")
    except Exception as e:
        st.error(f"Dosya işlenirken hata oluştu: {e}")
        st.stop()

    # 3. Main Action
    if st.button("Çeviri İşlemini Başlat 🚀"):
        st.divider()
        
        # Define columns: Left for agent logs, Right for final output
        col_agents, col_output = st.columns([1, 1])
        
        with col_agents:
            st.subheader("🤖 Ajanların Çalışma Alanı (Canlı Traces)")
            agent_container = st.container()
            
        with col_output:
            st.subheader("📝 Çevrilen Metin (Akıcı Türkçe)")
            output_text_area = st.empty()
            progress_bar = st.progress(0.0)

        # Initialize progress variables
        translated_chunks = []
        previous_chunk_context = ""
        dynamic_glossary = []
        
        graph = create_translation_graph()
        summary_llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, model=Config.MINI_MODEL, temperature=0)

        # Process each chunk
        for i, chunk_text in enumerate(chunks):
            progress_bar.progress((i) / len(chunks))
            
            with col_agents:
                st.write(f"👉 **Parça {i+1} / {len(chunks)} çevriliyor...**")

            initial_state = {
                "source_text": chunk_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "style_guide": DocumentProcessor.load_document(Config.get_genre_paths(genre)[0]) if Config.get_genre_paths(genre)[0].exists() else "",
                "glossary": json.loads(DocumentProcessor.load_document(Config.get_genre_paths(genre)[1])) if Config.get_genre_paths(genre)[1].exists() else [],
                "idioms": json.loads(DocumentProcessor.load_document(Config.IDIOMS_PATH)) if Config.IDIOMS_PATH.exists() else [],
                "style_analysis": None,
                "raw_translation": None,
                "stylized_translation": None,
                "critique": None,
                "is_approved": False,
                "revision_count": 0,
                "final_translation": None,
                "logs": [],
                "previous_chunk_context": previous_chunk_context,
                "dynamic_glossary": dynamic_glossary
            }

            current_log_index = 0
            final_translation = None

            # Stream graph execution and print step-by-step
            for output in graph.stream(initial_state):
                node_name = list(output.keys())[0]
                node_state = output[node_name]
                
                logs = node_state.get("logs", [])
                while current_log_index < len(logs):
                    log = logs[current_log_index]
                    agent_name = log["agent"]
                    action = log["action"]
                    content = log["output"]
                    
                    # Output log into Streamlit agent workspace
                    with agent_container:
                        emoji = "📝"
                        if "Analyst" in agent_name:
                            emoji = "🔍"
                        elif "Translator" in agent_name:
                            emoji = "⚙️"
                        elif "Stylist" in agent_name:
                            emoji = "✍️"
                        elif "Critic" in agent_name:
                            emoji = "🛡️"
                        elif "Polisher" in agent_name:
                            emoji = "✨"

                        with st.expander(f"{emoji} {agent_name} - {action}", expanded=("Critic" in agent_name or "Polisher" in agent_name)):
                            st.markdown(content)
                            
                    current_log_index += 1
                
                if "final_translation" in node_state and node_state["final_translation"]:
                    final_translation = node_state["final_translation"]

            # Fallback search for polished translation
            if not final_translation:
                for log in logs:
                    if log["agent"] == "Final Polisher":
                        final_translation = log["output"]

            if final_translation:
                translated_chunks.append(final_translation)
                
                # Update output area dynamically
                full_current_translation = "\n\n".join(translated_chunks)
                output_text_area.text_area("Çeviri Çıktısı", value=full_current_translation, height=500, disabled=True)
                
                # Generate summary for next page context
                try:
                    summary_prompt = f"Provide a brief 2-sentence summary in English of the following translated narrative to be used as context for translating the next section: {final_translation}"
                    previous_chunk_context = summary_llm.invoke(summary_prompt).content.strip()
                except:
                    previous_chunk_context = ""

        # Complete progress
        progress_bar.progress(1.0)
        st.success("🎉 Çeviri başarıyla tamamlandı!")
        
        # 4. Evaluation Module
        st.divider()
        st.subheader("📊 Otonom Kalite Değerlendirmesi (AI-as-a-Judge)")
        
        with st.spinner("Yapay zeka çeviri kalitesini değerlendiriyor..."):
            try:
                eval_source = full_text[:4000] + "\n... [truncated for evaluation] ...\n" + full_text[-4000:] if len(full_text) > 8000 else full_text
                eval_translation = full_current_translation[:4000] + "\n... [truncated for evaluation] ...\n" + full_current_translation[-4000:] if len(full_current_translation) > 8000 else full_current_translation
                
                evaluation = TranslationEvaluator.evaluate_translation(eval_source, eval_translation, genre=genre)
                
                # Render scores in columns
                score_col1, score_col2, score_col3 = st.columns(3)
                with score_col1:
                    st.metric(label="🎯 Doğruluk (Accuracy)", value=f"{evaluation['accuracy']} / 5")
                with score_col2:
                    st.metric(label="🌊 Akıcılık (Fluency)", value=f"{evaluation['fluency']} / 5")
                with score_col3:
                    st.metric(label="✏️ İmla & Terim Tutarlılığı", value=f"{evaluation['grammar']} / 5")
                
                st.markdown(f"### Detaylı Rapor\n{evaluation['summary']}")
            except Exception as e:
                st.warning(f"Kalite değerlendirmesi yapılamadı: {e}")

        # 5. Download Button
        st.download_button(
            label="Çeviriyi İndir (.txt) 📥",
            data=full_current_translation,
            file_name=f"translated_{Path(uploaded_file.name).stem}.txt",
            mime="text/plain"
        )
