import datetime
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MemoryHygieneManager:
    """Assign hygiene decisions to memory records based on effectiveness metadata.

    Uses conservative thresholds to promote, keep, downgrade, review, or mark
    memories as retire_candidate without ever deleting them.
    """

    VALID_DECISIONS = {"promote", "keep", "downgrade", "review", "retire_candidate"}

    # Scope priority for ranking (higher number = loaded more conservatively downstream)
    SCOPE_PRIORITY = {
        "work": 4,
        "user": 3,
        "genre": 2,
        "global": 1,
    }

    def __init__(self, dry_run: bool = True, memory_dir: Optional[Path] = None):
        self.dry_run = dry_run
        if memory_dir is None:
            self.memory_dir = Path(__file__).resolve().parent.parent.parent / "memory"
        else:
            self.memory_dir = Path(memory_dir)

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def evaluate(self, memory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a list of hygiene recommendation records for every item."""
        decisions: List[Dict[str, Any]] = []
        for item in memory_items:
            rec = self._evaluate_one(item)
            rec["memory_id"] = item.get("memory_id", "")
            rec["key"] = item.get("key", "")
            rec["scope"] = item.get("scope", "global")
            rec["type"] = item.get("type", "")
            rec["times_injected"] = int(item.get("times_injected", 0) or 0)
            rec["times_detected_in_output"] = int(item.get("times_detected_in_output", 0) or 0)
            rec["estimated_quality_impact_avg"] = float(item.get("estimated_quality_impact_avg", 0.0) or 0.0)
            rec["harm_score_avg"] = float(item.get("harm_score_avg", 0.0) or 0.0)
            rec["previous_importance_score"] = float(item.get("importance_score", 0.5) or 0.5)
            decisions.append(rec)
        return decisions

    def apply(self, memory_items: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Apply hygiene decisions back into memory metadata (mutates in-memory only in dry_run mode).

        Returns (updated_items, mutation_count).
        """
        rec_by_id: Dict[str, Dict[str, Any]] = {
            str(r.get("memory_id", "")): r
            for r in recommendations
            if r.get("memory_id")
        }
        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        mutations = 0

        for item in memory_items:
            mid = item.get("memory_id")
            rec = rec_by_id.get(str(mid)) if mid else None
            if rec is None:
                continue

            # Ensure required hygiene fields exist
            self._ensure_hygiene_fields(item)

            decision = rec["decision"]
            # Update importance_score based on the hygiene decision
            old_score = item.get("importance_score", 0.5) or 0.5
            new_score = self._adjusted_importance_score(decision, old_score)

            item["hygiene_status"] = decision
            item["hygiene_reason"] = rec["reason"]
            item["hygiene_updated_at"] = now
            item["effectiveness_observation_count"] = int(item.get("effectiveness_sample_count", 0) or 0)
            item["previous_importance_score"] = old_score
            item["importance_score"] = round(new_score, 4)
            mutations += 1

        return memory_items, mutations

    def generate_report(self, recommendations: List[Dict[str, Any]], output_path: Path) -> Path:
        """Write the memory hygiene markdown report."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        decisions = self._group_by_decision(recommendations)
        promoted = decisions.get("promote", [])
        kept = decisions.get("keep", [])
        downgraded = decisions.get("downgrade", [])
        review = decisions.get("review", [])
        retire = decisions.get("retire_candidate", [])

        lines = [
            "# Memory Hygiene Report",
            "",
            "## 1. Executive Summary",
            "",
            f"- Total memories evaluated: {len(recommendations)}",
            f"- Promoted: {len(promoted)}",
            f"- Kept: {len(kept)}",
            f"- Downgraded: {len(downgraded)}",
            f"- Review: {len(review)}",
            f"- Retire candidates: {len(retire)}",
            f"- Mode: {'dry-run' if self.dry_run else 'apply'}",
            "",
            "## 2. Memories Recommended for Promotion",
            "",
            self._records_table(promoted),
            "",
            "## 3. Memories Kept",
            "",
            self._records_table(kept),
            "",
            "## 4. Memories Downgraded",
            "",
            self._records_table(downgraded),
            "",
            "## 5. Memories Requiring Review",
            "",
            self._records_table(review),
            "",
            "## 6. Retire Candidates",
            "",
            self._records_table(retire),
            "",
            "## 7. Global Memory Noise Analysis",
            "",
            self._global_noise_table(recommendations),
            "",
            "## 8. Scope-Level Findings",
            "",
            self._scope_table(recommendations),
            "",
            "## 9. Recommendations",
            "",
            *self._recommendation_bullets(decisions, recommendations),
            "",
        ]

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------ #
    #  Decision helpers
    # ------------------------------------------------------------------ #

    def _evaluate_one(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Return a single decision record for one memory item."""
        impact = float(item.get("estimated_quality_impact_avg", 0.0) or 0.0)
        harm = float(item.get("harm_score_avg", 0.0) or 0.0)
        injected = int(item.get("times_injected", 0) or 0)
        detected = int(item.get("times_detected_in_output", 0) or 0)
        scope = str(item.get("scope", "global"))
        sample_count = int(item.get("effectiveness_sample_count", 0) or 0)
        confidence = float(item.get("confidence", 0.7) or 0.7)

        decision, reason = self._decide(impact, harm, injected, detected, scope, sample_count, confidence)

        return {
            "decision": decision,
            "reason": reason,
        }

    def _decide(
        self,
        impact: float,
        harm: float,
        injected: int,
        detected: int,
        scope: str,
        sample_count: int,
        confidence: float,
    ) -> Tuple[str, str]:
        """Apply conservative hygiene rules and return (decision, reason)."""

        # --- Promote ---
        if impact >= 0.75 and harm <= 0.10 and detected >= 1 and injected >= 1:
            return "promote", (
                f"High impact ({impact:.2f}), low harm ({harm:.2f}), "
                f"detected {detected} times over {injected} injections."
            )

        # --- Retire Candidate (global only, very conservative) ---
        if scope == "global" and injected >= 5 and detected == 0 and impact <= 0.10 and harm <= 0.10:
            return "retire_candidate", (
                f"Global memory repeatedly injected ({injected}x) but never detected "
                f"with negligible impact ({impact:.2f}) and low harm ({harm:.2f})."
            )

        # --- Review ---
        if harm >= 0.30:
            return "review", f"Harm score elevated ({harm:.2f}); human review recommended."
        if injected >= 3 and detected == 0 and impact < 0.20 and harm <= 0.10 and scope != "global":
            # Repeatedly injected non-global memory with no detection — unusual
            return "review", (
                f"Non-global memory injected {injected}x with zero detections "
                f"and low impact ({impact:.2f}); may have conflicting signals."
            )
        if sample_count == 0 and confidence < 0.5:
            return "review", "Low confidence and never sampled for effectiveness."

        # --- Downgrade ---
        if injected >= 3 and detected == 0 and impact < 0.20 and harm <= 0.10:
            return "downgrade", (
                f"Injected {injected}x but never detected; impact low ({impact:.2f})."
            )

        # --- Keep (default safe state) ---
        return "keep", (
            f"Moderate signals: impact={impact:.2f}, detected={detected}, "
            f"injected={injected}, harm={harm:.2f}. Insufficient evidence to promote or downgrade."
        )

    def _adjusted_importance_score(self, decision: str, current: float) -> float:
        if decision == "promote":
            return max(0.05, min(1.0, current + 0.10))
        if decision == "downgrade":
            return max(0.05, min(1.0, current - 0.05))
        if decision == "retire_candidate":
            return max(0.05, min(1.0, current - 0.10))
        return current

    def _ensure_hygiene_fields(self, item: Dict[str, Any]):
        """Add default hygiene metadata fields to old records without them."""
        defaults: Dict[str, Any] = {
            "hygiene_status": None,
            "hygiene_reason": None,
            "hygiene_updated_at": None,
            "effectiveness_observation_count": int(item.get("effectiveness_sample_count", 0) or 0),
            "previous_importance_score": float(item.get("importance_score", 0.5) or 0.5),
        }
        for k, v in defaults.items():
            if k not in item:
                item[k] = v

    # ------------------------------------------------------------------ #
    #  Reporting helpers
    # ------------------------------------------------------------------ #

    def _group_by_decision(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for rec in recommendations:
            groups[rec.get("decision", "review")].append(rec)
        return dict(groups)

    def _records_table(self, records: List[Dict[str, Any]]) -> str:
        if not records:
            return "_No records._"
        lines = [
            "| Memory ID | Key | Scope | Type | Injected | Detected | Avg Impact | Harm | Decision | Reason |",
            "| --------- | --- | ----- | ---- | -------: | -------: | ---------: | ---: | -------- | ------ |",
        ]
        for r in records:
            lines.append(
                "| {memory_id} | {key} | {scope} | {type} | {injected} | {detected} | {impact:.2f} | {harm:.2f} | {decision} | {reason} |".format(
                    memory_id=self._cell(r.get("memory_id")),
                    key=self._cell(r.get("key")),
                    scope=self._cell(r.get("scope")),
                    type=self._cell(r.get("type")),
                    injected=int(r.get("times_injected", 0) or 0),
                    detected=int(r.get("times_detected_in_output", 0) or 0),
                    impact=float(r.get("estimated_quality_impact_avg", 0.0) or 0.0),
                    harm=float(r.get("harm_score_avg", 0.0) or 0.0),
                    decision=self._cell(r.get("decision")),
                    reason=self._cell(r.get("reason")),
                )
            )
        return "\n".join(lines)

    def _global_noise_table(self, recommendations: List[Dict[str, Any]]) -> str:
        globals_ = [r for r in recommendations if r.get("scope") == "global"]
        if not globals_:
            return "_No global memories._"
        lines = [
            "| Memory ID | Key | Injected | Detected | Impact | Noise Score |",
            "| --------- | --- | -------: | -------: | -----: | ---------: |",
        ]
        for r in sorted(globals_, key=lambda x: -self._noise_score(x)):
            noise = self._noise_score(r)
            lines.append(
                "| {memory_id} | {key} | {injected} | {detected} | {impact:.2f} | {noise:.2f} |".format(
                    memory_id=self._cell(r.get("memory_id")),
                    key=self._cell(r.get("key")),
                    injected=int(r.get("times_injected", 0) or 0),
                    detected=int(r.get("times_detected_in_output", 0) or 0),
                    impact=float(r.get("estimated_quality_impact_avg", 0.0) or 0.0),
                    noise=noise,
                )
            )
        return "\n".join(lines)

    def _noise_score(self, rec: Dict[str, Any]) -> float:
        injected = max(1, int(rec.get("times_injected", 0) or 0))
        detected = int(rec.get("times_detected_in_output", 0) or 0)
        impact = float(rec.get("estimated_quality_impact_avg", 0.0) or 0.0)
        return (injected - detected) * (1.0 - impact) / injected

    def _scope_table(self, recommendations: List[Dict[str, Any]]) -> str:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for rec in recommendations:
            groups[str(rec.get("scope", "unknown"))].append(rec)

        lines = [
            "| Scope | Count | Promoted | Kept | Downgraded | Review | Retire Cand. | Avg Impact |",
            "| ----- | ----: | -------: | ---: | ---------: | -----: | -----------: | ---------: |",
        ]
        scope_order = ["work", "user", "genre", "global", "unknown"]
        for scope in scope_order:
            items = groups.get(scope, [])
            if not items:
                # Remove from dict so we don't print "unknown" if empty
                groups.pop(scope, None)
                continue
            decision_counts = defaultdict(int)
            for r in items:
                decision_counts[r.get("decision", "review")] += 1
            avg_impact = sum(float(r.get("estimated_quality_impact_avg", 0.0) or 0.0) for r in items) / len(items)
            lines.append(
                f"| {self._cell(scope)} | {len(items)} | {decision_counts.get('promote', 0)} | "
                f"{decision_counts.get('keep', 0)} | {decision_counts.get('downgrade', 0)} | "
                f"{decision_counts.get('review', 0)} | {decision_counts.get('retire_candidate', 0)} | "
                f"{avg_impact:.2f} |"
            )
        for scope, items in sorted(groups.items()):
            if not items:
                continue
            decision_counts = defaultdict(int)
            for r in items:
                decision_counts[r.get("decision", "review")] += 1
            avg_impact = sum(float(r.get("estimated_quality_impact_avg", 0.0) or 0.0) for r in items) / len(items)
            lines.append(
                f"| {self._cell(scope)} | {len(items)} | {decision_counts.get('promote', 0)} | "
                f"{decision_counts.get('keep', 0)} | {decision_counts.get('downgrade', 0)} | "
                f"{decision_counts.get('review', 0)} | {decision_counts.get('retire_candidate', 0)} | "
                f"{avg_impact:.2f} |"
            )
        return "\n".join(lines)

    def _recommendation_bullets(self, decisions: Dict[str, List[Dict[str, Any]]], all_recs: List[Dict[str, Any]]) -> List[str]:
        lines: List[str] = []
        if not all_recs:
            return ["- No memories evaluated."]

        promoted = len(decisions.get("promote", []))
        downgraded = len(decisions.get("downgrade", []))
        review = len(decisions.get("review", []))
        retire = len(decisions.get("retire_candidate", []))

        if promoted > 0:
            lines.append(f"- {promoted} memories recommended for promotion — these are working well within their scope.")
        else:
            lines.append("- No memories met promotion criteria. Consider increasing sample size.")

        global_noise = sum(1 for r in all_recs if r.get("scope") == "global" and r.get("decision") in {"downgrade", "retire_candidate"})
        if global_noise > 0:
            lines.append(f"- {global_noise} global memories are noise candidates. Global memory should be loaded more conservatively.")
        else:
            lines.append("- Global memory appears relatively clean for the current sample size.")

        if retire > 0:
            lines.append(f"- {retire} global memories identified as retire candidates — review manually before removing.")
        else:
            lines.append("- No retire candidates identified (good sign for this sample size).")

        if review > 0:
            lines.append(f"- {review} memories need human review due to conflicting signals or elevated harm scores.")

        if downgraded > 0:
            lines.append(f"- {downgraded} memories downgraded — these should be injected less frequently or with lower priority.")

        if self.dry_run:
            lines.append("- **Dry-run mode**: no memory files were mutated. Run with `--apply` to persist changes.")

        return lines

    # ------------------------------------------------------------------ #
    #  Utility
    # ------------------------------------------------------------------ #

    @staticmethod
    def _cell(value: Any) -> str:
        if value is None:
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")