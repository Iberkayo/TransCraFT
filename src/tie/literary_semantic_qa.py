"""Deterministic literary semantic QA guardrails."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


Flag = Dict[str, Any]


LITERARY_TERM_RISK_MAP: Dict[str, Dict[str, List[str]]] = {
    "flatboat": {
        "invalid_targets": ["düzenbaz", "duzenbaz"],
        "suggested_senses": ["sal", "düz tabanlı tekne", "nehir teknesi", "düz tekne"],
    },
    "schoolmaster": {
        "risky_targets": ["okul müdürü", "okul muduru"],
        "suggested_senses": ["okul hocası", "öğretmen"],
    },
    "scullery fire": {
        "risky_targets": ["bulaşık ocağı", "bulasik ocagi"],
        "suggested_senses": ["mutfak ocağı", "arka mutfak ocağı"],
    },
    "Dipper": {
        "risky_targets": ["kepçe", "kepce"],
        "suggested_senses": ["Büyük Kepçe", "takımyıldızı bağlamı"],
    },
    "full house": {
        "risky_targets": ["dolu salonda oynuyordu"],
        "suggested_senses": ["kalabalık cemaate vaaz veriyordu", "çadırı dolduran kalabalığa konuşuyordu"],
    },
}

ENTITY_VARIANTS = {
    "Memphis": ["Memphis"],
    "Saint Louis": ["Saint Louis", "St. Louis"],
    "New Orleans": ["New Orleans"],
    "Texas": ["Texas", "Teksas"],
    "Nacogdoches": ["Nacogdoches"],
    "Reverend Green": ["Reverend Green", "Rahip Green", "Papaz Green"],
    "Judge Holden": ["Judge Holden", "Yargıç Holden", "Yargic Holden"],
    "Toadvine": ["Toadvine"],
    "Fort Smith": ["Fort Smith"],
    "Arkansas": ["Arkansas"],
    "Tennessee": ["Tennessee"],
    "Kentucky": ["Kentucky"],
    "Mississippi": ["Mississippi"],
}


class LiteraryTermRiskDetector:
    """Flag small, known high-risk literary term mappings."""

    def detect(self, source_text: str, target_text: str) -> List[Flag]:
        source_folded = (source_text or "").casefold()
        target_folded = (target_text or "").casefold()
        flags: List[Flag] = []

        for source_term, rule in LITERARY_TERM_RISK_MAP.items():
            if source_term.casefold() not in source_folded:
                continue
            for invalid in rule.get("invalid_targets", []):
                if invalid.casefold() in target_folded:
                    flags.append(self._flag(source_term, invalid, "critical", "semantic_mistranslation_risk", rule))
            for risky in rule.get("risky_targets", []):
                if risky.casefold() in target_folded:
                    flags.append(self._flag(source_term, risky, "major", "literary_term_risk", rule))
        return flags

    def _flag(
        self,
        source_term: str,
        target_evidence: str,
        severity: str,
        flag_type: str,
        rule: Dict[str, List[str]],
    ) -> Flag:
        return {
            "type": flag_type,
            "source_term": source_term,
            "target_evidence": target_evidence,
            "severity": severity,
            "suggested_senses": rule.get("suggested_senses", []),
            "recommendation": f"review {source_term} translation",
        }


class SourceTargetConsistencyChecker:
    """Flag missing source entities and numeric/unit anomalies."""

    def check(self, source_text: str, target_text: str) -> List[Flag]:
        flags: List[Flag] = []
        source = source_text or ""
        target = target_text or ""
        source_folded = source.casefold()
        target_folded = target.casefold()

        for entity, variants in ENTITY_VARIANTS.items():
            if entity.casefold() not in source_folded:
                continue
            if not any(variant.casefold() in target_folded for variant in variants):
                flags.append(
                    {
                        "type": "missing_source_entity",
                        "source_entity": entity,
                        "severity": "major",
                        "recommendation": "review entity preservation or accepted localization",
                    }
                )

        if "seven foot" in source_folded and re.search(r"\bfittik\b", target_folded):
            flags.append(
                {
                    "type": "unit_or_typo_risk",
                    "evidence": "fittik",
                    "severity": "major",
                    "recommendation": "review unit rendering",
                }
            )
        elif re.search(r"\bfittik\b", target_folded):
            flags.append(
                {
                    "type": "unit_or_typo_risk",
                    "evidence": "fittik",
                    "severity": "major",
                    "recommendation": "review typo-like unit rendering",
                }
            )

        return flags


class LiterarySemanticQAChecker:
    """Aggregate deterministic semantic QA flags for source-target pairs."""

    def __init__(
        self,
        term_detector: Optional[LiteraryTermRiskDetector] = None,
        consistency_checker: Optional[SourceTargetConsistencyChecker] = None,
    ):
        self.term_detector = term_detector or LiteraryTermRiskDetector()
        self.consistency_checker = consistency_checker or SourceTargetConsistencyChecker()

    def check(self, source_text: str, target_text: str) -> Dict[str, Any]:
        flags = []
        flags.extend(self.term_detector.detect(source_text, target_text))
        flags.extend(self.consistency_checker.check(source_text, target_text))
        recommendation = "accept"
        if any(flag["severity"] == "critical" for flag in flags):
            recommendation = "review"
        elif flags:
            recommendation = "review"
        return {"flags": flags, "recommendation": recommendation}
