import re
from typing import Any, Dict, List, Optional, Tuple


class MemoryAwareRanker:
    """Deterministic memory router scorer using relevance, scope, hygiene, and effectiveness metadata."""

    SCOPE_WEIGHTS = {
        "work": 0.35,
        "user": 0.25,
        "genre": 0.15,
        "global": 0.0,
    }
    HYGIENE_WEIGHTS = {
        "promote": 0.35,
        "keep": 0.0,
        "downgrade": -0.25,
        "review": -0.45,
        "retire_candidate": -0.80,
    }
    DIRECT_TYPES = {"terminology", "glossary", "character_info", "idiom", "phrasal_verb", "correction_pattern"}
    BROAD_TYPES = {"style_rule", "preference", "author_style"}

    def __init__(
        self,
        injection_threshold: float = 0.55,
        global_share_cap: float = 0.30,
    ):
        self.injection_threshold = injection_threshold
        self.global_share_cap = global_share_cap

    def route(
        self,
        source_text: str,
        memory_items: List[Dict[str, Any]],
        max_memory_items: int = 20,
    ) -> Dict[str, Any]:
        scored = [self.score_item(item, source_text) for item in memory_items]
        better_scoped_exact = self._better_scoped_exact_scores(scored)

        decisions: List[Dict[str, Any]] = []
        candidates: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

        for item, score in scored:
            decision, reason = self._preselection_decision(item, score, better_scoped_exact)
            routing_decision = self._decision_record(item, score, decision, reason)
            decisions.append(routing_decision)
            if decision == "inject":
                enriched = item.copy()
                enriched["_routing_decision"] = routing_decision
                candidates.append((enriched, routing_decision))

        candidates.sort(key=lambda pair: pair[1]["final_score"], reverse=True)

        injected: List[Dict[str, Any]] = []
        final_decisions_by_id: Dict[str, Dict[str, Any]] = {}
        global_count = 0
        non_global_exists = any(item.get("scope") != "global" for item, _ in candidates)

        for item, decision in candidates:
            if len(injected) >= max_memory_items:
                decision["decision"] = "skip"
                decision["reason"] = "Skipped because max memory injection limit was reached."
                final_decisions_by_id[str(decision.get("memory_id"))] = decision
                continue

            if item.get("scope") == "global" and not self._global_share_allows(global_count, len(injected), non_global_exists):
                decision["decision"] = "skip"
                decision["reason"] = "Skipped by global memory share cap."
                final_decisions_by_id[str(decision.get("memory_id"))] = decision
                continue

            decision["decision"] = "inject"
            if item.get("scope") == "global":
                global_count += 1
            injected.append(item)
            final_decisions_by_id[str(decision.get("memory_id"))] = decision

        final_decisions = []
        injected_ids = {item.get("memory_id") for item in injected}
        for decision in decisions:
            memory_id = str(decision.get("memory_id"))
            final_decision = final_decisions_by_id.get(memory_id, decision)
            if final_decision.get("memory_id") in injected_ids:
                final_decision["decision"] = "inject"
            final_decisions.append(final_decision)

        skipped_ids = [
            d.get("memory_id")
            for d in final_decisions
            if d.get("decision") in {"skip", "downrank"} and d.get("memory_id")
        ]
        injected_ids_list = [item.get("memory_id") for item in injected if item.get("memory_id")]

        return {
            "injected": injected,
            "skipped": [item for item, score in scored if item.get("memory_id") in set(skipped_ids)],
            "injected_memory_ids": injected_ids_list,
            "skipped_memory_ids": skipped_ids,
            "routing_decisions": final_decisions,
            "summary": self.summarize(final_decisions),
        }

    def score_item(self, item: Dict[str, Any], source_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        relevance, relevance_reason, exact_match = self._relevance(item, source_text)
        scope = str(item.get("scope") or "global")
        scope_weight = self.SCOPE_WEIGHTS.get(scope, 0.0)
        importance = self._clamp(float(item.get("importance_score", 0.5) or 0.5))
        confidence = self._clamp(float(item.get("confidence", 0.7) or 0.7))
        hygiene_status = self._hygiene_status(item)
        hygiene_weight = self.HYGIENE_WEIGHTS.get(hygiene_status, 0.0)
        impact = self._clamp(float(item.get("estimated_quality_impact_avg", 0.0) or 0.0))
        harm = self._clamp(float(item.get("harm_score_avg", 0.0) or 0.0))
        injected = int(item.get("times_injected", 0) or 0)
        detected = int(item.get("times_detected_in_output", 0) or 0)

        effectiveness_bonus = 0.0
        if impact >= 0.75:
            effectiveness_bonus += 0.30
        elif impact >= 0.50:
            effectiveness_bonus += 0.15
        if detected > 0:
            effectiveness_bonus += min(0.20, 0.05 * detected)
        if impact < 0.20 and injected >= 3:
            effectiveness_bonus -= 0.25
        if injected >= 3 and detected == 0:
            effectiveness_bonus -= 0.15

        harm_penalty = 0.60 if harm >= 0.30 else harm * 0.5
        global_noise_penalty = self._global_noise_penalty(item, relevance, exact_match)

        final_score = (
            relevance
            + scope_weight
            + (importance * 0.20)
            + (confidence * 0.15)
            + effectiveness_bonus
            + hygiene_weight
            - harm_penalty
            - global_noise_penalty
        )

        score = {
            "relevance_score": round(relevance, 4),
            "scope_weight": scope_weight,
            "importance_component": round(importance * 0.20, 4),
            "confidence_component": round(confidence * 0.15, 4),
            "effectiveness_bonus": round(effectiveness_bonus, 4),
            "hygiene_status": hygiene_status,
            "hygiene_weight": hygiene_weight,
            "harm_penalty": round(harm_penalty, 4),
            "global_noise_penalty": round(global_noise_penalty, 4),
            "final_score": round(final_score, 4),
            "exact_key_match": exact_match,
            "relevance_reason": relevance_reason,
        }
        return item, score

    def summarize(self, routing_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        loaded = len(routing_decisions)
        injected = [d for d in routing_decisions if d.get("decision") == "inject"]
        skipped = [d for d in routing_decisions if d.get("decision") in {"skip", "downrank"}]
        global_injected = [d for d in injected if d.get("scope") == "global"]
        promoted_injected = [d for d in injected if d.get("hygiene_status") == "promote"]
        retire_skipped = [d for d in skipped if d.get("hygiene_status") == "retire_candidate"]
        avg_score = sum(float(d.get("final_score", 0.0) or 0.0) for d in injected) / len(injected) if injected else 0.0
        return {
            "router_loaded_memory_count": loaded,
            "router_injected_memory_count": len(injected),
            "router_skipped_memory_count": len(skipped),
            "router_global_memory_share": len(global_injected) / len(injected) if injected else 0.0,
            "router_promoted_injected_count": len(promoted_injected),
            "router_retire_candidate_skipped_count": len(retire_skipped),
            "router_average_injected_score": avg_score,
        }

    def _preselection_decision(
        self,
        item: Dict[str, Any],
        score: Dict[str, Any],
        better_scoped_exact: Dict[str, float],
    ) -> Tuple[str, str]:
        hygiene_status = score["hygiene_status"]
        harm = float(item.get("harm_score_avg", 0.0) or 0.0)
        scope = item.get("scope", "global")
        final_score = score["final_score"]
        exact_match = score["exact_key_match"]

        if harm >= 0.30:
            return "skip", "Skipped because historical harm score is elevated."

        if hygiene_status == "retire_candidate":
            if self._retire_exception_allowed(item, score, better_scoped_exact):
                return "inject", "Retire candidate allowed only because it is an exact safe match with no better scoped memory."
            return "skip", "Skipped because hygiene marked this memory as retire_candidate."

        if item.get("type") not in self.BROAD_TYPES and score["relevance_score"] <= 0.0:
            return "skip", "Skipped because keyed memory has no lexical relevance to the source chunk."

        if hygiene_status == "downgrade" and float(item.get("estimated_quality_impact_avg", 0.0) or 0.0) < 0.20:
            return "downrank", "Downranked because hygiene marked this low-impact memory as downgrade."

        if scope == "global" and not exact_match and score["relevance_score"] < 0.70:
            return "skip", "Skipped because global memory requires strong lexical relevance."

        if final_score < self.injection_threshold:
            return "downrank", f"Downranked because score {final_score:.2f} is below threshold {self.injection_threshold:.2f}."

        return "inject", self._positive_reason(item, score)

    def _retire_exception_allowed(
        self,
        item: Dict[str, Any],
        score: Dict[str, Any],
        better_scoped_exact: Dict[str, float],
    ) -> bool:
        if not score["exact_key_match"]:
            return False
        if float(item.get("harm_score_avg", 0.0) or 0.0) > 0.10:
            return False
        if score["final_score"] < self.injection_threshold:
            return False
        memory_id = str(item.get("memory_id") or "")
        return better_scoped_exact.get(memory_id, 0.0) <= 0.0

    def _better_scoped_exact_scores(self, scored: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> Dict[str, float]:
        best_non_global = max(
            (
                score["final_score"]
                for item, score in scored
                if item.get("scope") != "global" and score.get("exact_key_match")
            ),
            default=0.0,
        )
        return {str(item.get("memory_id") or ""): best_non_global for item, score in scored}

    def _decision_record(
        self,
        item: Dict[str, Any],
        score: Dict[str, Any],
        decision: str,
        reason: str,
    ) -> Dict[str, Any]:
        return {
            "memory_id": item.get("memory_id"),
            "key": item.get("key"),
            "scope": item.get("scope", "global"),
            "type": item.get("type"),
            "hygiene_status": score["hygiene_status"],
            "estimated_quality_impact_avg": float(item.get("estimated_quality_impact_avg", 0.0) or 0.0),
            "harm_score_avg": float(item.get("harm_score_avg", 0.0) or 0.0),
            "relevance_score": score["relevance_score"],
            "final_score": score["final_score"],
            "decision": decision,
            "reason": reason,
        }

    def _positive_reason(self, item: Dict[str, Any], score: Dict[str, Any]) -> str:
        parts = []
        if item.get("scope") == "work":
            parts.append("work-scoped")
        elif item.get("scope") == "user":
            parts.append("user-scoped")
        elif item.get("scope") == "genre":
            parts.append("genre-scoped")
        else:
            parts.append("global")
        if score["hygiene_status"] == "promote":
            parts.append("promoted")
        if float(item.get("estimated_quality_impact_avg", 0.0) or 0.0) >= 0.50:
            parts.append("high-effectiveness")
        if score["exact_key_match"]:
            parts.append("exact-match")
        return "Injected " + ", ".join(parts) + f" memory with score {score['final_score']:.2f}."

    def _global_share_allows(self, global_count: int, injected_count: int, non_global_exists: bool) -> bool:
        if not non_global_exists:
            return True
        if injected_count == 0:
            return False
        return (global_count + 1) / (injected_count + 1) <= self.global_share_cap

    def _hygiene_status(self, item: Dict[str, Any]) -> str:
        return str(
            item.get("hygiene_status")
            or item.get("last_effectiveness_decision")
            or "keep"
        )

    def _relevance(self, item: Dict[str, Any], source_text: str) -> Tuple[float, str, bool]:
        key = str(item.get("key") or "")
        value = item.get("value", "")
        memory_type = str(item.get("type") or "")
        source_norm = self._norm(source_text)
        key_norm = self._norm(key)
        value_norm = self._norm_value(value)

        if key_norm and key_norm in source_norm:
            return 1.0, "Exact key match in source chunk.", True

        key_tokens = [t for t in key_norm.split() if len(t) >= 3]
        if key_tokens and all(t in source_norm for t in key_tokens):
            return 0.85, "Partial key token match in source chunk.", False

        if value_norm and value_norm in source_norm and memory_type not in self.BROAD_TYPES:
            return 0.65, "Memory value appears in source chunk.", False

        if memory_type in self.BROAD_TYPES:
            confidence = float(item.get("confidence", 0.7) or 0.7)
            if confidence >= 0.85:
                return 0.35, "Broad style/preference memory with high confidence.", False
            return 0.20, "Broad style/preference memory with weak lexical relevance.", False

        return 0.0, "No lexical relevance signal.", False

    def _global_noise_penalty(self, item: Dict[str, Any], relevance: float, exact_match: bool) -> float:
        if item.get("scope") != "global":
            return 0.0
        penalty = 0.10
        if not exact_match:
            penalty += 0.20
        if relevance < 0.70:
            penalty += 0.15
        return penalty

    def _norm_value(self, value: Any) -> str:
        if isinstance(value, dict):
            return self._norm(" ".join(str(v) for v in value.values()))
        if isinstance(value, list):
            return self._norm(" ".join(str(v) for v in value))
        return self._norm(value)

    def _norm(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").casefold()).strip()

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
