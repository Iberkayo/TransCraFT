"""Source extraction cleanup and quality checks for PDF-derived text.

The cleaner is intentionally conservative: it repairs only high-confidence
extraction artifacts and reports uncertain merged tokens for review.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional


Repair = Dict[str, Any]
Flag = Dict[str, Any]


REPAIR_MAP = {
    "stokesthe": "stokes the",
    "woodsbeyond": "woods beyond",
    "asolitary": "a solitary",
    "Hisshoulders": "His shoulders",
    "hequotes": "he quotes",
    "watcheshim": "watches him",
    "starsdid": "stars did",
    "creaturewho": "creature who",
    "thepredawn": "the predawn",
    "kitchenhouse": "kitchen house",
}

COMMON_LONG_WORDS = {
    "circumstances",
    "nevertheless",
    "understanding",
    "responsibility",
    "characteristically",
    "notwithstanding",
    "unquestionable",
    "extraordinary",
    "consequently",
    "superintendent",
}


class SourceExtractionCleaner:
    """Repair common PDF extraction artifacts without guessing aggressively."""

    def clean(
        self,
        text: str,
        source_language: str = "en_US",
        document_type: str = "pdf",
        genre: str = "literary_fiction",
    ) -> Dict[str, Any]:
        del source_language, document_type, genre

        original = text or ""
        cleaned = original
        repairs: List[Repair] = []

        cleaned = self._repair_hyphenation(cleaned, repairs)
        cleaned = self._apply_repair_map(cleaned, repairs)
        cleaned = self._repair_punctuation_spacing(cleaned, repairs)
        cleaned = self._normalize_paragraph_spacing(cleaned, repairs)

        flags = self._quality_flags(cleaned)
        recommendation = self._recommendation(flags)

        return {
            "original_text": original,
            "cleaned_text": cleaned,
            "changed": cleaned != original,
            "repairs": repairs,
            "quality_flags": flags,
            "recommendation": recommendation,
        }

    def _apply_repair_map(self, text: str, repairs: List[Repair]) -> str:
        cleaned = text
        for before, after in REPAIR_MAP.items():
            pattern = re.compile(rf"\b{re.escape(before)}\b")
            matches = list(pattern.finditer(cleaned))
            if not matches:
                continue
            cleaned = pattern.sub(after, cleaned)
            for _ in matches:
                repairs.append(
                    {
                        "type": "merged_word_repair",
                        "before": before,
                        "after": after,
                        "confidence": "high",
                    }
                )
        return cleaned

    def _repair_punctuation_spacing(self, text: str, repairs: List[Repair]) -> str:
        pattern = re.compile(r"([.!?,;:])(?=[A-Za-z])")
        matches = list(pattern.finditer(text))
        if not matches:
            return text
        repairs.append(
            {
                "type": "punctuation_spacing_repair",
                "before": "missing space after punctuation",
                "after": "space after punctuation",
                "confidence": "high",
                "count": len(matches),
            }
        )
        return pattern.sub(r"\1 ", text)

    def _repair_hyphenation(self, text: str, repairs: List[Repair]) -> str:
        pattern = re.compile(r"\b([A-Za-z]{3,})-\s*\n\s*([a-z]{3,})\b")
        matches = list(pattern.finditer(text))
        if not matches:
            return text
        repairs.append(
            {
                "type": "hyphenation_repair",
                "before": "line-break hyphenation",
                "after": "joined token",
                "confidence": "medium",
                "count": len(matches),
            }
        )
        return pattern.sub(r"\1\2", text)

    def _normalize_paragraph_spacing(self, text: str, repairs: List[Repair]) -> str:
        if not text:
            return text

        paragraphs = re.split(r"\n\s*\n", text.strip())
        normalized_paragraphs = []
        changed = False
        for paragraph in paragraphs:
            normalized = re.sub(r"[ \t]*\n[ \t]*", " ", paragraph)
            normalized = re.sub(r"[ \t]{2,}", " ", normalized).strip()
            if normalized != paragraph.strip():
                changed = True
            if normalized:
                normalized_paragraphs.append(normalized)

        result = "\n\n".join(normalized_paragraphs)
        if changed:
            repairs.append(
                {
                    "type": "paragraph_spacing_repair",
                    "before": "PDF line breaks inside paragraph",
                    "after": "normalized spaces while preserving paragraph breaks",
                    "confidence": "medium",
                }
            )
        return result

    def _quality_flags(self, text: str) -> List[Flag]:
        flags: List[Flag] = []

        for token in suspicious_merged_tokens(text):
            flags.append(
                {
                    "type": "suspected_merged_token",
                    "evidence": token,
                    "recommendation": "review source extraction",
                }
            )

        missing_spaces = re.findall(r"[.!?,;:][A-Za-z]", text)
        if missing_spaces:
            flags.append(
                {
                    "type": "missing_punctuation_space",
                    "evidence": missing_spaces[:5],
                    "count": len(missing_spaces),
                    "recommendation": "review punctuation spacing",
                }
            )

        if looks_truncated(text):
            flags.append(
                {
                    "type": "abrupt_truncation",
                    "evidence": text[-80:].strip(),
                    "recommendation": "reject or re-extract chapter boundary",
                }
            )

        return flags

    @staticmethod
    def _recommendation(flags: List[Flag]) -> str:
        if any(flag["type"] == "abrupt_truncation" for flag in flags):
            return "reject"
        if len(flags) >= 3 or any(flag["type"] == "suspected_merged_token" for flag in flags):
            return "review"
        return "accept"


class SourceExtractionQualityChecker:
    """Score whether extracted source is safe to translate."""

    def check(
        self,
        text: str,
        source_language: str = "en_US",
        document_type: str = "pdf",
        genre: str = "literary_fiction",
    ) -> Dict[str, Any]:
        del source_language, document_type, genre

        value = text or ""
        flags: List[Flag] = []

        suspicious = suspicious_merged_tokens(value)
        if suspicious:
            flags.append(
                {
                    "type": "suspicious_long_lowercase_tokens",
                    "count": len(suspicious),
                    "evidence": suspicious[:10],
                    "recommendation": "review source extraction",
                }
            )

        camel_joins = re.findall(r"\b[A-Z][a-z]+[A-Z][a-z]+\b", value)
        if camel_joins:
            flags.append(
                {
                    "type": "unusual_camel_case_join",
                    "count": len(camel_joins),
                    "evidence": camel_joins[:10],
                    "recommendation": "review merged words",
                }
            )

        missing_spaces = re.findall(r"[.!?,;:][A-Za-z]", value)
        if missing_spaces:
            flags.append(
                {
                    "type": "missing_spaces_after_punctuation",
                    "count": len(missing_spaces),
                    "evidence": missing_spaces[:10],
                    "recommendation": "run source cleanup",
                }
            )

        repeated = repeated_suspicious_tokens(suspicious)
        if repeated:
            flags.append(
                {
                    "type": "repeated_merged_words",
                    "evidence": repeated,
                    "recommendation": "review extraction settings",
                }
            )

        artifact_count = len(re.findall(r"[^\w\s.,;:!?'\-\"()]", value))
        if artifact_count > max(5, len(value) // 200):
            flags.append(
                {
                    "type": "non_word_artifacts",
                    "count": artifact_count,
                    "recommendation": "review PDF extraction artifacts",
                }
            )

        if looks_truncated(value):
            flags.append(
                {
                    "type": "abrupt_truncation",
                    "evidence": value[-100:].strip(),
                    "recommendation": "reject or re-extract chapter boundary",
                }
            )

        score = quality_score(value, flags)
        recommendation = "accept"
        if any(flag["type"] == "abrupt_truncation" for flag in flags):
            recommendation = "reject"
        elif score < 0.78 or flags:
            recommendation = "review"

        return {
            "quality_score": score,
            "flags": flags,
            "should_translate": recommendation != "reject",
            "recommendation": recommendation,
        }


def suspicious_merged_tokens(text: str) -> List[str]:
    tokens = re.findall(r"\b[a-z]{14,}\b", text or "")
    suspicious = []
    for token in tokens:
        if token in COMMON_LONG_WORDS:
            continue
        if re.search(r"(the|and|with|who|his|her|their|beyond|before|after)$", token):
            suspicious.append(token)
            continue
        if len(token) >= 18:
            suspicious.append(token)
    return list(dict.fromkeys(suspicious))


def repeated_suspicious_tokens(tokens: List[str]) -> List[str]:
    counts = Counter(tokens)
    return [token for token, count in counts.items() if count > 1]


def looks_truncated(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if len(stripped) < 80:
        return False
    if stripped.endswith((".", "!", "?", '"', "'", ")", "]")):
        return False
    tail_words = re.findall(r"\b\w+\b", stripped[-80:])
    if tail_words and len(tail_words[-1]) <= 2:
        return True
    return len(tail_words) < 5 or bool(re.search(r"\b[a-z]{1,3}$", stripped))


def quality_score(text: str, flags: List[Flag]) -> float:
    if not text or not text.strip():
        return 0.0
    penalty = 0.0
    for flag in flags:
        flag_type = flag.get("type")
        count = int(flag.get("count", 1) or 1)
        if flag_type == "abrupt_truncation":
            penalty += 0.35
        elif flag_type in {"suspicious_long_lowercase_tokens", "unusual_camel_case_join"}:
            penalty += min(0.25, 0.06 * count)
        elif flag_type == "missing_spaces_after_punctuation":
            penalty += min(0.18, 0.03 * count)
        elif flag_type == "non_word_artifacts":
            penalty += min(0.12, 0.01 * count)
        else:
            penalty += 0.04
    return round(max(0.0, min(1.0, 1.0 - penalty)), 2)
