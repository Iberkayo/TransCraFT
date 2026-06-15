import datetime
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class MemoryEffectivenessEvaluator:
    """Rule-based evaluator for measuring whether loaded memories affected output."""

    FORBIDDEN_TYPES = {"forbidden_term", "negative_glossary", "do_not_translate"}
    DIRECT_MATCH_TYPES = {
        "terminology",
        "glossary",
        "character_info",
        "idiom",
        "phrasal_verb",
        "correction_pattern",
    }
    STYLE_TYPES = {"style_rule", "preference", "author_style"}

    def __init__(self, enable_llm: bool = False):
        self.enable_llm = enable_llm

    def evaluate_chunk(
        self,
        source_text: str,
        translated_text: str,
        loaded_memories: Optional[List[Dict[str, Any]]] = None,
        injected_memory_ids: Optional[List[str]] = None,
        tie_off_translation: Optional[str] = None,
        tie_on_translation: Optional[str] = None,
        genre: Optional[str] = None,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
        style_contract: Optional[Dict[str, Any]] = None,
        evaluator_output: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        del user_id, style_contract, evaluator_output  # Reserved inputs for future scoring hooks.

        loaded_memories = loaded_memories or []
        injected_ids = set(injected_memory_ids or [])
        records = []

        for memory in loaded_memories:
            memory_id = memory.get("memory_id")
            detected = self._detected_in_output(memory, translated_text)
            relevance = self._relevance_score(memory, source_text)
            harm = self._harm_score(memory, translated_text)
            usage = self._usage_score(memory, detected, relevance)
            impact = self._quality_impact(
                memory=memory,
                detected=detected,
                relevance_score=relevance,
                usage_score=usage,
                harm_score=harm,
                tie_off_translation=tie_off_translation,
                tie_on_translation=tie_on_translation or translated_text,
            )
            decision = self._decision(usage, impact, harm)

            records.append(
                {
                    "memory_id": memory_id,
                    "key": memory.get("key"),
                    "type": memory.get("type"),
                    "scope": memory.get("scope"),
                    "loaded": True,
                    "injected": bool(memory_id and memory_id in injected_ids),
                    "detected_in_output": detected,
                    "relevance_score": round(relevance, 3),
                    "usage_score": round(usage, 3),
                    "estimated_quality_impact": round(impact, 3),
                    "harm_score": round(harm, 3),
                    "decision": decision,
                    "evidence": self._evidence(memory, detected, relevance, impact, harm),
                    "source_work": work_id or memory.get("source_work"),
                    "source_genre": genre or memory.get("source_genre"),
                }
            )

        return records

    def summarize_records(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        records = list(records)
        loaded = len(records)
        detected = sum(1 for r in records if r.get("detected_in_output"))
        injected = sum(1 for r in records if r.get("injected"))
        avg_impact = self._avg(r.get("estimated_quality_impact", 0.0) for r in records)
        avg_harm = self._avg(r.get("harm_score", 0.0) for r in records)
        decisions = Counter(r.get("decision", "review") for r in records)
        return {
            "memory_loaded_count": loaded,
            "memory_injected_count": injected,
            "memory_detected_count": detected,
            "memory_use_rate": detected / loaded if loaded else 0.0,
            "average_memory_impact": avg_impact,
            "average_harm_score": avg_harm,
            "promoted_memory_count": decisions.get("promote", 0),
            "downgraded_memory_count": decisions.get("downgrade", 0),
            "retired_memory_count": decisions.get("retire", 0),
            "review_memory_count": decisions.get("review", 0),
            "kept_memory_count": decisions.get("keep", 0),
        }

    def evaluate_ab_impact(
        self,
        tie_off_translation: str,
        tie_on_translation: str,
        effectiveness_records: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Return a lightweight TIE ON/OFF impact summary when paired outputs exist."""
        records = list(effectiveness_records or [])
        off_norm = self._norm(tie_off_translation)
        on_norm = self._norm(tie_on_translation)
        summaries = self.summarize_records(records)
        return {
            "tie_off_length": len(off_norm),
            "tie_on_length": len(on_norm),
            "length_delta": len(on_norm) - len(off_norm),
            "outputs_identical": off_norm == on_norm,
            "memory_detected_count": summaries["memory_detected_count"],
            "average_memory_impact": summaries["average_memory_impact"],
            "average_harm_score": summaries["average_harm_score"],
        }

    def generate_report(self, records: Iterable[Dict[str, Any]], output_path: Path) -> Path:
        records = self._aggregate_records(list(records))
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = self.summarize_records(records)
        high = sorted(records, key=lambda r: r.get("estimated_quality_impact", 0.0), reverse=True)[:20]
        low = sorted(records, key=lambda r: (r.get("usage_score", 0.0), r.get("estimated_quality_impact", 0.0)))[:20]
        harmful = [r for r in records if r.get("harm_score", 0.0) >= 0.5]

        lines = [
            "# Memory Effectiveness Report",
            "",
            "## 1. Executive Summary",
            "",
            f"- Memories evaluated: {summary['memory_loaded_count']}",
            f"- Injected memories: {summary['memory_injected_count']}",
            f"- Detected in output: {summary['memory_detected_count']}",
            f"- Memory use rate: {summary['memory_use_rate']:.2%}",
            f"- Average estimated impact: {summary['average_memory_impact']:.2f}",
            f"- Average harm score: {summary['average_harm_score']:.2f}",
            "",
            "## 2. Top 20 Most Useful Memories",
            "",
            self._records_table(high),
            "",
            "## 3. Top 20 Low-Value Memories",
            "",
            self._records_table(low),
            "",
            "## 4. Potentially Harmful Memories",
            "",
            self._records_table(harmful),
            "",
            "## 5. Memory Usage by Scope",
            "",
            self._group_table(records, "scope"),
            "",
            "## 6. Memory Usage by Genre",
            "",
            self._group_table(records, "source_genre"),
            "",
            "## 7. Memory Usage by Work",
            "",
            self._group_table(records, "source_work"),
            "",
            "## 8. Recommendations",
            "",
            *self._recommendations(summary, harmful),
            "",
        ]
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def _aggregate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            key = record.get("memory_id") or f"{record.get('scope')}|{record.get('type')}|{record.get('key')}"
            grouped[str(key)].append(record)

        aggregated = []
        for items in grouped.values():
            first = items[0]
            detected_count = sum(1 for item in items if item.get("detected_in_output"))
            loaded_count = sum(1 for item in items if item.get("loaded"))
            injected_count = sum(1 for item in items if item.get("injected"))
            impact = self._avg(item.get("estimated_quality_impact", 0.0) for item in items)
            harm = self._avg(item.get("harm_score", 0.0) for item in items)
            usage = detected_count / len(items) if items else 0.0
            aggregated.append(
                {
                    **first,
                    "loaded": loaded_count > 0,
                    "injected": injected_count > 0,
                    "detected_in_output": detected_count > 0,
                    "loaded_count": loaded_count,
                    "detected_count": detected_count,
                    "usage_score": usage,
                    "estimated_quality_impact": impact,
                    "harm_score": harm,
                    "decision": self._decision(usage, impact, harm),
                }
            )
        return aggregated

    def _detected_in_output(self, memory: Dict[str, Any], translated_text: str) -> bool:
        text = self._norm(translated_text)
        memory_type = memory.get("type", "")
        values = self._candidate_output_values(memory)

        if memory_type in self.FORBIDDEN_TYPES:
            return not any(self._norm(v) in text for v in values if self._norm(v))

        if memory_type in self.DIRECT_MATCH_TYPES:
            return any(self._norm(v) in text for v in values if self._norm(v))

        if memory_type in self.STYLE_TYPES:
            return self._style_signal(memory, translated_text)

        return any(self._norm(v) in text for v in values if self._norm(v))

    def _relevance_score(self, memory: Dict[str, Any], source_text: str) -> float:
        key = self._norm(memory.get("key", ""))
        source = self._norm(source_text)
        memory_type = memory.get("type", "")

        if key and key in source:
            return 0.95
        if memory_type in self.STYLE_TYPES:
            return 0.55
        if memory.get("scope") in {"work", "genre", "user"}:
            return 0.35
        return 0.15

    def _usage_score(self, memory: Dict[str, Any], detected: bool, relevance_score: float) -> float:
        if memory.get("type") in self.FORBIDDEN_TYPES:
            return 0.0 if detected else 0.9
        if detected:
            return max(0.65, relevance_score)
        return 0.05 if relevance_score < 0.4 else 0.15

    def _quality_impact(
        self,
        memory: Dict[str, Any],
        detected: bool,
        relevance_score: float,
        usage_score: float,
        harm_score: float,
        tie_off_translation: Optional[str],
        tie_on_translation: Optional[str],
    ) -> float:
        if harm_score >= 0.8:
            return 0.0

        values = [self._norm(v) for v in self._candidate_output_values(memory)]
        if tie_off_translation and tie_on_translation and values:
            off = self._norm(tie_off_translation)
            on = self._norm(tie_on_translation)
            appears_on = any(v and v in on for v in values)
            appears_off = any(v and v in off for v in values)
            if appears_on and not appears_off:
                return min(1.0, 0.75 + relevance_score * 0.2)

        if detected:
            confidence = float(memory.get("confidence", 0.7) or 0.7)
            return min(1.0, usage_score * 0.65 + relevance_score * 0.25 + confidence * 0.1)
        return 0.0

    def _harm_score(self, memory: Dict[str, Any], translated_text: str) -> float:
        if memory.get("type") not in self.FORBIDDEN_TYPES:
            return 0.0
        text = self._norm(translated_text)
        forbidden_values = [self._norm(v) for v in self._candidate_output_values(memory)]
        return 0.9 if any(v and v in text for v in forbidden_values) else 0.0

    def _decision(self, usage_score: float, impact: float, harm: float) -> str:
        if harm >= 0.8:
            return "retire"
        if impact >= 0.75 and usage_score >= 0.65:
            return "promote"
        if usage_score < 0.2 and impact < 0.2:
            return "downgrade"
        if impact >= 0.35:
            return "keep"
        return "review"

    def _evidence(
        self,
        memory: Dict[str, Any],
        detected: bool,
        relevance: float,
        impact: float,
        harm: float,
    ) -> str:
        if harm >= 0.8:
            return "Forbidden or negative memory appeared in the output."
        if detected:
            return f"Memory value was detected in the output with relevance {relevance:.2f} and estimated impact {impact:.2f}."
        return f"Memory was loaded but not detected in the output; relevance estimate {relevance:.2f}."

    def _candidate_output_values(self, memory: Dict[str, Any]) -> List[str]:
        value = memory.get("value", "")
        if isinstance(value, dict):
            values = [str(v) for v in value.values()]
        elif isinstance(value, list):
            values = [str(v) for v in value]
        else:
            values = [str(value)]

        if memory.get("type") in self.FORBIDDEN_TYPES:
            values.append(str(memory.get("key", "")))
        return [v for v in values if v]

    def _style_signal(self, memory: Dict[str, Any], translated_text: str) -> bool:
        text = translated_text or ""
        combined = f"{memory.get('key', '')} {memory.get('value', '')}".lower()
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]

        if "fragment" in combined or "paratactic" in combined:
            short_sentences = [s for s in sentences if len(s.split()) <= 5]
            return len(short_sentences) >= 2
        if "semicolon" in combined:
            return ";" in text
        if "formal" in combined or "academic" in combined:
            return any(term in text.lower() for term in ["çalışma", "model", "sonuç", "yöntem"])
        return False

    def _records_table(self, records: List[Dict[str, Any]]) -> str:
        if not records:
            return "_No records._"
        lines = [
            "| Memory ID | Key | Type | Scope | Loaded | Detected | Avg Impact | Harm | Decision |",
            "| --------- | --- | ---- | ----- | -----: | -------: | ---------: | ---: | -------- |",
        ]
        for r in records:
            lines.append(
                "| {memory_id} | {key} | {type} | {scope} | {loaded} | {detected} | {impact:.2f} | {harm:.2f} | {decision} |".format(
                    memory_id=self._cell(r.get("memory_id")),
                    key=self._cell(r.get("key")),
                    type=self._cell(r.get("type")),
                    scope=self._cell(r.get("scope")),
                    loaded=int(r.get("loaded_count", 1 if r.get("loaded") else 0) or 0),
                    detected=int(r.get("detected_count", 1 if r.get("detected_in_output") else 0) or 0),
                    impact=float(r.get("estimated_quality_impact", 0.0) or 0.0),
                    harm=float(r.get("harm_score", 0.0) or 0.0),
                    decision=self._cell(r.get("decision")),
                )
            )
        return "\n".join(lines)

    def _group_table(self, records: List[Dict[str, Any]], field: str) -> str:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            groups[str(record.get(field) or "unknown")].append(record)
        if not groups:
            return "_No records._"

        lines = [
            "| Group | Loaded | Detected | Use Rate | Avg Impact | Avg Harm |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
        for group, items in sorted(groups.items()):
            detected = sum(1 for r in items if r.get("detected_in_output"))
            lines.append(
                f"| {self._cell(group)} | {len(items)} | {detected} | {detected / len(items):.2%} | "
                f"{self._avg(r.get('estimated_quality_impact', 0.0) for r in items):.2f} | "
                f"{self._avg(r.get('harm_score', 0.0) for r in items):.2f} |"
            )
        return "\n".join(lines)

    def _recommendations(self, summary: Dict[str, Any], harmful: List[Dict[str, Any]]) -> List[str]:
        lines = []
        if summary["memory_loaded_count"] == 0:
            return ["- No memories were evaluated; run a TIE-enabled sample before making memory decisions."]
        if summary["memory_use_rate"] < 0.25:
            lines.append("- Simplify or prune memory: most loaded memories are not reflected in output.")
        else:
            lines.append("- Keep the current memory approach, but continue measuring item-level usefulness.")
        if harmful:
            lines.append("- Review or retire harmful memories before promotion.")
        if summary["promoted_memory_count"] > summary["downgraded_memory_count"]:
            lines.append("- Promote repeatedly detected, high-impact memories within their current scope.")
        return lines

    def _norm(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").casefold()).strip()

    def _cell(self, value: Any) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")

    def _avg(self, values: Iterable[float]) -> float:
        values = [float(v or 0.0) for v in values]
        return sum(values) / len(values) if values else 0.0


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
