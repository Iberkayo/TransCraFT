"""TIE v0.9.4.2 — Literary Human Correction Feedback + Fix Suggestion Layer.

Loads Berkay's human correction dataset and generates structured
suggestions for literary translation review. Never auto-applies corrections.
Supports accepted edit parsing, normalized matching, and coverage auditing.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CORRECTIONS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "eval" / "blood_meridian_first5_human_corrections.json"


def _normalize_turkish(text: str) -> str:
    """Normalize Turkish text for comparison: collapse whitespace, strip punctuation at boundaries."""
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("\u2019", "'").replace("\u2018", "'")  # curly quotes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return text


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


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
        lower = source_phrase.casefold()
        return [c for c in self.corrections if c.get("source_phrase", "").casefold() in lower]

    def find_by_current_target(self, target_text: str) -> List[Dict[str, Any]]:
        lower = target_text.casefold()
        return [c for c in self.corrections if c.get("current_target", "").casefold() in lower]

    def find_in_text(self, turkish_text: str) -> List[Dict[str, Any]]:
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
        """Generate suggestions for a translated chunk with exact, normalized, and fuzzy matching."""
        suggestions: List[Dict[str, Any]] = []
        norm_target = _normalize_turkish(translated_text).casefold()
        norm_source = _normalize_turkish(source_text).casefold()

        for correction in self.store.corrections:
            ct = correction.get("current_target", "")
            ct_norm = _normalize_turkish(ct).casefold()
            sp = correction.get("source_phrase", "").casefold()
            match_type = None
            confidence = "low"

            # 1. Exact match: current_target present in translated text
            if ct_norm in norm_target:
                match_type = "exact"
                confidence = "high"
            # 2. Normalized variant: current_target with minor punctuation diffs
            elif ct_norm.rstrip(".") in norm_target and len(ct_norm) > 10:
                match_type = "normalized"
                confidence = "high"
            # 3. Source phrase present but target variant not detected
            elif sp and sp in norm_source and ct_norm not in norm_target:
                match_type = "source_only"
                confidence = "low"
                # Only suggest if source is present — may need fuzzy target check
                if not self._any_target_keyword_in_text(ct_norm, norm_target):
                    continue  # neither source exact nor target variant present

            if match_type is None:
                continue

            suggestions.append({
                "correction_id": correction["id"],
                "source_phrase": correction["source_phrase"],
                "current_target": correction["current_target"],
                "suggested_target": correction["suggested_target"],
                "severity": correction["severity"],
                "reason": correction["reason"],
                "apply_mode": correction.get("apply_mode", "suggest_only"),
                "tags": correction.get("tags", []),
                "match_type": match_type,
                "confidence": confidence,
            })

        critical = sum(1 for s in suggestions if s["severity"] == "critical")
        major = sum(1 for s in suggestions if s["severity"] == "major")
        minor = sum(1 for s in suggestions if s["severity"] == "minor")
        recommendation = "review" if critical > 0 or major > 2 or minor > 5 else "accept"

        return {
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
            "critical_suggestions": critical,
            "major_suggestions": major,
            "minor_suggestions": minor,
            "recommendation": recommendation,
        }

    def _any_target_keyword_in_text(self, target_lower: str, text_lower: str) -> bool:
        """Check if any significant keyword from the target appears in the text."""
        words = [w for w in re.split(r"\s+", target_lower) if len(w) > 3]
        return any(w in text_lower for w in words)

    def generate_edit_file(self, output_path: Path, translated_text: str = "") -> Path:
        result = self.generate_suggestions(translated_text=translated_text)
        suggestions = result["suggestions"]
        lines = ["# Blood Meridian — Suggested Edits (Human Review Required)", ""]
        lines.append("This is human correction feedback infrastructure, not automatic proof of literary quality.")
        lines.append("Suggestions require human review before application. Do not auto-apply.")
        lines.append("")
        lines.append("| Source Phrase | Current Target | Suggested Target | Severity | Match | Reviewer Decision |")
        lines.append("| ------------- | ------------- | --------------- | -------- | ----- | ----------------- |")
        for s in suggestions:
            lines.append(
                f"| {_cell(s['source_phrase'])} | {_cell(s['current_target'])} | "
                f"{_cell(s['suggested_target'])} | {s['severity']} | {s.get('match_type', '?')} | accept / reject / modify |"
            )
        lines.append("")
        lines.append("## Summary")
        lines.append(f"- Total corrections in dataset: {len(self.store.corrections)}")
        lines.append(f"- Suggestions generated: {result['suggestion_count']}")
        lines.append(f"- Critical: {result['critical_suggestions']}")
        lines.append(f"- Major: {result['major_suggestions']}")
        lines.append(f"- Minor: {result['minor_suggestions']}")
        lines.append(f"- Recommendation: {result['recommendation']}")
        lines.append("")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def generate_coverage_report(self, output_path: Any) -> Path:
        """Generate coverage report showing which corrections triggered suggestions."""
        output_path = Path(output_path)
        lines = ["# Literary Feedback Coverage Report", ""]
        lines.append(f"Total corrections in dataset: {len(self.store.corrections)}")
        lines.append("")
        lines.append("| ID | Source Phrase | Current Target | Severity |")
        lines.append("| -- | ------------- | ------------- | -------- |")
        for c in self.store.corrections:
            lines.append(f"| {c['id']} | {_cell(c['source_phrase'])} | {_cell(c['current_target'])} | {c['severity']} |")
        lines.append("")
        lines.append("## Matching Notes")
        lines.append("Suggestions are triggered when the current_target appears in the translated text.")
        lines.append("Matching is case-insensitive, normalized (collapsed whitespace, curly quotes standardized).")
        lines.append("If a current_target does not appear in the translated output, no suggestion is generated.")
        lines.append("")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path


# ------------------------------------------------------------------ #
#  Accepted edit parsing and application
# ------------------------------------------------------------------ #

def parse_reviewer_decisions_from_suggested_edits(markdown_text: str) -> List[Dict[str, Any]]:
    """Parse accepted/rejected decisions from suggested edits markdown file."""
    decisions = []
    current = {}
    in_suggestion = False
    for line in markdown_text.splitlines():
        if line.startswith("### ") and not line.startswith("#### "):
            if current and current.get("correction_id"):
                decisions.append(current)
            current = {"correction_id": line[4:].strip(), "decision": "", "suggested_target": "", "current_target": "", "source_phrase": ""}
            in_suggestion = True
        elif in_suggestion:
            if "Suggested target:" in line:
                current["suggested_target"] = line.split(":", 1)[1].strip()
            elif "Current target:" in line:
                current["current_target"] = line.split(":", 1)[1].strip()
            elif "Source phrase:" in line:
                current["source_phrase"] = line.split(":", 1)[1].strip()
            elif "Reviewer decision:" in line:
                decision_text = line.split(":", 1)[1].strip().casefold()
                if "accept" in decision_text and "reject" not in decision_text:
                    current["decision"] = "accept"
                elif "reject" in decision_text:
                    current["decision"] = "reject"
                elif "modify" in decision_text:
                    current["decision"] = "modify"
    if current and current.get("correction_id"):
        decisions.append(current)
    return decisions


def apply_accepted_suggestions_to_text(text: str, accepted_suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply accepted suggestions by replacing current_target with suggested_target in text."""
    applied = []
    skipped = []
    edited = text
    for s in accepted_suggestions:
        if s.get("decision") != "accept":
            skipped.append({"correction_id": s["correction_id"], "current_target": s.get("current_target", ""), "reason": "not accepted"})
            continue
        ct = s.get("current_target", "")
        st = s.get("suggested_target", "")
        if ct and ct in edited:
            edited = edited.replace(ct, st)
            applied.append({"correction_id": s["correction_id"], "before": ct, "after": st})
        elif ct and _normalize_turkish(ct) in _normalize_turkish(edited):
            # Try normalized replacement
            norm_ct = _normalize_turkish(ct)
            norm_edit = _normalize_turkish(edited)
            idx = norm_edit.find(norm_ct)
            if idx >= 0:
                orig_span = edited[idx:idx + len(norm_ct)]
                edited = edited.replace(orig_span, st, 1)
                applied.append({"correction_id": s["correction_id"], "before": orig_span, "after": st})
            else:
                skipped.append({"correction_id": s["correction_id"], "current_target": ct, "reason": "current_target not found in text"})
        else:
            skipped.append({"correction_id": s["correction_id"], "current_target": ct, "reason": "current_target not found in text"})
    return {
        "edited_text": edited,
        "applied": applied,
        "skipped": skipped,
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "recommendation": "review" if skipped else "accept",
    }


def write_edited_translation_file(
    original_path: Path,
    edited_path: Path,
    accepted_suggestions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Read original translation, apply accepted suggestions, write edited file."""
    if not original_path.exists():
        return {"edited_text": "", "applied": [], "skipped": [{"reason": "original file not found"}], "recommendation": "reject"}
    original_text = original_path.read_text(encoding="utf-8")
    result = apply_accepted_suggestions_to_text(original_text, accepted_suggestions)
    edited_path.parent.mkdir(parents=True, exist_ok=True)
    edited_path.write_text(result["edited_text"], encoding="utf-8")
    return result


def write_suggested_edits_file(output_path: Path, suggestions_by_chunk: List[Dict[str, Any]], total_dataset_count: int = 0) -> Path:
    """Write the suggested edits markdown file with coverage info."""
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
                f"- **Match type:** {s.get('match_type', '?')}",
                f"- **Confidence:** {s.get('confidence', '?')}",
                f"- **Reason:** {_cell(s.get('reason', ''))}",
                f"- **Apply mode:** {s.get('apply_mode', 'suggest_only')}",
                f"- **Reviewer decision:** accept / reject / modify",
                f"- **Reviewer notes:**",
                "",
            ])
    lines.append("## Summary")
    if total_dataset_count:
        lines.append(f"- Total corrections in dataset: {total_dataset_count}")
    lines.append(f"- Total suggestions generated: {total_suggestions}")
    lines.append("")
    lines.append("## Instructions")
    lines.append("For each suggestion, mark your decision:")
    lines.append("- **accept** — apply the suggested target")
    lines.append("- **reject** — keep the current target unchanged")
    lines.append("- **modify** — write your own alternative in the notes")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path