"""Foreign residue QA for Turkish translation outputs.

Detects likely untranslated English residue while allowing protected names,
places, titles, and glossary terms.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Set


Residue = Dict[str, Any]


DEFAULT_PROTECTED_TERMS = {
    "Memphis",
    "Saint Louis",
    "New Orleans",
    "Leonids",
    "Dipper",
    "Tennessee",
    "Texas",
    "Galveston",
    "Nacogdoches",
    "Fredonia",
    "Judge Holden",
    "Toadvine",
}

CRITICAL_PHRASES = [
    "All races, all breeds",
]

CRITICAL_TOKENS = {
    "Hisshoulders",
    "Blacks",
    "Men",
}

ENGLISH_FUNCTION_WORDS = {
    "all",
    "the",
    "and",
    "with",
    "whose",
    "which",
    "that",
    "his",
    "their",
    "of",
    "for",
}

STRONG_ENGLISH_FUNCTION_WORDS = {
    "all",
    "the",
    "and",
    "with",
    "whose",
    "which",
    "that",
    "his",
    "their",
}

TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")

COMMON_ENGLISH_NOUNS = {
    "child",
    "fire",
    "woods",
    "fields",
    "shoulders",
    "races",
    "breeds",
    "men",
    "black",
    "blacks",
    "water",
    "father",
    "mother",
    "night",
}


class ForeignResidueDetector:
    """Detect untranslated English fragments in Turkish output."""

    def detect(
        self,
        translated_text: str,
        target_language: str = "tr_TR",
        allowed_terms: Optional[Iterable[str]] = None,
        protected_terms: Optional[Iterable[str]] = None,
        proper_nouns: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        if not translated_text:
            return {
                "foreign_residue_count": 0,
                "residues": [],
                "recommendation": "accept",
            }

        if not target_language.startswith("tr"):
            return {
                "foreign_residue_count": 0,
                "residues": [],
                "recommendation": "accept",
            }

        protected = self._protected_set(allowed_terms, protected_terms, proper_nouns)
        residues: List[Residue] = []

        residues.extend(self._detect_critical_phrases(translated_text, protected))
        residues.extend(self._detect_critical_tokens(translated_text, protected))
        residues.extend(self._detect_function_word_phrases(translated_text, protected))
        residues.extend(self._detect_camel_or_merged(translated_text, protected))
        residues.extend(self._detect_english_nouns(translated_text, protected))

        residues = dedupe_residues(residues)
        recommendation = self._recommendation(residues)

        return {
            "foreign_residue_count": len(residues),
            "residues": residues,
            "recommendation": recommendation,
        }

    def _protected_set(
        self,
        allowed_terms: Optional[Iterable[str]],
        protected_terms: Optional[Iterable[str]],
        proper_nouns: Optional[Iterable[str]],
    ) -> Set[str]:
        values = set(DEFAULT_PROTECTED_TERMS)
        for terms in (allowed_terms, protected_terms, proper_nouns):
            if terms:
                values.update(str(term) for term in terms if term)
        expanded = set(values)
        for value in list(values):
            expanded.update(part for part in re.split(r"\s+", value) if part)
        return {value.casefold() for value in expanded}

    def _is_protected(self, text: str, protected: Set[str]) -> bool:
        if text.casefold() in protected:
            return True
        normalized = re.sub(r"[^\w\s]", "", text).strip().casefold()
        return normalized in protected

    def _detect_critical_phrases(self, text: str, protected: Set[str]) -> List[Residue]:
        residues = []
        for phrase in CRITICAL_PHRASES:
            if phrase in text and not self._is_protected(phrase, protected):
                residues.append(
                    {
                        "text": phrase,
                        "type": "english_phrase",
                        "severity": "critical",
                        "recommendation": "translate or review",
                    }
                )
        return residues

    def _detect_critical_tokens(self, text: str, protected: Set[str]) -> List[Residue]:
        residues = []
        for token in CRITICAL_TOKENS:
            if re.search(rf"\b{re.escape(token)}\b", text) and not self._is_protected(token, protected):
                residues.append(
                    {
                        "text": token,
                        "type": "english_token",
                        "severity": "critical",
                        "recommendation": "translate or review",
                    }
                )
        return residues

    def _detect_function_word_phrases(self, text: str, protected: Set[str]) -> List[Residue]:
        residues = []
        sentence_parts = re.split(r"(?<=[.!?])\s+|[\n;]", text)
        for part in sentence_parts:
            words = re.findall(r"\b[A-Za-z][A-Za-z']+\b", part)
            unprotected = [word for word in words if not self._is_protected(word, protected)]
            if not unprotected:
                continue
            function_hits = [word for word in unprotected if word.casefold() in ENGLISH_FUNCTION_WORDS]
            strong_hits = [word for word in function_hits if word.casefold() in STRONG_ENGLISH_FUNCTION_WORDS]
            has_turkish_chars = any(char in TURKISH_CHARS for char in part)
            if len(function_hits) >= 2 or (function_hits and len(unprotected) >= 4):
                if has_turkish_chars and not strong_hits:
                    continue
                residues.append(
                    {
                        "text": part.strip()[:120],
                        "type": "english_function_word_phrase",
                        "severity": "critical",
                        "recommendation": "translate sentence fragment or review",
                    }
                )
        return residues

    def _detect_camel_or_merged(self, text: str, protected: Set[str]) -> List[Residue]:
        residues = []
        for token in re.findall(r"\b[A-Za-z]{10,}\b", text):
            if self._is_protected(token, protected):
                continue
            if re.search(r"[a-z][A-Z]", token) or token.casefold().endswith(("the", "and", "his", "her", "their")):
                residues.append(
                    {
                        "text": token,
                        "type": "english_merged_or_camel_token",
                        "severity": "critical",
                        "recommendation": "repair source or translate residue",
                    }
                )
        return residues

    def _detect_english_nouns(self, text: str, protected: Set[str]) -> List[Residue]:
        residues = []
        for token in re.findall(r"\b[A-Za-z][A-Za-z']*\b", text):
            if self._is_protected(token, protected):
                continue
            folded = token.casefold().strip("'")
            if folded in COMMON_ENGLISH_NOUNS:
                severity = "critical" if folded in {"men", "blacks"} else "review"
                residues.append(
                    {
                        "text": token,
                        "type": "untranslated_english_noun",
                        "severity": severity,
                        "recommendation": "translate or confirm intentional protected term",
                    }
                )
        return residues

    @staticmethod
    def _recommendation(residues: List[Residue]) -> str:
        if any(residue.get("severity") == "critical" for residue in residues):
            return "reject"
        if residues:
            return "review"
        return "accept"


class TargetLanguageResidueChecker:
    """Wrapper name for use in target-side QA workflows."""

    def __init__(self, detector: Optional[ForeignResidueDetector] = None):
        self.detector = detector or ForeignResidueDetector()

    def check(
        self,
        translated_text: str,
        target_language: str = "tr_TR",
        allowed_terms: Optional[Iterable[str]] = None,
        protected_terms: Optional[Iterable[str]] = None,
        proper_nouns: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        return self.detector.detect(
            translated_text=translated_text,
            target_language=target_language,
            allowed_terms=allowed_terms,
            protected_terms=protected_terms,
            proper_nouns=proper_nouns,
        )


def dedupe_residues(residues: List[Residue]) -> List[Residue]:
    seen = set()
    deduped = []
    for residue in residues:
        key = (residue.get("text"), residue.get("type"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(residue)
    return deduped
