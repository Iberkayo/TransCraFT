# TransCraft 🔮

**TransCraft** is a production-grade, autonomous **Multi-Agent Translation & Localization Engine** designed to produce high-fidelity, publishing-quality translations of complex literary and technical documents (PDFs & TXTs). 

Rather than executing dry, word-by-word machine translations, TransCraft orchestrates a collaborative graph of specialized AI agents that analyze, translate, stylize, audit, and polish content dynamically.

---

## 🚀 Key Features

*   **Multi-Agent Collaborative Graph:** Powered by **LangGraph**, it coordinates 5 specialized agents in a self-correcting feedback loop (Critic-Stylist revision cycles).
*   **Smart Semantic Chunking:** Splits large PDF and TXT documents into optimal chunks without breaking paragraphs or sentences.
*   **Stateful Translation Memory:** Preserves narrative continuity across pages using running context summaries and a dynamic glossary.
*   **Domain & Genre Routing:** Automatically loads specific dictionaries and style guides depending on the genre (`tech` vs. `literary`).
*   **Resumable Progress Checkpoints:** Saves translation state to a recovery file after every chunk, preventing token loss in case of interruptions.
*   **AI-as-a-Judge Evaluation:** Runs an autonomous quality audit evaluating the output on *Accuracy*, *Fluency*, and *Grammar* (1-5 scale).
*   **Dual Interfaces:** Includes a rich terminal command-line tool (CLI) and an interactive **Streamlit Web UI**.
*   **FastAPI Microservice Mode:** Can be spun up as an API server for backend integrations.

---

## 🏢 Enterprise Localization Features

To ensure terminology consistency and publisher-level quality across large documents, TransCraft implements a robust layer of localization workflows:
*   **Terminology Extraction Agent:** Analyzes the document *before* translation starts, identifying repeated technical terms and acronyms to create auto-glossary candidates. Features a fail-safe, regex-based fallback extraction if LLM formatting limits are hit.
*   **Strict Glossary Hierarchy:** Enforces a rigid priority system during translation: **Positive Glossary** (User mandatory) > **Dynamic Auto-Glossary** > **Standard Glossary** > **Negative Glossary** (Forbidden terms).
*   **Consistency Checker Agent:** A post-processing auditor that scans the *entire* translated document to ensure 100% terminology adherence, style consistency, and flags any un-translated English fragments.
*   **Genre & Style Presets:** Decouples structural rules (genre) from linguistic flavor (style). Easily apply presets like `classic_literary`, `academic_technical`, or `publisher_editor`.
*   **Native PDF Rendering:** Generates professional-looking PDF outputs that fully support native characters (e.g. Turkish `ş, ç, ğ`) directly from the Web UI.

---

## 🧠 Translation Intelligence Engine (TIE) v0.1 (MVP)

TransCraft features a model-independent **Translation Intelligence Engine (TIE)** layer that accumulates reusable translation knowledge across translation runs.

*   **Memory Layers (`memory/`):** Organized into `global/` (idioms, phrasing patterns), `genres/` (genre-specific heuristics), `works/` (character info, glossary, and style profiles), and `users/` (user preferences).
*   **Context Router:** Analyzes translation metadata (user, genre, work) before execution to retrieve relevant memories and inject a compact context block into agent prompts.
*   **Memory Curator Agent:** Observes the translation lifecycle (source, draft, critique, final polish) at the end of translation chunks to extract new terminology, proper nouns, corrections, and style choices. Employs a regex-based heuristic fallback if the LLM is unavailable.
*   **Handoff Generator:** Generates a reusable `translation_handoff.md` summarizing characters, active glossary, style rules, key decisions, and known pitfalls for continuing translation with other models.

To run with TIE enabled:
```bash
python main.py --input data/inputs/literary_english.txt --enable-tie --user berkay --work blood_meridian --generate-handoff
```

---

## 🤖 The Multi-Agent Architecture

```
                       [Input Document]
                              │
                              ▼
                [ 0. Terminology Extractor ]
                              │
                              ▼
               [ 1. Style & Culture Analyst ]
                              │
                              ▼
                [ 2. First-Pass Translator ]
                              │
                              ▼
                  [ 3. Cultural Stylist ] ◄─────┐
                              │                 │ (If rejected,
                              ▼                 │  loops back)
                   [ 4. Translation Critic ] ───┘
                              │
                              ▼ (If approved)
                   [ 5. Final Copy-Editor ]
                              │
                              ▼
               [ 6. Enterprise Consistency Checker ]
                              │
                              ▼
                       [Polished Output]
```

*   **Terminology Extractor:** Pre-processes the document to generate an auto-glossary of domain-specific terminology.
*   **Style & Culture Analyst:** Profiles the text's tone, registers idioms, and maps vocabulary.
*   **First-Pass Translator:** Conducts literal and semantic translation preserving facts and terminology, adhering strictly to the Glossary Hierarchy.
*   **Cultural Stylist:** Rewrites the draft to sound completely natural in the target language.
*   **Translation Critic:** Performs comparative analysis, audits terminology, and requests revisions if criteria aren't met.
*   **Final Polisher:** Inspects grammar, punctuation, and format encoding.
*   **Consistency Checker:** Audits the fully assembled text for global terminology and stylistic consistency.

---

## ⚙️ Setup & Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Iberkayo/TransCraFT.git
    cd TransCraFT
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment Variables:**
    Copy the env template and enter your OpenAI API key:
    ```bash
    cp .env.example .env
    # Edit the .env file with your OPENAI_API_KEY
    ```

---

## 💻 How to Run

### 1. Interactive Web Playground (Streamlit)
To launch the visual browser interface (allows file uploads, real-time agent trace logs, and dynamic translation progress):
```bash
streamlit run app.py
```

### 2. Command Line Interface (CLI)
Translate files directly in the terminal with colored logs:
*   **Literary/General texts:**
    ```bash
    python main.py --input data/inputs/literary_english.txt --genre literary
    ```
*   **Technical/AI Research papers:**
    ```bash
    python main.py --input data/inputs/1706.03762v7.pdf --genre tech --chunk-size 5000
    ```

### 3. FastAPI Microservice
Run TransCraft as a background translation server:
```bash
python main.py --server --port 8000
```
*   **Translation Endpoint:** `POST http://127.0.0.1:8000/translate` (form-data: `file`, `genre`, `source_lang`, `target_lang`)
*   **Health Status:** `GET http://127.0.0.1:8000/status`

---

## 🔍 Observability & Experiment Tracking

TransCraft integrates **Langfuse** and **MLflow** to provide production-grade monitoring for its multi-agent system. 

### Why this matters in production GenAI systems
In enterprise GenAI applications, especially multi-agent architectures, silent failures (like hallucinations, repetitive loops, or prompt drift) are common. 
- **Langfuse** gives us x-ray vision into the *execution state* of every LangGraph node (e.g., exactly what the Critic agent said to the Stylist agent, how many tokens were used, and step-by-step latency). 
- **MLflow** allows us to quantitatively measure *translation quality* over time across different experiments (e.g., testing `gpt-4o-mini` vs `gpt-4o` prompts to see which yields higher AI-as-a-Judge scores).

### 🛠️ What is Tracked?
*   **Langfuse (Tracing):** Agent executions, chunk indices, revision loops, raw inputs/outputs per agent, exact LLM prompts, token usage, and latency.
*   **MLflow (Experimentation):** Hyperparameters (chunk size, model, genre), metrics (AI-as-a-Judge Accuracy, Fluency, Grammar scores, total latency), and generated artifact files.

### 🔌 How to Enable/Disable
Both tools are completely optional and fail safely if unavailable. Enable them in your `.env`:
```env
ENABLE_LANGFUSE=true
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

ENABLE_MLFLOW=true
MLFLOW_TRACKING_URI=./mlruns
MLFLOW_EXPERIMENT_NAME=transcraft_translation_quality
```

### 🧪 Run an Evaluation Experiment
You can automatically evaluate and compare different prompt versions or models using the evaluation script:
```bash
python scripts/run_eval.py
```
After running translations or evaluations, open the MLflow UI to view the dashboards:
```bash
mlflow ui
```

---

## 🧪 Unit Testing

To run the Pytest verification suite:
```bash
python -m pytest tests/
```
