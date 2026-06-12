import argparse
import json
import sys
import io
from pathlib import Path

# Enforce UTF-8 encoding for Windows terminals to prevent UnicodeEncodeError on emojis
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from langchain_openai import ChatOpenAI

# Setup path and imports
sys.path.append(str(Path(__file__).resolve().parent))
from src.core.config import Config
from src.core.graph import create_translation_graph
from src.core.document_processor import DocumentProcessor
from src.core.evaluator import TranslationEvaluator
from src.observability.langfuse_tracker import tracker
from src.observability.mlflow_tracker import mlflow_tracker
import time

# Initialize Rich console with custom theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "agent_header": "bold royal_blue1",
    "accent": "bold gold1"
})
console = Console(theme=custom_theme)

def load_text_file(path: Path) -> str:
    """Load text file content safely."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        console.print(f"[danger]Error loading file {path}: {e}[/danger]")
        sys.exit(1)

def load_json_file(path: Path, default: any = None) -> any:
    """Load JSON file content safely."""
    if not path.exists():
        return default or []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[warning]Warning: Could not parse {path} ({e}). Using default.[/warning]")
        return default or []

def main():
    parser = argparse.ArgumentParser(description="TransCraft: Autonomous Multi-Agent Literary & Cultural Translation System")
    parser.add_argument("--input", "-i", type=str, help="Path to the source text file (.pdf or .txt)")
    parser.add_argument("--source-lang", "-s", type=str, default="English", help="Source language")
    parser.add_argument("--target-lang", "-t", type=str, default="Turkish", help="Target language")
    parser.add_argument("--chunk-size", "-c", type=int, default=3000, help="Max characters per chunk")
    parser.add_argument("--genre", "-g", type=str, choices=["literary", "tech"], default="literary", help="Genre of the text (literary, tech)")
    parser.add_argument("--style", "-st", type=str, choices=["modern_turkish", "classic_literary", "childrens_book", "academic_technical", "publisher_editor"], default="modern_turkish", help="Style preset to apply")
    parser.add_argument("--server", action="store_true", help="Start the FastAPI translation microservice server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address for the server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the server")
    args = parser.parse_args()

    # Welcome Banner
    console.print("\n" + "="*80, style="accent")
    console.print(Panel(
        "[accent]TRANSCRAFT[/accent] :sparkles: [bold white]Multi-Agent Literary & Cultural Translation Console[/bold white]\n"
        "[dim]An elegant, autonomous translation workflow powered by LangGraph & OpenAI[/dim]",
        border_style="accent",
        expand=False
    ))
    console.print("="*80 + "\n", style="accent")

    # 1. Config Validation
    try:
        Config.validate()
    except ValueError as e:
        console.print(f"[danger]Configuration Error:[/danger] {e}")
        console.print("[warning]Please create a '.env' file in the project root and insert your OPENAI_API_KEY.[/warning]")
        sys.exit(1)

    # 1.5 Handle Server Mode
    if args.server:
        console.print(f"[success]🚀 Starting FastAPI Translation Server on http://{args.host}:{args.port}...[/success]\n")
        from src.core.server import start_server
        try:
            start_server(host=args.host, port=args.port)
        except Exception as e:
            console.print(f"[danger]Server failed to start:[/danger] {e}")
        sys.exit(0)

    # Verify input exists if not running server
    if not args.input:
        parser.error("the following arguments are required: --input/-i (unless running with --server)")

    input_path = Path(args.input)
    if not input_path.exists():
        console.print(f"[danger]Error:[/danger] Input file not found at '{input_path}'")
        sys.exit(1)

    # 2. Setup Resources
    console.print("[info]Loading resources and initializing language models...[/info]")
    
    _, glossary_path = Config.get_genre_paths(args.genre)
    style_guide_path = Config.get_style_path(args.style)
    
    style_guide = load_text_file(style_guide_path)
    glossary = load_json_file(glossary_path, default=[])
    idioms = load_json_file(Config.IDIOMS_PATH, default=[])
    
    # Load Negative Glossary
    negative_glossary_path = Config.REFERENCE_DIR / "yanlis_ceviriler.json"
    negative_glossary = load_json_file(negative_glossary_path, default={})

    # Load Positive Glossary
    positive_glossary_path = Config.REFERENCE_DIR / "positive_glossary.json"
    positive_glossary = load_json_file(positive_glossary_path, default={})
        
    console.print(f"[info]Loading and chunking document: {input_path}...[/info]")
    
    # Load and split document using smart chunker
    try:
        full_text = DocumentProcessor.load_document(input_path)
        chunks = DocumentProcessor.smart_chunk_text(full_text, max_chunk_size=args.chunk_size)
    except Exception as e:
        console.print(f"[danger]Error processing document: {e}[/danger]")
        sys.exit(1)

    console.print(f"[success]Loaded {len(chunks)} chunk(s) from document.[/success]")

    # Dynamic path resolution based on genre
    style_guide_path, glossary_path = Config.get_genre_paths(args.genre)
    console.print(f"[info]Loading style guide and glossary for genre: [accent]{args.genre}[/accent]...[/info]")
    
    style_guide = load_text_file(style_guide_path) if style_guide_path.exists() else "Default literary translation rules."
    glossary = load_json_file(glossary_path, default=[])
    idioms = load_json_file(Config.IDIOMS_PATH, default=[])
    
    # 3. Recovery / Resume Setup
    output_dir = Config.DATA_DIR / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    recovery_file = output_dir / f"recovery_{input_path.stem}.json"
    
    translated_chunks = []
    dynamic_glossary = []
    previous_chunk_context = ""
    start_chunk_index = 0
    
    if recovery_file.exists():
        try:
            with open(recovery_file, "r", encoding="utf-8") as rf:
                recovery_data = json.load(rf)
                translated_chunks = recovery_data.get("translated_chunks", [])
                dynamic_glossary = recovery_data.get("dynamic_glossary", [])
                previous_chunk_context = recovery_data.get("previous_chunk_context", "")
                start_chunk_index = len(translated_chunks)
                console.print(f"[warning]Found active recovery file. Resuming from Chunk {start_chunk_index + 1}/{len(chunks)}...[/warning]\n")
        except Exception as e:
            console.print(f"[warning]Warning: Could not parse recovery file ({e}). Starting fresh.[/warning]")

    # 4. Initialize Graph & Models
    graph = create_translation_graph()
    summary_llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.MINI_MODEL,
        temperature=0
    )

    # Initialize Langfuse Trace for this file
    run_name = f"translation_{input_path.stem}"
    trace_id = tracker.create_trace(
        name=run_name,
        metadata={
            "input_filename": input_path.name,
            "genre": args.genre,
            "source_lang": args.source_lang,
            "target_lang": args.target_lang,
            "chunk_size": args.chunk_size
        }
    )
    start_time = time.time()

    # 5. Process each chunk
    for i in range(start_chunk_index, len(chunks)):
        chunk_text = chunks[i]
        console.print(f"\n[accent]>>> Translating Chunk {i+1} of {len(chunks)}[/accent] ({len(chunk_text)} characters)...")
        
        initial_state = {
            "source_text": chunk_text,
            "source_language": args.source_lang,
            "target_language": args.target_lang,
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
            "dynamic_glossary": dynamic_glossary,
            "trace_id": trace_id,
            "chunk_index": i
        }

        current_log_index = 0
        final_translation = None
        
        # Stream the graph execution for console logs
        for output in graph.stream(initial_state):
            node_name = list(output.keys())[0]
            node_state = output[node_name]
            
            logs = node_state.get("logs", [])
            while current_log_index < len(logs):
                log = logs[current_log_index]
                agent_name = log["agent"]
                action = log["action"]
                content = log["output"]
                
                # Render logs beautifully
                panel_title = f"[agent_header]🤖 {agent_name}[/agent_header] - [dim]{action}[/dim]"
                
                if "Critic" in agent_name:
                    border_color = "success" if "Approved: True" in content else "warning"
                elif "Polisher" in agent_name:
                    border_color = "accent"
                else:
                    border_color = "royal_blue1"
                
                # For large books, we minimize logging of raw translation but keep stylist and critic logs
                if "Draft Translator" in agent_name:
                    # Keep it tiny
                    console.print(f"[info]... {agent_name} generated raw draft.[/info]")
                else:
                    console.print(Panel(
                        Markdown(content),
                        title=panel_title,
                        title_align="left",
                        border_style=border_color,
                        padding=(1, 2)
                    ))
                
                current_log_index += 1
                
            # Extract polished translation once done
            if "final_translation" in node_state and node_state["final_translation"]:
                final_translation = node_state["final_translation"]

        # Double check we have the translation
        if not final_translation:
            # Fallback check from logs
            for log in logs:
                if log["agent"] == "Final Polisher":
                    final_translation = log["output"]

        if not final_translation:
            console.print(f"[danger]Error: Chunk {i+1} failed to translate.[/danger]")
            sys.exit(1)

        # Generate summary of the translated chunk for the next page's context
        console.print("[info]Generating context summary for the next chunk...[/info]")
        try:
            summary_prompt = f"Provide a brief 2-sentence summary in English of the following translated narrative to be used as context for translating the next section: {final_translation}"
            previous_chunk_context = summary_llm.invoke(summary_prompt).content.strip()
        except Exception as e:
            console.print(f"[warning]Could not generate context summary: {e}[/warning]")
            previous_chunk_context = ""

        # Save chunk result
        translated_chunks.append(final_translation)
        
        # Save recovery file state
        try:
            recovery_data = {
                "input_file": str(input_path),
                "translated_chunks": translated_chunks,
                "dynamic_glossary": dynamic_glossary,
                "previous_chunk_context": previous_chunk_context
            }
            with open(recovery_file, "w", encoding="utf-8") as rf:
                json.dump(recovery_data, rf, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[warning]Failed to save recovery checkpoint: {e}[/warning]")

    # 6. Final Assemble & Clean Up
    console.print("\n[accent]>>> Assembling final translation...[/accent]")
    full_translation = "\n\n".join(translated_chunks)
    
    # Save final output
    if input_path.suffix.lower() == ".pdf":
        output_file = output_dir / f"translated_{input_path.stem}.txt"
    else:
        output_file = output_dir / f"translated_{input_path.name}"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_translation)
        console.print(f"[success]🎉 Translation completed! Saved to:[/success] [accent]{output_file.absolute()}[/accent]\n")
        
        # Delete recovery file upon successful completion
        if recovery_file.exists():
            recovery_file.unlink()
            
        # 6.5 Consistency Checker Post-Process
        console.print("[bold yellow]Running Enterprise Consistency Checker...[/bold yellow]\n")
        from src.agents.consistency_checker import run_consistency_check
        consistency_report = run_consistency_check(full_text, full_translation, positive_glossary)
        
        if consistency_report.get("issues_found", 0) > 0:
            console.print(f"[warning]Found {consistency_report['issues_found']} potential inconsistencies.[/warning]")
            for issue in consistency_report.get("issues", []):
                console.print(f"  - [dim]{issue['type']}:[/dim] {issue['description']}")
                
        if consistency_report.get("glossary_candidates"):
            console.print(f"[info]Extracted {len(consistency_report['glossary_candidates'])} terminology recommendations.[/info]")
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
            except Exception as e:
                pass
            
        # 7. Run AI Quality Evaluation
        console.print("[bold yellow]Running AI-as-a-Judge Quality Evaluation...[/bold yellow]\n")
        try:
            # Optimize text length for evaluation to prevent token overflow
            eval_source = full_text[:4000] + "\n... [truncated for evaluation] ...\n" + full_text[-4000:] if len(full_text) > 8000 else full_text
            eval_translation = full_translation[:4000] + "\n... [truncated for evaluation] ...\n" + full_translation[-4000:] if len(full_translation) > 8000 else full_translation
            
            evaluation = TranslationEvaluator.evaluate_translation(eval_source, eval_translation, genre=args.genre)
            
            # Print evaluation report beautifully
            scores_str = f"⭐ [success]Doğruluk (Accuracy):[/success] {evaluation['accuracy']}/5 | " \
                         f"⭐ [success]Akıcılık (Fluency):[/success] {evaluation['fluency']}/5 | " \
                         f"⭐ [success]İmla (Grammar):[/success] {evaluation['grammar']}/5 | " \
                         f"⭐ [success]Tutarlılık (Consistency):[/success] {evaluation['consistency']}/5"
                         
            console.print(Panel(
                f"{scores_str}\n\n[bold white]Overall Quality Score:[/bold white] {evaluation['overall_score']:.1f}/5.0\n\n{evaluation['summary']}",
                title="[accent]📊 OTONOM KALİTE DEĞERLENDİRME RAPORU (AI Evaluation) 📊[/accent]",
                border_style="accent",
                padding=(1, 2)
            ))
            console.print("\n")

            # 8. Log Experiment to MLflow
            end_time = time.time()
            mlflow_tracker.log_translation_experiment(
                run_name=run_name,
                params={
                    "model": Config.MAIN_MODEL,
                    "style": args.style,
                    "genre": args.genre,
                    "source_lang": args.source_lang,
                    "target_lang": args.target_lang,
                    "chunk_size": args.chunk_size,
                    "num_chunks": len(chunks)
                },
                metrics={
                    "accuracy": float(evaluation['accuracy']),
                    "fluency": float(evaluation['fluency']),
                    "grammar": float(evaluation['grammar']),
                    "total_latency_seconds": end_time - start_time
                },
                artifacts={"output_file": str(output_file.absolute())}
            )
            tracker.flush()

        except Exception as e:
            console.print(f"[warning]AI Quality Evaluation failed: {e}[/warning]\n")
    except Exception as e:
        console.print(f"[danger]Failed to save final output or delete recovery file: {e}[/danger]")

if __name__ == "__main__":
    main()
