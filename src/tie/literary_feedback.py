"""TIE v0.9.4 — Literary Human Correction Feedback + Fix Suggestion Layer.

Loads Berkay's human correction dataset and generates structured
suggestions for literary translation review. Never auto-applies corrections.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CORRECTIONS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "eval" / "blood_meridian_first5_human_corrections.json"


class LiteraryCorrectionFeedbackStore:
    """Load and query Berkay's literary human correction dataset."""

    def __init__(self, corrections_path: Optional[Path] = None):
        self.corrections_path = corrections_path or DEFAULT_CORRECTIONS_PATH
        self.corrections: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.corrections_path.exists():
            data = json.loads(self.corrections_path.read_text(encoding="utf-8"))
            self.corrections = data if isinstance(data, list) else []

    def reload(self) -> None:
        self._load()

    def find_by_source(self, source_phrase: str) -> List[Dict[str, Any]]:
        """Find corrections matching a source phrase (case-insensitive substring)."""
        lower = source_phrase.casefold()
        return [c for c in self.corrections if c.get("source_phrase", "").casefold() in lower]

    def find_by_current_target(self, target_text: str) -> List[Dict[str, Any]]:
        """Find corrections matching a current target text fragment."""
        lower = target_text.casefold()
        return [c for c in self.corrections if c.get("current_target", "").casefold() in lower]

    def find_in_text(self, turkish_text: str) -> List[Dict[str, Any]]:
        """Find corrections whose current_target appears in the given Turkish text."""
        lower = turkish_text.casefold()
        return [c for c in self.corrections if c.get("current_target", "").casefold() in lower]

    def critical_count(self) -> int:
        return sum(1 for c in self.corrections if c.get("severity") == "critical")

    def major_count(self) -> int:
        return sum(1 for c in self.corrections if c.get("severity") == "major")

    def minor_count(self) -> int:
        return sum(1 for c in self.corrections if c.get("severity") == "minor")


class LiterarySuggestionGenerator:
    """Generate structured suggestions from correction dataset without auto-applying them."""

    def __init__(self, store: Optional[LiteraryCorrectionFeedbackStore] = None):
        self.store = store or LiteraryCorrectionFeedbackStore()

    def generate_suggestions(
        self,
        source_text: str = "",
        translated_text: str = "",
    ) -> Dict[str, Any]:
        """Generate suggestions for a translated chunk, never auto-applying."""
        suggestions: List[Dict[str, Any]] = []

        for correction in self.store.corrections:
            current_target = correction.get("current_target", "")
            if current_target.casefold() in translated_text.casefold():
                suggestions.append({
                    "correction_id": correction["id"],
                    "source_phrase": correction["source_phrase"],
                    "current_target": correction["current_target"],
                    "suggested_target": correction["suggested_target"],
                    "severity": correction["severity"],
                    "reason": correction["reason"],
                    "apply_mode": correction.get("apply_mode", "suggest_only"),
                    "tags": correction.get("tags", []),
                })

        critical = sum(1 for s in suggestions if s["severity"] == "critical")
        major = sum(1 for s in suggestions if s["severity"] == "major")
        minor = sum(1 for s in suggestions if s["severity"] == "minor")

        recommendation = "accept"
        if critical > 0:
            recommendation = "review"
        elif major > 2:
            recommendation = "review"
        elif minor > 5:
            recommendation = "review"

        return {
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
            "critical_suggestions": critical,
            "major_suggestions": major,
            "minor_suggestions": minor,
            "recommendation": recommendation,
        }

    def generate_edit_file(self, output_path: Path, translated_text: str = "") -> Path:
        """Generate a human-readable suggested edits markdown file."""
        result = self.generate_suggestions(translated_text=translated_text)
        suggestions = result["suggestions"]

        lines = ["# Blood Meridian — Suggested Edits (Human Review Required)", ""]
        lines.append("This is human correction feedback infrastructure, not automatic proof of literary quality.")
        lines.append("Suggestions require human review before application. Do not auto-apply.")
        lines.append("")
        lines.append("| Source Phrase | Current Target | Suggested Target | Severity | Reason | Reviewer Decision |")
        lines.append("| ------------- | ------------- | --------------- | -------- | ------ | ----------------- |")

        for s in suggestions:
            lines.append(
                f"| {_cell(s['source_phrase'])} | {_cell(s['current_target'])} | "
                f"{_cell(s['suggested_target'])} | {s['severity']} | {_cell(s['reason'])} | accept / reject / modify |"
            )

        lines.append("")
        lines.append("## Summary")
        lines.append(f"- Total suggestions: {result['suggestion_count']}")
        lines.append(f"- Critical: {result['critical_suggestions']}")
        lines.append(f"- Major: {result['major_suggestions']}")
        lines.append(f"- Minor: {result['minor_suggestions']}")
        lines.append(f"- Recommendation: {result['recommendation']}")
        lines.append("")
        lines.append("## Instructions")
        lines.append("For each suggestion, mark your decision in the 'Reviewer Decision' column:")
        lines.append("- **accept** — apply the suggested target")
        lines.append("- **reject** — keep the current target unchanged")
        lines.append("- **modify** — write your own alternative in the notes")
        lines.append("")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_suggested_edits_file(output_path: Path, suggestions_by_chunk: List[Dict[str, Any]]) -> Path:
    """Write the suggested edits markdown file. Always creates the file, even with zero suggestions."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_suggestions = sum(chunk.get("feedback_suggestion_count", 0) for chunk in suggestions_by_chunk)
    lines = ["# Blood Meridian First 5 Pages — Suggested Edits (Human Review Required)", ""]

    if total_suggestions == 0:
        lines.append("No literary feedback suggestions were generated.")
        lines.append("")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    lines.append("This is human correction feedback infrastructure, not automatic proof of literary quality.")
    lines.append("Suggestions require human review before application. Do not auto-apply.")
    lines.append("")

    for chunk in suggestions_by_chunk:
        suggestions = chunk.get("literary_feedback_suggestions", [])
        if not suggestions:
            continue
        lines.append(f"## Chunk: {chunk.get('chunk_id', 'unknown')}")
        lines.append("")
        for s in suggestions:
            lines.extend([
                f"### {s.get('correction_id', '?')}",
                "",
                f"- **Source phrase:** {_cell(s.get('source_phrase', ''))}",
                f"- **Current target:** {_cell(s.get('current_target', ''))}",
                f"- **Suggested target:** {_cell(s.get('suggested_target', ''))}",
                f"- **Severity:** {s.get('severity', '?')}",
                f"- **Reason:** {_cell(s.get('reason', ''))}",
                f"- **Apply mode:** {s.get('apply_mode', 'suggest_only')}",
                f"- **Reviewer decision:** accept / reject / modify",
                f"- **Reviewer notes:**",
                "",
            ])

    lines.append("## Summary")
    lines.append(f"- Total suggestions: {total_suggestions}")
    lines.append("")
    lines.append("## Instructions")
    lines.append("For each suggestion, mark your decision:")
    lines.append("- **accept** — apply the suggested target")
    lines.append("- **reject** — keep the current target unchanged")
    lines.append("- **modify** — write your own alternative in the notes")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
