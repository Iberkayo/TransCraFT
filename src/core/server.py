import json
import tempfile
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import project components
from src.core.config import Config
from src.core.graph import create_translation_graph
from src.core.document_processor import DocumentProcessor
from src.core.evaluator import TranslationEvaluator
from langchain_openai import ChatOpenAI

app = FastAPI(
    title="TransCraft Translation API",
    description="Autonomous Multi-Agent Translation Engine Microservice",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    api_configured: bool

@app.get("/status", response_model=HealthResponse)
def get_status():
    """Verify that the translation engine API is healthy and configured."""
    return {
        "status": "ok",
        "api_configured": bool(Config.OPENAI_API_KEY)
    }

@app.post("/translate")
async def translate_document(
    file: UploadFile = File(...),
    genre: str = Form("literary"),
    source_lang: str = Form("English"),
    target_lang: str = Form("Turkish"),
    chunk_size: int = Form(3000)
):
    """
    Upload a document (.pdf or .txt) and translate it asynchronously.
    Returns the final translated text and the quality evaluation report.
    """
    # 1. Validation
    if not Config.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API Key is not configured on the server.")
        
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".txt", ".pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only .pdf and .txt are supported.")

    # 2. Write uploaded file to temp path
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    try:
        # Load and chunk text
        full_text = DocumentProcessor.load_document(tmp_path)
        chunks = DocumentProcessor.smart_chunk_text(full_text, max_chunk_size=chunk_size)
        
        # Load style guide and glossary based on genre
        style_guide_path, glossary_path = Config.get_genre_paths(genre)
        style_guide = DocumentProcessor.load_document(style_guide_path) if style_guide_path.exists() else ""
        glossary = []
        if glossary_path.exists():
            with open(glossary_path, "r", encoding="utf-8") as gf:
                glossary = json.load(gf)
        
        # Load idioms list
        idioms = []
        if Config.IDIOMS_PATH.exists():
            with open(Config.IDIOMS_PATH, "r", encoding="utf-8") as ifile:
                idioms = json.load(ifile)

        graph = create_translation_graph()
        summary_llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, model=Config.MINI_MODEL, temperature=0)

        translated_chunks = []
        previous_chunk_context = ""
        dynamic_glossary = []

        # Run translation loop
        for i, chunk_text in enumerate(chunks):
            initial_state = {
                "source_text": chunk_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "style_guide": style_guide,
                "glossary": glossary,
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
                "dynamic_glossary": dynamic_glossary
            }

            # Run graph to completion
            final_state = graph.invoke(initial_state)
            
            # Extract output
            final_translation = final_state.get("final_translation")
            if not final_translation:
                # Search logs as fallback
                for log in final_state.get("logs", []):
                    if log["agent"] == "Final Polisher":
                        final_translation = log["output"]
            
            if not final_translation:
                raise ValueError(f"Failed to translate chunk {i+1}")

            translated_chunks.append(final_translation)

            # Generate context summary for next chunk
            try:
                summary_prompt = f"Provide a brief 2-sentence summary in English of the following translated narrative to be used as context for translating the next section: {final_translation}"
                previous_chunk_context = summary_llm.invoke(summary_prompt).content.strip()
            except:
                previous_chunk_context = ""

        # Assemble full text
        full_translation = "\n\n".join(translated_chunks)

        # Run evaluation
        eval_source = full_text[:4000] + "\n... [truncated] ...\n" + full_text[-4000:] if len(full_text) > 8000 else full_text
        eval_translation = full_translation[:4000] + "\n... [truncated] ...\n" + full_translation[-4000:] if len(full_translation) > 8000 else full_translation
        
        evaluation_report = TranslationEvaluator.evaluate_translation(eval_source, eval_translation, genre=genre)

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_processed": len(chunks),
            "translated_text": full_translation,
            "evaluation": evaluation_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation pipeline error: {str(e)}")
        
    finally:
        # Clean up temp file safely
        if tmp_path.exists():
            os.unlink(tmp_path)

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start uvicorn server programmatically."""
    import uvicorn
    uvicorn.run("src.core.server:app", host=host, port=port, reload=False)
