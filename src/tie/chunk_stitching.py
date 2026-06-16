"""Sentence-safe chunking and chunk boundary QA."""

from __future__ import annotations

import re
from typing import Any, Dict, List


Flag = Dict[str, Any]

CONTINUATION_STARTS = {
    "itself",
    "and",
    "but",
    "which",
    "that",
    "whose",
    "where",
}


class ChunkBoundaryQualityChecker:
    """Detect risky source chunk boundaries before translation."""

    def check(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        text = (chunk.get("text") or "").strip()
        chunk_id = chunk.get("chunk_id", "chunk")
        flags: List[Flag] = []

        if not text:
            flags.append(
                {
                    "type": "empty_chunk",
                    "evidence": "",
                    "severity": "critical",
                    "recommendation": "drop empty chunk",
                }
            )
            return {"chunk_id": chunk_id, "flags": flags, "recommendation": "reject"}

        first_words = " ".join(re.findall(r"\b\w+\b", text[:80])[:4])
        first_token = re.search(r"\b[A-Za-z]+\b", text)
        if first_token:
            token = first_token.group(0)
            if token[0].islower():
                flags.append(
                    {
                        "type": "lowercase_chunk_start",
                        "evidence": first_words,
                        "severity": "major",
                        "recommendation": "merge with previous chunk or adjust boundary",
                    }
                )
            if token.casefold() in CONTINUATION_STARTS:
                flags.append(
                    {
                        "type": "continuation_chunk_start",
                        "evidence": first_words,
                        "severity": "major",
                        "recommendation": "merge with previous chunk or adjust boundary",
                    }
                )

        if self._ends_mid_sentence(text):
            flags.append(
                {
                    "type": "unfinished_sentence_end",
                    "evidence": text[-100:].strip(),
                    "severity": "major",
                    "recommendation": "extend chunk to sentence boundary",
                }
            )

        recommendation = "accept"
        if any(flag["severity"] == "critical" for flag in flags):
            recommendation = "reject"
        elif flags:
            recommendation = "review"
        return {"chunk_id": chunk_id, "flags": flags, "recommendation": recommendation}

    def _ends_mid_sentence(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return True
        if stripped.endswith((".", "!", "?", '"', "'", ")", "]")):
            return False
        # Allow short literary fragments only when punctuation-complete.
        return True


class SentenceSafeChunker:
    """Chunk text with paragraph-first, sentence-second boundaries."""

    def __init__(self, max_chars: int = 3200):
        self.max_chars = max_chars
        self.boundary_checker = ChunkBoundaryQualityChecker()

    def chunk_text(self, text: str, chunk_id_prefix: str = "chunk") -> Dict[str, Any]:
        value = (text or "").strip()
        units = self._paragraph_sentence_units(value)
        chunks: List[Dict[str, Any]] = []
        current: List[str] = []
        start_offset = 0
        cursor = 0

        for unit in units:
            unit_len = len(unit)
            joined = "\n\n".join(current + [unit]) if current else unit
            if current and len(joined) > self.max_chars:
                chunk_text = "\n\n".join(current).strip()
                chunks.append(self._make_chunk(chunk_id_prefix, len(chunks) + 1, chunk_text, start_offset, cursor))
                start_offset = cursor
                current = []
            current.append(unit)
            cursor += unit_len + 2

        if current:
            chunk_text = "\n\n".join(current).strip()
            chunks.append(self._make_chunk(chunk_id_prefix, len(chunks) + 1, chunk_text, start_offset, min(len(value), cursor)))

        global_flags = []
        recommendation = "accept"
        for chunk in chunks:
            check = self.boundary_checker.check(chunk)
            chunk["boundary_flags"] = check["flags"]
            chunk["recommendation"] = check["recommendation"]
            if check["recommendation"] != "accept":
                global_flags.extend(check["flags"])
                recommendation = "review" if recommendation != "reject" else recommendation
            if check["recommendation"] == "reject":
                recommendation = "reject"

        return {"chunks": chunks, "global_flags": global_flags, "recommendation": recommendation}

    def _make_chunk(self, prefix: str, index: int, text: str, start: int, end: int) -> Dict[str, Any]:
        return {
            "chunk_id": f"{prefix}_{index:02d}",
            "text": text,
            "start_offset": start,
            "end_offset": end,
            "boundary_flags": [],
            "recommendation": "accept",
        }

    def _paragraph_sentence_units(self, text: str) -> List[str]:
        units: List[str] = []
        paragraphs = self._merge_continuation_paragraphs(
            [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        )
        for paragraph in paragraphs:
            if len(paragraph) <= self.max_chars:
                units.append(paragraph)
            else:
                units.extend(self._split_paragraph_by_sentence(paragraph))
        return units

    def _merge_continuation_paragraphs(self, paragraphs: List[str]) -> List[str]:
        if not paragraphs:
            return []
        merged: List[str] = []
        for paragraph in paragraphs:
            if not merged:
                merged.append(paragraph)
                continue
            previous = merged[-1].strip()
            if self._should_stitch(previous, paragraph):
                merged[-1] = f"{previous} {paragraph.strip()}"
            else:
                merged.append(paragraph)
        return merged

    def _should_stitch(self, previous: str, current: str) -> bool:
        if self.boundary_checker._ends_mid_sentence(previous):
            return True
        first = re.search(r"\b[A-Za-z]+\b", current or "")
        if not first:
            return False
        token = first.group(0)
        return token[0].islower() or token.casefold() in CONTINUATION_STARTS

    def _split_paragraph_by_sentence(self, paragraph: str) -> List[str]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()]
        units: List[str] = []
        current: List[str] = []
        for sentence in sentences:
            joined = " ".join(current + [sentence]) if current else sentence
            if current and len(joined) > self.max_chars:
                units.append(" ".join(current).strip())
                current = []
            if len(sentence) > self.max_chars:
                units.extend(self._split_long_sentence(sentence))
            else:
                current.append(sentence)
        if current:
            units.append(" ".join(current).strip())
        return units

    def _split_long_sentence(self, sentence: str) -> List[str]:
        # Sentence safety has priority over the nominal chunk size. A single
        # long literary sentence is safer as an oversized chunk than as two
        # grammatically orphaned chunks.
        return [sentence.strip()]


class ChunkStitchingReviewer:
    """Review a list of chunks for stitching risks."""

    def __init__(self):
        self.boundary_checker = ChunkBoundaryQualityChecker()

    def review(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        reviews = [self.boundary_checker.check(chunk) for chunk in chunks]
        global_flags = [flag for review in reviews for flag in review["flags"]]
        recommendation = "accept"
        if any(review["recommendation"] == "reject" for review in reviews):
            recommendation = "reject"
        elif any(review["recommendation"] == "review" for review in reviews):
            recommendation = "review"
        return {"chunk_reviews": reviews, "global_flags": global_flags, "recommendation": recommendation}
