"""Blind, paired English-to-Turkish book-translation comparison.

This deliberately compares the repository's CURRENT BookTranslationRunner
(default draft translator) against a direct LLM translation. It does not
claim to compare the full LangGraph/TIE workflow. No automatic LLM judge
or artificial quality score is presented as human evidence.
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from src.core.config import Config
from src.tie.book_runner import BookTranslationRunner, build_book_run_config


Translator = Callable[[str, dict[str, Any]], str]


def _response_text(response: Any) -> str:
    content = response.content
    if isinstance(content, str):
        value = content.strip()
    elif isinstance(content, list):
        value = "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()
    else:
        raise TypeError("Unexpected model response content type.")
    if not value:
        raise ValueError("Direct model returned an empty translation.")
    return value


class DirectLiteraryTranslator:
    """Provider-native direct translation without any other agent/critic."""

    def __init__(self, model: str, provider: str = "openai") -> None:
        if provider not in {"openai", "anthropic"}:
            raise ValueError("provider must be openai or anthropic")
        if not model.strip():
            raise ValueError("direct model ID cannot be empty")
        self.model = model
        self.provider = provider
        self._client: Any = None

    def _make_client(self) -> Any:
        if self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError as exc:
                raise RuntimeError(
                    "Claude requires: pip install langchain-anthropic"
                ) from exc
            return ChatAnthropic(model=self.model, max_tokens=4096)

        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=self.model,
        )

    def __call__(self, source: str, context: dict[str, Any]) -> str:
        if self._client is None:
            self._client = self._make_client()
        messages = [
            (
                "system",
                "You are a professional English-to-Turkish literary translator. "
                "Translate the complete supplied passage into natural, idiomatic "
                "Turkish. Preserve all meaning, imagery, narrative voice, "
                "character dialogue, ambiguity, and paragraph boundaries. "
                "Do not summarize, embellish, or omit anything. Return only "
                "the Turkish translation.",
            ),
            ("human", source),
        ]
        return _response_text(self._client.invoke(messages))


def _demo_legacy(source: str, context: dict[str, Any]) -> str:
    """Fixture-only stand-in. NOT a valid translation or quality test."""
    return "[DRY RUN - LEGACY] " + source


def _demo_direct(source: str, context: dict[str, Any]) -> str:
    """Fixture-only stand-in. NOT a valid translation or quality test."""
    return "[DRY RUN - DIRECT] " + source


def _load_run(result: Any) -> dict[str, Any]:
    metadata_path = result.output_paths["metadata_json"]
    if not metadata_path:
        raise ValueError("Runner metadata was not written.")
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    return {"result": result, "chunks": metadata["chunks"]}


def _make_blind_review(
    baseline_chunks: list[dict[str, Any]],
    direct_chunks: list[dict[str, Any]],
    seed: int,
    dry_run: bool,
) -> tuple[str, dict[str, str]]:
    names = ["baseline", "direct"]
    random.Random(seed).shuffle(names)
    labels = {"A": names[0], "B": names[1]}
    lines = [
        "# Blind EN → TR translation review",
        "",
        "Read the source and both translations before choosing. "
        "Score meaning fidelity, naturalness, and literary voice from 1–5.",
        "Do not open answer_key.json until all preferences are recorded.",
        "",
    ]
    if dry_run:
        lines += [
            "**DRY RUN ONLY: The candidates below are synthetic placeholders, not translations.**",
            "",
        ]
    for index, (base, direct) in enumerate(
        zip(baseline_chunks, direct_chunks), start=1
    ):
        translations = {
            "baseline": base["translation"],
            "direct": direct["translation"],
        }
        lines.extend([
            f"## Passage {index:03d}",
            "",
            "### Original (English)",
            "",
            base["source_text"],
            "",
            "### Candidate A",
            "",
            translations[labels["A"]],
            "",
            "### Candidate B",
            "",
            translations[labels["B"]],
            "",
            "### Human evaluation",
            "",
            "- Accuracy (A/B; 1–5): ___ / ___",
            "- Natural Turkish (A/B; 1–5): ___ / ___",
            "- Literary voice (A/B; 1–5): ___ / ___",
            "- Preference (A / B / tie): ___",
            "- Meaning lost, added, or distorted: ___",
            "",
            "---",
            "",
        ])
    return "\n".join(lines), labels


def run_novel_ab(
    input_path: str | Path,
    *,
    model: Optional[str] = None,
    provider: str = "openai",
    first_words: int = 1000,
    chunk_chars: int = 3200,
    output_root: str | Path = "outputs/novel_ab",
    seed: int = 42,
    start_at: str = "body",
    dry_run: bool = False,
    baseline_translator: Optional[Translator] = None,
    direct_translator: Optional[Translator] = None,
) -> dict[str, Any]:
    """Execute the same selected input twice, then create a blinded review pack.

    Optional injected translators exist for offline tests only. They make no
    claim about the quality or relative performance of real models.
    """
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if first_words < 1 or chunk_chars < 100:
        raise ValueError("first_words >= 1 and chunk_chars >= 100 required.")
    if start_at not in {"body", "beginning"}:
        raise ValueError("start_at must be body or beginning.")

    challenger_model = model or Config.MAIN_MODEL
    run_id = "novel_ab_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    destination = Path(output_root) / run_id
    destination.mkdir(parents=True, exist_ok=False)

    if dry_run:
        baseline_translator = baseline_translator or _demo_legacy
        direct_translator = direct_translator or _demo_direct
    elif direct_translator is None:
        direct_translator = DirectLiteraryTranslator(challenger_model, provider)

    runs: dict[str, dict[str, Any]] = {}
    for name, translator in [
        ("baseline", baseline_translator),
        ("direct", direct_translator),
    ]:
        config = build_book_run_config(
            input_path=str(source),
            target_language="tr",
            source_language="en",
            first_words=first_words,
            chunk_chars=chunk_chars,
            tm_enabled=False,
            output_root=str(destination / name),
            write_pdf=False,
            write_markdown=True,
            write_side_by_side=False,
            write_quality_report=True,
            write_metadata=True,
            start_at=start_at,
            include_front_matter=start_at == "beginning",
            exclude_toc=start_at != "beginning",
        )
        began = time.monotonic()
        run_result = BookTranslationRunner(translator=translator).run(config)
        elapsed = time.monotonic() - began
        loaded = _load_run(run_result)
        loaded["elapsed_seconds"] = round(elapsed, 3)
        runs[name] = loaded

    baseline_chunks = runs["baseline"]["chunks"]
    direct_chunks = runs["direct"]["chunks"]
    if not baseline_chunks or len(baseline_chunks) != len(direct_chunks):
        raise RuntimeError("Cannot compare runs: chunk counts differ.")
    if [c["source_text"] for c in baseline_chunks] != [
        c["source_text"] for c in direct_chunks
    ]:
        raise RuntimeError("Cannot compare runs: source chunks differ.")

    review, answer_key = _make_blind_review(
        baseline_chunks, direct_chunks, seed, dry_run
    )
    (destination / "blind_review.md").write_text(review, encoding="utf-8")
    (destination / "answer_key.json").write_text(
        json.dumps(answer_key, indent=2), encoding="utf-8"
    )

    report: dict[str, Any] = {
        "status": "dry_run_no_model_calls" if dry_run else "awaiting_human_review",
        "purpose": "Current Book Runner default vs direct single-model translation",
        "full_langgraph_tie_included": False,
        "source_file": source.name,
        "first_words": first_words,
        "chunk_chars": chunk_chars,
        "seed": seed,
        "passages": len(baseline_chunks),
        "baseline_model": (
            "stub" if dry_run else
            ("injected test translator" if baseline_translator else Config.MINI_MODEL)
        ),
        "direct_model": (
            "stub" if dry_run else
            ("injected test translator" if direct_translator and not isinstance(
                direct_translator, DirectLiteraryTranslator
            ) else challenger_model)
        ),
        "direct_provider": provider,
        "arms": {},
        "quality_conclusion": (
            "No model quality can be inferred from a dry run."
            if dry_run else
            "No winner until blind human review; QA flags are not scores."
        ),
    }
    for name in ("baseline", "direct"):
        result = runs[name]["result"]
        report["arms"][name] = {
            "elapsed_seconds": runs[name]["elapsed_seconds"],
            "source_words": result.source_words,
            "target_words": result.target_words,
            "chunks": result.chunks_translated,
            "quality_guardrail": result.recommendation,
            "flagged_chunks": sum(
                chunk["quality_gate"]["recommendation"] != "accept"
                for chunk in runs[name]["chunks"]
            ),
            "metadata_path": str(result.output_paths["metadata_json"]),
        }
    (destination / "comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report["output_dir"] = str(destination)
    report["blind_review_file"] = str(destination / "blind_review.md")
    report["answer_key_file"] = str(destination / "answer_key.json")
    return report
