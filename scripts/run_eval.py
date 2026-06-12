import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core.evaluator import TranslationEvaluator
from src.observability.mlflow_tracker import mlflow_tracker
from rich.console import Console

console = Console()

def run_evaluations():
    eval_file = PROJECT_ROOT / "data" / "eval" / "sample_translation_cases.json"
    
    if not eval_file.exists():
        console.print(f"[bold red]Evaluation file not found: {eval_file}[/bold red]")
        sys.exit(1)
        
    with open(eval_file, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    console.print(f"[bold blue]Loaded {len(cases)} evaluation cases.[/bold blue]\n")
    
    for case in cases:
        console.print(f"[bold]Evaluating Case: {case['id']} ({case['genre']})[/bold]")
        
        for version in ["v1", "v2"]:
            translation_key = f"translation_{version}"
            translation_text = case[translation_key]
            
            console.print(f"  [dim]Evaluating {translation_key}...[/dim]")
            
            # Run AI Judge
            try:
                evaluation = TranslationEvaluator.evaluate_translation(
                    source_text=case["source"],
                    translated_text=translation_text,
                    genre=case["genre"]
                )
                
                # Log to MLflow
                run_name = f"eval_{case['id']}_{version}"
                mlflow_tracker.log_translation_experiment(
                    run_name=run_name,
                    params={
                        "evaluation_type": "comparison",
                        "case_id": case["id"],
                        "version": version,
                        "genre": case["genre"]
                    },
                    metrics={
                        "accuracy": float(evaluation['accuracy']),
                        "fluency": float(evaluation['fluency']),
                        "grammar": float(evaluation['grammar']),
                        "consistency": float(evaluation.get('consistency', 0.0))
                    }
                )
                
                console.print(f"  [green]Result for {version}: Acc {evaluation['accuracy']}/5, Fluency {evaluation['fluency']}/5, Grammar {evaluation['grammar']}/5[/green]")
            except Exception as e:
                console.print(f"  [red]Failed to evaluate {version}: {e}[/red]")
                
        console.print("-" * 40)
        
    console.print("[bold green]Evaluations complete! Check MLflow to see the comparisons.[/bold green]")

if __name__ == "__main__":
    # Ensure MLflow is enabled before running
    from src.core.config import Config
    if not Config.ENABLE_MLFLOW:
        console.print("[bold yellow]MLflow tracking is disabled. Enable it in .env to record metrics.[/bold yellow]")
        
    run_evaluations()
