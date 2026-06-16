"""Deterministic Turkish fluency anomaly QA."""

from __future__ import annotations

import re
from typing import Any, Dict, List


Flag = Dict[str, Any]


SUSPICIOUS_PHRASES = [
    ("gözlerini kafeslerler", "literal_calque_or_nonsense", "critical", "review unnatural literal phrase"),
    ("gozlerini kafeslerler", "literal_calque_or_nonsense", "critical", "review unnatural literal phrase"),
    ("dolu salonda oynuyordu", "register_semantic_oddity", "major", "review preaching/full-house rendering"),
    ("içkiye yatar", "suspicious_literary_phrase", "minor", "review idiomatic Turkish rendering"),
    ("ickiye yatar", "suspicious_literary_phrase", "minor", "review idiomatic Turkish rendering"),
    ("akılsız bir şiddete eğilim", "suspicious_literary_phrase", "major", "review phrase naturalness"),
    ("akilsiz bir siddete egilim", "suspicious_literary_phrase", "major", "review phrase naturalness"),
]


class TurkishGrammarRiskDetector:
    """Flag broken deterministic Turkish grammar patterns."""

    def detect(self, text: str) -> List[Flag]:
        value = text or ""
        folded = value.casefold()
        flags: List[Flag] = []

        if re.search(r"\bne\s+okuyup\s+yazma\s+bilir\s+ne\s+de\b", folded):
            flags.append(
                {
                    "type": "broken_turkish_grammar",
                    "evidence": "Ne okuyup yazma bilir ne de",
                    "severity": "critical",
                    "recommendation": "review malformed Turkish phrase",
                }
            )

        if re.search(r"\bfittik\b", folded):
            flags.append(
                {
                    "type": "unit_or_typo_risk",
                    "evidence": "fittik",
                    "severity": "major",
                    "recommendation": "review unit rendering typo",
                }
            )

        for match in re.finditer(r"\S  \S", value):
            start = max(0, match.start() - 20)
            end = min(len(value), match.end() + 20)
            flags.append(
                {
                    "type": "double_space",
                    "evidence": value[start:end].strip(),
                    "severity": "minor",
                    "recommendation": "remove accidental double space",
                }
            )

        return flags


class LiteraryRegisterRiskDetector:
    """Flag suspicious literary register and literal-calque phrases."""

    def detect(self, text: str) -> List[Flag]:
        folded = (text or "").casefold()
        flags: List[Flag] = []
        for phrase, flag_type, severity, recommendation in SUSPICIOUS_PHRASES:
            if phrase.casefold() in folded:
                flags.append(
                    {
                        "type": flag_type,
                        "evidence": phrase,
                        "severity": severity,
                        "recommendation": recommendation,
                    }
                )
        return flags


class TurkishFluencyAnomalyChecker:
    """Aggregate deterministic Turkish fluency anomaly flags."""

    def __init__(self):
        self.grammar_detector = TurkishGrammarRiskDetector()
        self.register_detector = LiteraryRegisterRiskDetector()

    def check(self, target_text: str) -> Dict[str, Any]:
        flags: List[Flag] = []
        flags.extend(self.grammar_detector.detect(target_text))
        flags.extend(self.register_detector.detect(target_text))
        score = self._score(flags)
        recommendation = "accept"
        if any(flag["severity"] == "critical" for flag in flags):
            recommendation = "review"
        elif flags:
            recommendation = "review"
        return {"fluency_score": score, "flags": flags, "recommendation": recommendation}

    def _score(self, flags: List[Flag]) -> float:
        score = 1.0
        for flag in flags:
            if flag["severity"] == "critical":
                score -= 0.35
            elif flag["severity"] == "major":
                score -= 0.2
            elif flag["severity"] == "minor":
                score -= 0.08
        return round(max(0.0, score), 2)
