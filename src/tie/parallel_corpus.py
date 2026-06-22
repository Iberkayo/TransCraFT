"""Generic parallel corpus discovery, alignment, and local TM extraction.

The module deliberately uses conservative structural heuristics. It does not
fine-tune a model and does not claim semantic equivalence between aligned
segments.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pypdf import PdfReader


NOISE_TOKENS = {
    "pdf",
    "z",
    "library",
    "lib",
    "archive",
    "isbn",
    "isbn10",
    "isbn13",
    "edition",
    "ed",
    "volume",
    "vol",
}

COMMON_CAPITALIZED_WORDS = {
    "A",
    "An",
    "And",
    "As",
    "At",
    "But",
    "By",
    "For",
    "From",
    "He",
    "Her",
    "His",
    "I",
    "If",
    "In",
    "It",
    "Its",
    "No",
    "Not",
    "Of",
    "On",
    "One",
    "Or",
    "She",
    "That",
    "The",
    "Their",
    "They",
    "This",
    "To",
    "We",
    "When",
    "With",
    "You",
}


def discover_parallel_candidates(
    input_root: str,
    source_lang: str = "EN",
    target_lang: str = "TR",
) -> List[Dict[str, Any]]:
    """Discover paired documents using a local manifest or generic metadata."""

    root = Path(input_root)
    manifest_path = root / "parallel_manifest.json"
    if manifest_path.exists():
        return _load_manifest_candidates(manifest_path, source_lang, target_lang)

    source_dir = root / source_lang
    target_dir = root / target_lang
    source_files = sorted(source_dir.glob("*.pdf")) if source_dir.exists() else []
    target_files = sorted(target_dir.glob("*.pdf")) if target_dir.exists() else []
    if not source_files or not target_files:
        return []

    source_metadata = [_document_match_metadata(path) for path in source_files]
    target_metadata = [_document_match_metadata(path) for path in target_files]
    scored: List[Tuple[float, int, int, str]] = []
    for source_index, source in enumerate(source_metadata):
        for target_index, target in enumerate(target_metadata):
            score, reason = _candidate_match_score(source, target)
            scored.append((score, source_index, target_index, reason))

    candidates: List[Dict[str, Any]] = []
    used_source = set()
    used_target = set()
    for score, source_index, target_index, reason in sorted(scored, reverse=True):
        if source_index in used_source or target_index in used_target:
            continue
        source = source_metadata[source_index]
        target = target_metadata[target_index]
        used_source.add(source_index)
        used_target.add(target_index)
        confidence = _match_confidence(score)
        pair_id = _pair_slug(source, target)
        candidates.append(
            {
                "pair_id": pair_id,
                "source_path": str(source["path"]),
                "target_path": str(target["path"]),
                "source_lang": source_lang,
                "target_lang": target_lang,
                "match_confidence": confidence,
                "match_reason": reason,
                "match_score": round(score, 4),
                "source_pages": source.get("page_count"),
                "target_pages": target.get("page_count"),
            }
        )
    return sorted(candidates, key=lambda item: item["pair_id"])


def extract_pdf_text_by_page(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """Extract text page by page without mutating or copying the source PDF."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    reader = PdfReader(str(path))
    page_limit = len(reader.pages) if max_pages is None else min(len(reader.pages), max_pages)
    pages = []
    text_parts = []
    for page_index in range(page_limit):
        raw_text = reader.pages[page_index].extract_text() or ""
        normalized = normalize_parallel_text(raw_text)
        pages.append(
            {
                "page_number": page_index + 1,
                "text": normalized,
                "word_count": _word_count(normalized),
                "char_count": len(normalized),
            }
        )
        text_parts.append(normalized)

    metadata = reader.metadata
    return {
        "path": str(path),
        "file_name": path.name,
        "sha256": _sha256(path),
        "page_count": len(reader.pages),
        "pages_extracted": page_limit,
        "title": metadata.title if metadata else None,
        "author": metadata.author if metadata else None,
        "pages": pages,
        "text": "\f".join(text_parts),
        "word_count": sum(page["word_count"] for page in pages),
    }


def normalize_parallel_text(text: str) -> str:
    """Normalize common extraction noise while retaining paragraph structure."""

    value = unicodedata.normalize("NFKC", text or "")
    value = value.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[^\S\n]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"([.!?])(?=[A-ZÇĞİÖŞÜ])", r"\1 ", value)
    return value.strip()


def segment_text_units(text: str, mode: str = "paragraph") -> List[Dict[str, Any]]:
    """Segment normalized text into page, paragraph, or sentence units."""

    if mode not in {"paragraph", "sentence", "page"}:
        raise ValueError("mode must be paragraph, sentence, or page")

    pages = (text or "").split("\f")
    units: List[Dict[str, Any]] = []
    for page_index, page_text in enumerate(pages, start=1):
        page_text = normalize_parallel_text(page_text)
        if not page_text:
            continue
        if mode == "page":
            segments = [page_text]
        elif mode == "sentence":
            segments = [
                segment.strip()
                for segment in re.split(r"(?<=[.!?])\s+", page_text)
                if segment.strip()
            ]
        else:
            segments = _paragraph_segments(page_text)

        for segment in segments:
            unit_index = len(units) + 1
            units.append(
                {
                    "unit_id": f"unit_{unit_index:06d}",
                    "text": segment,
                    "page_number": page_index,
                    "order": unit_index - 1,
                    "word_count": _word_count(segment),
                    "char_count": len(segment),
                    "sentence_count": _sentence_count(segment),
                    "is_heading": _is_heading(segment),
                }
            )
    return units


def align_parallel_units(
    source_units: List[Dict[str, Any]],
    target_units: List[Dict[str, Any]],
    pair_id: str = "parallel_pair",
    source_lang: str = "EN",
    target_lang: str = "TR",
) -> Dict[str, Any]:
    """Align units monotonically using position, length, heading, and page order."""

    aligned: List[Dict[str, Any]] = []
    quality = {"high": 0, "medium": 0, "low": 0}
    if not source_units or not target_units:
        return {
            "pair_id": pair_id,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source_units": len(source_units),
            "target_units": len(target_units),
            "aligned_units": [],
            "alignment_quality": quality,
            "unmatched_source_units": len(source_units),
            "unmatched_target_units": len(target_units),
        }

    last_target_index = -1
    target_count = len(target_units)
    source_count = len(source_units)
    for source_index, source in enumerate(source_units):
        expected = round(source_index * (target_count - 1) / max(1, source_count - 1))
        search_start = max(last_target_index + 1, expected - 3)
        search_end = min(target_count, expected + 4)
        candidate_indexes = list(range(search_start, search_end))
        if not candidate_indexes and last_target_index + 1 < target_count:
            candidate_indexes = [last_target_index + 1]
        if not candidate_indexes:
            break

        best_index = min(
            candidate_indexes,
            key=lambda index: _alignment_cost(
                source,
                target_units[index],
                source_index,
                index,
                source_count,
                target_count,
            ),
        )
        target = target_units[best_index]
        metrics = _alignment_metrics(
            source,
            target,
            source_index,
            best_index,
            source_count,
            target_count,
        )
        confidence = _alignment_confidence(metrics)
        quality[confidence] += 1
        alignment_index = len(aligned) + 1
        aligned.append(
            {
                "alignment_id": f"{pair_id}_{alignment_index:06d}",
                "source_unit_id": source.get("unit_id", f"src_{source_index + 1:06d}"),
                "target_unit_id": target.get("unit_id", f"trg_{best_index + 1:06d}"),
                "source_text": source.get("text", ""),
                "target_text": target.get("text", ""),
                "source_page": source.get("page_number"),
                "target_page": target.get("page_number"),
                "source_word_count": source.get("word_count", _word_count(source.get("text", ""))),
                "target_word_count": target.get("word_count", _word_count(target.get("text", ""))),
                "alignment_confidence": confidence,
                "alignment_method": "sequence_length_heading",
                "alignment_metrics": metrics,
            }
        )
        last_target_index = best_index

    return {
        "pair_id": pair_id,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "source_units": source_count,
        "target_units": target_count,
        "aligned_units": aligned,
        "alignment_quality": quality,
        "unmatched_source_units": max(0, source_count - len(aligned)),
        "unmatched_target_units": max(0, target_count - len(aligned)),
    }


def build_translation_memory(alignment_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build local private reference TM entries from non-empty alignments."""

    pair_id = alignment_result.get("pair_id", "parallel_pair")
    source_lang = alignment_result.get("source_lang", "EN")
    target_lang = alignment_result.get("target_lang", "TR")
    entries = []
    for alignment in alignment_result.get("aligned_units", []):
        if not alignment.get("source_text") or not alignment.get("target_text"):
            continue
        tm_index = len(entries) + 1
        profile = _detect_domain_profile(
            alignment["source_text"],
            alignment["target_text"],
        )
        entries.append(
            {
                "tm_id": f"tm_{tm_index:06d}",
                "pair_id": pair_id,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": alignment["source_text"],
                "target_text": alignment["target_text"],
                "source_word_count": alignment["source_word_count"],
                "target_word_count": alignment["target_word_count"],
                "alignment_confidence": alignment["alignment_confidence"],
                "domain_profile": profile,
                "usage_policy": {
                    "scope": "local_private_reference",
                    "do_not_commit_full_text": True,
                },
            }
        )
    return entries


def extract_glossary_candidates(alignment_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract conservative co-occurring capitalized term candidates."""

    pair_id = alignment_result.get("pair_id", "parallel_pair")
    source_occurrences: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for alignment in alignment_result.get("aligned_units", []):
        if alignment.get("alignment_confidence") == "low":
            continue
        for term in set(_capitalized_terms(alignment.get("source_text", ""))):
            source_occurrences[term].append(alignment)

    candidates = []
    for source_term, occurrences in sorted(source_occurrences.items()):
        if len(occurrences) < 2:
            continue
        target_counter: Counter[str] = Counter()
        for alignment in occurrences:
            target_counter.update(set(_capitalized_terms(alignment.get("target_text", ""))))
        if not target_counter:
            continue
        best_count = target_counter.most_common(1)[0][1]
        target_candidates = [
            term
            for term, count in target_counter.most_common(5)
            if count == best_count or count >= 2
        ][:3]
        if not target_candidates:
            continue
        ratio = best_count / len(occurrences)
        confidence = "high" if len(occurrences) >= 4 and ratio >= 0.75 else "medium" if ratio >= 0.5 else "low"
        candidates.append(
            {
                "source_term": source_term,
                "target_candidates": target_candidates,
                "evidence_count": len(occurrences),
                "confidence": confidence,
                "pair_ids": [pair_id],
                "review_required": True,
            }
        )
    return candidates


def build_parallel_style_profile(alignment_result: Dict[str, Any]) -> Dict[str, Any]:
    """Produce descriptive style observations without claiming learned style."""

    aligned = alignment_result.get("aligned_units", [])
    source_texts = [item.get("source_text", "") for item in aligned if item.get("source_text")]
    target_texts = [item.get("target_text", "") for item in aligned if item.get("target_text")]
    source_sentence_lengths = _sentence_lengths(source_texts)
    target_sentence_lengths = _sentence_lengths(target_texts)
    source_paragraph_words = [_word_count(text) for text in source_texts if text]
    target_paragraph_words = [_word_count(text) for text in target_texts if text]
    source_average = mean(source_sentence_lengths) if source_sentence_lengths else 0.0
    target_average = mean(target_sentence_lengths) if target_sentence_lengths else 0.0
    paragraph_ratio = (
        mean(target_paragraph_words) / mean(source_paragraph_words)
        if source_paragraph_words and target_paragraph_words and mean(source_paragraph_words)
        else 0.0
    )
    target_joined = "\n".join(target_texts)
    notes = []
    if source_average and target_average:
        if target_average < source_average * 0.8:
            notes.append("Target text tends to use shorter sentences than the source.")
        elif target_average > source_average * 1.2:
            notes.append("Target text tends to use longer sentences than the source.")
        else:
            notes.append("Source and target sentence lengths are broadly similar.")
    if paragraph_ratio:
        notes.append("Paragraph-length ratio is descriptive and requires human interpretation.")

    return {
        "pair_id": alignment_result.get("pair_id", "parallel_pair"),
        "observations": {
            "average_source_sentence_length": round(source_average, 2),
            "average_target_sentence_length": round(target_average, 2),
            "dialogue_density": round(_dialogue_density(source_texts + target_texts), 4),
            "paragraph_length_ratio": round(paragraph_ratio, 4),
            "target_punctuation_style": {
                "semicolon_frequency": target_joined.count(";"),
                "em_dash_frequency": target_joined.count("—"),
            },
        },
        "notes": notes,
        "human_review_required": True,
    }


def write_parallel_artifacts(
    result: Dict[str, Any],
    output_dir: str = "outputs/parallel",
) -> Dict[str, str]:
    """Write full-text artifacts locally; callers must keep the directory private."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pair = result["pair"]
    pair_id = pair["pair_id"]
    alignment = result["alignment"]
    translation_memory = result["translation_memory"]
    glossary = result["glossary_candidates"]
    style_profile = result["style_profile"]

    paths = {
        "alignment": output / f"{pair_id}_alignment.jsonl",
        "translation_memory": output / f"{pair_id}_translation_memory.jsonl",
        "glossary": output / f"{pair_id}_glossary_candidates.json",
        "style_profile": output / f"{pair_id}_style_profile.json",
        "report": output / f"{pair_id}_alignment_report.md",
    }
    _write_jsonl(paths["alignment"], alignment.get("aligned_units", []))
    _write_jsonl(paths["translation_memory"], translation_memory)
    paths["glossary"].write_text(json.dumps(glossary, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["style_profile"].write_text(json.dumps(style_profile, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["report"].write_text(_alignment_report(result), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _load_manifest_candidates(
    manifest_path: Path,
    source_lang: str,
    target_lang: str,
) -> List[Dict[str, Any]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = []
    for pair in data.get("pairs", []):
        if pair.get("source_lang", source_lang) != source_lang:
            continue
        if pair.get("target_lang", target_lang) != target_lang:
            continue
        candidates.append(
            {
                "pair_id": pair["pair_id"],
                "source_path": pair["source_path"],
                "target_path": pair["target_path"],
                "source_lang": source_lang,
                "target_lang": target_lang,
                "match_confidence": "high",
                "match_reason": "manifest",
                "match_score": 1.0,
            }
        )
    return candidates


def _document_match_metadata(path: Path) -> Dict[str, Any]:
    title = None
    author = None
    page_count = None
    try:
        reader = PdfReader(str(path))
        metadata = reader.metadata
        title = metadata.title if metadata else None
        author = metadata.author if metadata else None
        page_count = len(reader.pages)
    except Exception:
        pass
    return {
        "path": path,
        "stem": path.stem,
        "normalized_name": _normalize_match_string(path.stem),
        "tokens": set(_match_tokens(path.stem)),
        "title": title,
        "title_normalized": _normalize_match_string(title or ""),
        "author": author,
        "author_tokens": set(_match_tokens(author or "")),
        "page_count": page_count,
    }


def _candidate_match_score(source: Dict[str, Any], target: Dict[str, Any]) -> Tuple[float, str]:
    name_ratio = SequenceMatcher(None, source["normalized_name"], target["normalized_name"]).ratio()
    token_union = source["tokens"] | target["tokens"]
    token_overlap = len(source["tokens"] & target["tokens"]) / len(token_union) if token_union else 0.0
    title_ratio = 0.0
    if source["title_normalized"] and target["title_normalized"]:
        title_ratio = SequenceMatcher(None, source["title_normalized"], target["title_normalized"]).ratio()
    page_similarity = 0.0
    if source.get("page_count") and target.get("page_count"):
        page_similarity = min(source["page_count"], target["page_count"]) / max(source["page_count"], target["page_count"])
    author_overlap = False
    source_author_tokens = source.get("author_tokens", set())
    if source_author_tokens:
        author_overlap = source_author_tokens.issubset(target["tokens"]) or bool(source_author_tokens & target["tokens"])
    target_author_tokens = target.get("author_tokens", set())
    if target_author_tokens:
        author_overlap = author_overlap or target_author_tokens.issubset(source["tokens"]) or bool(target_author_tokens & source["tokens"])

    structural = max(name_ratio, token_overlap, title_ratio)
    score = structural * 0.65 + page_similarity * 0.15 + (0.20 if author_overlap else 0.0)
    reasons = ["filename_similarity"]
    if title_ratio >= 0.75:
        reasons.append("title_metadata")
    if author_overlap:
        reasons.append("author_metadata")
    if page_similarity >= 0.8:
        reasons.append("page_count")
    return min(1.0, score), "+".join(reasons)


def _match_confidence(score: float) -> str:
    if score >= 0.68:
        return "high"
    if score >= 0.42:
        return "medium"
    return "low"


def _pair_slug(source: Dict[str, Any], target: Dict[str, Any]) -> str:
    preferred = source.get("title") or target.get("title") or source.get("stem") or target.get("stem")
    slug = re.sub(r"[^a-z0-9]+", "_", _ascii_fold(preferred).casefold()).strip("_")
    if not slug:
        digest = hashlib.sha256(f"{source['path']}|{target['path']}".encode("utf-8")).hexdigest()[:10]
        slug = f"parallel_pair_{digest}"
    return slug[:80]


def _normalize_match_string(value: str) -> str:
    tokens = _match_tokens(value)
    return " ".join(tokens)


def _match_tokens(value: str) -> List[str]:
    folded = _ascii_fold(value).casefold()
    folded = re.sub(r"\b(?:19|20)\d{2}\b", " ", folded)
    folded = re.sub(r"\b[a-f0-9]{16,}\b", " ", folded)
    tokens = re.findall(r"[a-z0-9]+", folded)
    return [token for token in tokens if token not in NOISE_TOKENS and len(token) > 1]


def _ascii_fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(character)
    )


def _paragraph_segments(text: str) -> List[str]:
    paragraphs = [segment.strip() for segment in re.split(r"\n\s*\n", text) if segment.strip()]
    if len(paragraphs) <= 1:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        paragraphs = []
        current = []
        for line in lines:
            current.append(line)
            if line.endswith((".", "!", "?", ":", ";")) or _is_heading(line):
                paragraphs.append(" ".join(current))
                current = []
        if current:
            paragraphs.append(" ".join(current))
    return [paragraph for paragraph in paragraphs if _word_count(paragraph) >= 2]


def _is_heading(text: str) -> bool:
    words = re.findall(r"\b\w+\b", text or "", flags=re.UNICODE)
    if not words or len(words) > 14:
        return False
    if text.strip().endswith((".", "?", "!")):
        return False
    letters = [character for character in text if character.isalpha()]
    upper_ratio = sum(character.isupper() for character in letters) / len(letters) if letters else 0.0
    title_ratio = sum(word[:1].isupper() for word in words) / len(words)
    return upper_ratio >= 0.65 or title_ratio >= 0.8


def _alignment_cost(
    source: Dict[str, Any],
    target: Dict[str, Any],
    source_index: int,
    target_index: int,
    source_count: int,
    target_count: int,
) -> float:
    metrics = _alignment_metrics(source, target, source_index, target_index, source_count, target_count)
    return (
        (1.0 - metrics["length_similarity"]) * 0.55
        + metrics["position_delta"] * 0.35
        + (0.0 if metrics["heading_match"] else 0.10)
    )


def _alignment_metrics(
    source: Dict[str, Any],
    target: Dict[str, Any],
    source_index: int,
    target_index: int,
    source_count: int,
    target_count: int,
) -> Dict[str, Any]:
    source_words = max(1, source.get("word_count", _word_count(source.get("text", ""))))
    target_words = max(1, target.get("word_count", _word_count(target.get("text", ""))))
    length_similarity = min(source_words, target_words) / max(source_words, target_words)
    source_position = source_index / max(1, source_count - 1)
    target_position = target_index / max(1, target_count - 1)
    return {
        "length_similarity": round(length_similarity, 4),
        "length_ratio": round(target_words / source_words, 4),
        "position_delta": round(abs(source_position - target_position), 4),
        "heading_match": bool(source.get("is_heading")) == bool(target.get("is_heading")),
        "page_delta": abs((source.get("page_number") or 0) - (target.get("page_number") or 0)),
    }


def _alignment_confidence(metrics: Dict[str, Any]) -> str:
    if (
        metrics["length_similarity"] >= 0.72
        and metrics["position_delta"] <= 0.035
        and metrics["heading_match"]
    ):
        return "high"
    if metrics["length_similarity"] >= 0.42 and metrics["position_delta"] <= 0.10:
        return "medium"
    return "low"


def _detect_domain_profile(source_text: str, target_text: str) -> Dict[str, str]:
    combined = f"{source_text} {target_text}".casefold()
    technical_markers = {
        "algorithm",
        "analytics",
        "data",
        "database",
        "model",
        "network",
        "system",
        "technology",
        "veri",
        "sistem",
        "teknoloji",
    }
    dialogue_marks = combined.count('"') + combined.count("“") + combined.count("”")
    technical_hits = sum(1 for marker in technical_markers if re.search(rf"\b{re.escape(marker)}\b", combined))
    if technical_hits >= 2:
        text_type = "technical"
        register = "formal"
    elif dialogue_marks >= 4:
        text_type = "literary"
        register = "literary"
    elif _sentence_count(combined) >= 2:
        text_type = "nonfiction"
        register = "plain"
    else:
        text_type = "unknown"
        register = "unknown"
    return {"detected_text_type": text_type, "detected_register": register}


def _capitalized_terms(text: str) -> List[str]:
    terms = re.findall(
        r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+){0,2}\b",
        text or "",
    )
    return [
        term
        for term in terms
        if term not in COMMON_CAPITALIZED_WORDS and len(term) >= 3
    ]


def _sentence_lengths(texts: Iterable[str]) -> List[int]:
    lengths = []
    for text in texts:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            count = _word_count(sentence)
            if count:
                lengths.append(count)
    return lengths


def _dialogue_density(texts: Iterable[str]) -> float:
    joined = "\n".join(texts)
    words = max(1, _word_count(joined))
    dialogue_marks = joined.count('"') + joined.count("“") + joined.count("”") + joined.count("—")
    return dialogue_marks / words


def _alignment_report(result: Dict[str, Any]) -> str:
    pair = result["pair"]
    alignment = result["alignment"]
    return "\n".join(
        [
            f"# Parallel Alignment Report: {pair['pair_id']}",
            "",
            "This report contains metadata and counts only. Full aligned text remains in local JSONL artifacts.",
            "",
            f"- Source file: `{Path(pair['source_path']).name}`",
            f"- Target file: `{Path(pair['target_path']).name}`",
            f"- Match confidence: `{pair['match_confidence']}`",
            f"- Match reason: `{pair['match_reason']}`",
            f"- Source pages processed: `{result['source_extraction']['pages_extracted']}`",
            f"- Target pages processed: `{result['target_extraction']['pages_extracted']}`",
            f"- Source units: `{alignment['source_units']}`",
            f"- Target units: `{alignment['target_units']}`",
            f"- Aligned units: `{len(alignment['aligned_units'])}`",
            f"- Alignment quality: `{alignment['alignment_quality']}`",
            f"- Translation memory entries: `{len(result['translation_memory'])}`",
            f"- Glossary candidates: `{len(result['glossary_candidates'])}`",
            "",
            "Alignment is heuristic and requires human review before reuse.",
            "",
        ]
    )


def _write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text or "", flags=re.UNICODE))


def _sentence_count(text: str) -> int:
    return len([segment for segment in re.split(r"(?<=[.!?])\s+", text or "") if segment.strip()])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
