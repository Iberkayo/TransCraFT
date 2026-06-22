"""Generic, reference-only translation memory retrieval.

This module reads local private TM artifacts created by v0.9.5. Retrieved
examples are evidence for human review, never automatic translation truth.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
DEFAULT_WARNINGS = [
    "Translation memory references are local private reference material.",
    "Retrieved examples require human review.",
    "Do not treat retrieved translations as automatically correct.",
]


@dataclass
class TranslationMemoryEntry:
    """Tolerant representation of a v0.9.5 translation-memory entry."""

    tm_id: str
    pair_id: str = "unknown_pair"
    source_lang: str = "EN"
    target_lang: str = "TR"
    source_text: str = ""
    target_text: str = ""
    source_word_count: int = 0
    target_word_count: int = 0
    alignment_confidence: str = "low"
    domain_profile: Dict[str, Any] = field(default_factory=dict)
    usage_policy: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_path: Optional[str] = None) -> "TranslationMemoryEntry":
        source_text = str(data.get("source_text") or "")
        target_text = str(data.get("target_text") or "")
        confidence = str(data.get("alignment_confidence") or "low").casefold()
        if confidence not in CONFIDENCE_RANK:
            confidence = "low"
        policy = data.get("usage_policy")
        if not isinstance(policy, dict):
            policy = {}
        policy = {
            "scope": policy.get("scope", "local_private_reference"),
            "do_not_commit_full_text": bool(policy.get("do_not_commit_full_text", True)),
            **policy,
        }
        return cls(
            tm_id=str(data.get("tm_id") or _fallback_tm_id(data)),
            pair_id=str(data.get("pair_id") or "unknown_pair"),
            source_lang=str(data.get("source_lang") or "EN"),
            target_lang=str(data.get("target_lang") or "TR"),
            source_text=source_text,
            target_text=target_text,
            source_word_count=int(data.get("source_word_count") or _word_count(source_text)),
            target_word_count=int(data.get("target_word_count") or _word_count(target_text)),
            alignment_confidence=confidence,
            domain_profile=data.get("domain_profile") if isinstance(data.get("domain_profile"), dict) else {},
            usage_policy=policy,
            source_path=source_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TranslationMemoryStore:
    """Load local JSONL memories while retaining non-fatal warnings."""

    def __init__(self, entries: Optional[Iterable[Dict[str, Any]]] = None, warnings: Optional[List[str]] = None):
        self.entries = list(entries or [])
        self.warnings = list(warnings or [])

    @classmethod
    def from_directory(cls, tm_dir: str = "outputs/parallel") -> "TranslationMemoryStore":
        path = Path(tm_dir)
        if not path.exists():
            return cls([], [f"Translation memory directory does not exist: {path}"])
        files = sorted(path.glob("*_translation_memory.jsonl"))
        if not files:
            return cls([], [f"No translation memory JSONL files found under: {path}"])
        entries: List[Dict[str, Any]] = []
        warnings: List[str] = []
        for file_path in files:
            loaded, file_warnings = _load_tm_jsonl_with_warnings(file_path)
            entries.extend(loaded)
            warnings.extend(file_warnings)
        return cls(entries, warnings)

    def pair_ids(self) -> List[str]:
        return sorted({str(entry.get("pair_id") or "unknown_pair") for entry in self.entries})


class TranslationMemoryRetriever:
    """Rank local TM entries with lightweight deterministic similarity."""

    def __init__(self, entries: Iterable[Dict[str, Any]]):
        self.entries = list(entries)

    def retrieve(
        self,
        query_text: str,
        top_k: int = 5,
        min_alignment_confidence: str = "medium",
        min_score: float = 0.15,
    ) -> List[Dict[str, Any]]:
        return retrieve_translation_memory(
            query_text=query_text,
            tm_entries=self.entries,
            top_k=top_k,
            min_alignment_confidence=min_alignment_confidence,
            min_score=min_score,
        )


class ReferencePackBuilder:
    """Build a safe, explicitly reference-only result package."""

    def build(
        self,
        query_text: str,
        retrieved: List[Dict[str, Any]],
        max_chars_per_side: int = 600,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return build_reference_pack(
            query_text=query_text,
            retrieved=retrieved,
            max_chars_per_side=max_chars_per_side,
            warnings=warnings,
        )


def load_tm_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load one local TM JSONL file, skipping malformed/empty rows."""

    entries, _warnings = _load_tm_jsonl_with_warnings(Path(path))
    return entries


def load_tm_directory(tm_dir: str = "outputs/parallel") -> List[Dict[str, Any]]:
    """Load every v0.9.5 translation-memory JSONL file in a directory."""

    return TranslationMemoryStore.from_directory(tm_dir).entries


def normalize_retrieval_text(text: str) -> str:
    """Normalize text for token and character n-gram comparison."""

    value = unicodedata.normalize("NFKC", text or "").casefold()
    value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    value = value.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"[^\w\s'-]+", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def compute_similarity(query: str, candidate: str) -> float:
    """Weighted token/character overlap with a conservative length sanity check."""

    query_normalized = normalize_retrieval_text(query)
    candidate_normalized = normalize_retrieval_text(candidate)
    if not query_normalized or not candidate_normalized:
        return 0.0

    query_tokens = set(_tokens(query_normalized))
    candidate_tokens = set(_tokens(candidate_normalized))
    token_score = _jaccard(query_tokens, candidate_tokens)
    char_score = _jaccard(_char_ngrams(query_normalized, 3), _char_ngrams(candidate_normalized, 3))
    query_length = max(1, len(query_normalized))
    candidate_length = max(1, len(candidate_normalized))
    length_score = min(query_length, candidate_length) / max(query_length, candidate_length)

    containment_bonus = 0.0
    if query_normalized in candidate_normalized or candidate_normalized in query_normalized:
        containment_bonus = 0.08
    score = token_score * 0.58 + char_score * 0.32 + length_score * 0.10 + containment_bonus
    return round(min(1.0, max(0.0, score)), 6)


def retrieve_translation_memory(
    query_text: str,
    tm_entries: List[Dict[str, Any]],
    top_k: int = 5,
    min_alignment_confidence: str = "medium",
    min_score: float = 0.15,
) -> List[Dict[str, Any]]:
    """Filter and rank relevant local TM examples."""

    threshold = CONFIDENCE_RANK.get(min_alignment_confidence.casefold())
    if threshold is None:
        raise ValueError("min_alignment_confidence must be high, medium, or low")
    if top_k <= 0:
        return []

    retrieved = []
    for raw_entry in tm_entries:
        entry = TranslationMemoryEntry.from_dict(raw_entry, raw_entry.get("_source_path"))
        if not entry.source_text or not entry.target_text:
            continue
        if CONFIDENCE_RANK[entry.alignment_confidence] < threshold:
            continue
        if entry.usage_policy.get("allow_retrieval") is False:
            continue
        score = compute_similarity(query_text, entry.source_text)
        if score < min_score:
            continue
        item = entry.to_dict()
        item.update(
            {
                "similarity_score": score,
                "use_mode": "reference_only",
                "human_review_required": True,
                "do_not_auto_copy": True,
            }
        )
        retrieved.append(item)

    retrieved.sort(
        key=lambda item: (
            item["similarity_score"],
            CONFIDENCE_RANK.get(item["alignment_confidence"], 0),
            -abs(item["source_word_count"] - _word_count(query_text)),
        ),
        reverse=True,
    )
    return retrieved[:top_k]


def build_reference_pack(
    query_text: str,
    retrieved: List[Dict[str, Any]],
    max_chars_per_side: int = 600,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build the future translation-runner integration contract."""

    references = []
    for item in retrieved:
        source_text = str(item.get("source_text") or "")
        target_text = str(item.get("target_text") or "")
        policy = item.get("usage_policy") if isinstance(item.get("usage_policy"), dict) else {}
        policy = {
            "scope": policy.get("scope", "local_private_reference"),
            "do_not_commit_full_text": bool(policy.get("do_not_commit_full_text", True)),
            **policy,
        }
        references.append(
            {
                "tm_id": str(item.get("tm_id") or _fallback_tm_id(item)),
                "pair_id": str(item.get("pair_id") or "unknown_pair"),
                "similarity_score": float(item.get("similarity_score") or 0.0),
                "alignment_confidence": str(item.get("alignment_confidence") or "low"),
                "source_text": source_text,
                "target_text": target_text,
                "source_preview": _preview(source_text, max_chars_per_side),
                "target_preview": _preview(target_text, max_chars_per_side),
                "use_mode": "reference_only",
                "human_review_required": True,
                "do_not_auto_copy": True,
                "usage_policy": policy,
            }
        )

    pack_warnings = list(DEFAULT_WARNINGS)
    for warning in warnings or []:
        if warning not in pack_warnings:
            pack_warnings.append(warning)
    if not references:
        pack_warnings.append("No eligible translation memory references were retrieved.")
    return {
        "query_text_hash": hashlib.sha256((query_text or "").encode("utf-8")).hexdigest(),
        "query_word_count": _word_count(query_text),
        "top_k": len(references),
        "references": references,
        "warnings": pack_warnings,
    }


def build_translation_reference_context(
    source_chunk: str,
    tm_dir: str = "outputs/parallel",
    top_k: int = 3,
    min_alignment_confidence: str = "high",
    max_chars_per_side: int = 500,
) -> Dict[str, Any]:
    """Load local TM and return a reference pack without modifying translation."""

    store = TranslationMemoryStore.from_directory(tm_dir)
    retrieved = retrieve_translation_memory(
        query_text=source_chunk,
        tm_entries=store.entries,
        top_k=top_k,
        min_alignment_confidence=min_alignment_confidence,
    )
    return build_reference_pack(
        query_text=source_chunk,
        retrieved=retrieved,
        max_chars_per_side=max_chars_per_side,
        warnings=store.warnings,
    )


def _load_tm_jsonl_with_warnings(path: Path) -> tuple[List[Dict[str, Any]], List[str]]:
    if not path.exists():
        return [], [f"Translation memory file does not exist: {path}"]
    entries: List[Dict[str, Any]] = []
    warnings: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                warnings.append(f"Skipped malformed JSONL row {line_number} in {path.name}.")
                continue
            if not isinstance(data, dict):
                warnings.append(f"Skipped non-object JSONL row {line_number} in {path.name}.")
                continue
            entry = TranslationMemoryEntry.from_dict(data, str(path)).to_dict()
            entry["_source_path"] = str(path)
            entries.append(entry)
    return entries, warnings


def _tokens(text: str) -> List[str]:
    return re.findall(r"\b[\w'-]+\b", text or "", flags=re.UNICODE)


def _char_ngrams(text: str, size: int) -> set[str]:
    compact = re.sub(r"\s+", " ", text)
    if len(compact) < size:
        return {compact} if compact else set()
    return {compact[index : index + size] for index in range(len(compact) - size + 1)}


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _preview(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= max_chars:
        return compact
    if max_chars <= 3:
        return compact[:max_chars]
    return compact[: max_chars - 3].rstrip() + "..."


def _word_count(text: str) -> int:
    return len(_tokens(normalize_retrieval_text(text)))


def _fallback_tm_id(data: Dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(data.get("pair_id") or ""),
            str(data.get("source_text") or ""),
            str(data.get("target_text") or ""),
        ]
    )
    return "tm_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
