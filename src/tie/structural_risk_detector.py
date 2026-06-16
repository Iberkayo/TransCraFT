"""Lightweight source-side structural risk detection for strategy planning."""

import re
from typing import Dict, List


class StructuralRiskDetector:
    """Detect simple translation risks without heavy NLP dependencies."""

    PHRASAL_VERBS = {
        "follow up",
        "phase out",
        "carry out",
        "put off",
        "look into",
        "set up",
        "roll out",
        "break down",
        "bring up",
        "turn down",
        "move forward",
    }
    IDIOM_MARKERS = {
        "cold water",
        "green light",
        "red tape",
        "silver bullet",
        "moving target",
        "under the microscope",
        "bottleneck",
        "opened the door",
    }
    PRONOUNS = {"he", "she", "it", "they", "them", "him", "her", "his", "their", "its"}
    PREPOSITIONS = {"of", "for", "with", "in", "on", "by", "from", "about", "between", "through", "after", "before"}
    STOPWORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "before",
        "after",
        "with",
        "without",
        "for",
        "of",
        "in",
        "on",
        "by",
        "from",
    }

    def detect(self, source_text: str, genre: str = "general") -> List[Dict[str, str]]:
        text = source_text or ""
        lower = text.casefold()
        risks: List[Dict[str, str]] = []

        self._detect_long_sentence(text, risks)
        self._detect_long_relative_clause(text, risks)
        self._detect_noun_stack(text, risks)
        self._detect_passive_voice(text, risks)
        self._detect_phrasal_verb(lower, risks)
        self._detect_idiom_or_metaphor(lower, risks)
        self._detect_pronoun_heavy(lower, risks)
        self._detect_preposition_heavy(lower, risks)
        self._detect_literary_fragment(text, genre, risks)
        self._detect_business_translationese(lower, risks)
        self._detect_academic_nominalization(lower, genre, risks)
        return risks

    def _add(
        self,
        risks: List[Dict[str, str]],
        risk_type: str,
        evidence: str,
        translation_risk: str,
        recommended_strategy: str,
    ) -> None:
        if any(r["risk_type"] == risk_type and r["evidence"] == evidence for r in risks):
            return
        risks.append(
            {
                "risk_type": risk_type,
                "evidence": self._compact(evidence),
                "translation_risk": translation_risk,
                "recommended_strategy": recommended_strategy,
            }
        )

    def _detect_long_sentence(self, text: str, risks: List[Dict[str, str]]) -> None:
        if len(self._words(text)) >= 24:
            self._add(
                risks,
                "long_sentence",
                text,
                "A long source sentence may become heavy or unclear in Turkish.",
                "Split into natural Turkish sentence units when readability improves.",
            )

    def _detect_long_relative_clause(self, text: str, risks: List[Dict[str, str]]) -> None:
        match = re.search(r"([,;]?\s*(a decision|which|that|who|whose|where)\b[^.!?;]{18,})", text, re.IGNORECASE)
        if match:
            self._add(
                risks,
                "long_relative_clause",
                match.group(1),
                "Literal English clause order may create unnatural Turkish.",
                "Split into two Turkish sentences and reconstruct causality naturally.",
            )

    def _detect_noun_stack(self, text: str, risks: List[Dict[str, str]]) -> None:
        tokens = self._words(text)
        best: List[str] = []
        current: List[str] = []
        for token in tokens:
            if token.casefold() in self.STOPWORDS:
                if len(current) > len(best):
                    best = current
                current = []
                continue
            current.append(token)
        if len(current) > len(best):
            best = current
        if len(best) >= 4:
            evidence = " ".join(best[:7])
            self._add(
                risks,
                "noun_stack",
                evidence,
                "Stacked English modifiers may become an opaque Turkish noun chain.",
                "Unpack the stack into a clear possessive or explanatory Turkish phrase.",
            )

    def _detect_passive_voice(self, text: str, risks: List[Dict[str, str]]) -> None:
        pattern = r"\b(is|are|was|were|be|been|being|expected to be)\s+\w+(ed|en)\b|\bwas\s+\w+ed\s+by\b|\bwere\s+\w+ed\s+by\b"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            evidence_match = re.search(pattern, text, re.IGNORECASE)
            self._add(
                risks,
                "passive_voice",
                evidence_match.group(0) if evidence_match else text,
                "Mechanical passive transfer may sound stiff or obscure agency.",
                "Decide whether Turkish should keep passive voice or use a natural active structure.",
            )
        if len(matches) >= 2:
            self._add(
                risks,
                "double_passive",
                text,
                "Multiple passive verbs can make Turkish bureaucratic and heavy.",
                "Reduce passive stacking where meaning allows.",
            )

    def _detect_phrasal_verb(self, lower: str, risks: List[Dict[str, str]]) -> None:
        for phrase in sorted(self.PHRASAL_VERBS):
            if phrase in lower:
                self._add(
                    risks,
                    "phrasal_verb",
                    phrase,
                    "English phrasal verbs often lose meaning when translated word by word.",
                    "Translate the phrasal verb by its actual function in the sentence.",
                )

    def _detect_idiom_or_metaphor(self, lower: str, risks: List[Dict[str, str]]) -> None:
        for marker in sorted(self.IDIOM_MARKERS):
            if marker in lower:
                self._add(
                    risks,
                    "idiom_or_metaphor",
                    marker,
                    "Literal transfer may preserve words while losing the intended effect.",
                    "Use a natural Turkish idiom or plain meaning that carries the same effect.",
                )

    def _detect_pronoun_heavy(self, lower: str, risks: List[Dict[str, str]]) -> None:
        pronouns = [w for w in self._words(lower) if w in self.PRONOUNS]
        if len(pronouns) >= 4:
            self._add(
                risks,
                "pronoun_heavy",
                " ".join(pronouns[:8]),
                "Repeating explicit pronouns can sound unnatural or create ambiguity in Turkish.",
                "Drop unnecessary pronouns while preserving reference clarity.",
            )

    def _detect_preposition_heavy(self, lower: str, risks: List[Dict[str, str]]) -> None:
        preps = [w for w in self._words(lower) if w in self.PREPOSITIONS]
        if len(preps) >= 4:
            self._add(
                risks,
                "preposition_heavy",
                " ".join(preps[:8]),
                "English prepositional chains may produce literal and tangled Turkish order.",
                "Reorder the sentence around natural Turkish case relations and verbs.",
            )

    def _detect_literary_fragment(self, text: str, genre: str, risks: List[Dict[str, str]]) -> None:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        fragments = [p for p in parts if len(self._words(p)) <= 3]
        if genre == "literary" and len(fragments) >= 2:
            self._add(
                risks,
                "literary_fragment",
                " / ".join(fragments[:4]),
                "Explaining fragments can flatten rhythm and voice.",
                "Preserve intentional fragments and implied subjects where Turkish allows.",
            )

    def _detect_business_translationese(self, lower: str, risks: List[Dict[str, str]]) -> None:
        markers = [
            "has left",
            "have left",
            "a decision which",
            "expected to be",
            "at the expense of",
            "wondering how",
        ]
        evidence = next((m for m in markers if m in lower), "")
        if evidence:
            self._add(
                risks,
                "business_translationese_risk",
                evidence,
                "Literal business phrasing may lead to stiff Turkish such as 'neden oldu'.",
                "Use natural corporate Turkish such as 'soru isaretleri yaratti' or 'endise yaratti' when meaning fits.",
            )

    def _detect_academic_nominalization(self, lower: str, genre: str, risks: List[Dict[str, str]]) -> None:
        nominalizations = re.findall(r"\b\w+(tion|sion|ment|ity|ance|ence|ship)\b", lower)
        if genre in {"academic", "tech"} and len(nominalizations) >= 2:
            self._add(
                risks,
                "academic_nominalization",
                lower,
                "Dense nominalizations may make Turkish academic prose abstract and heavy.",
                "Use clear Turkish academic phrasing and turn nominal piles into readable clauses when needed.",
            )

    def _words(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-z][A-Za-z'-]*", text)

    def _compact(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
