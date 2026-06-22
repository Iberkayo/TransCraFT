"""Generic heuristic structure detection for extracted books."""

from __future__ import annotations

import re
from typing import Any, Dict, List


FRONT_MATTER_TERMS = {
    "contents",
    "table of contents",
    "dedication",
    "acknowledgements",
    "acknowledgments",
    "about the author",
    "copyright",
    "publisher",
    "isbn",
    "title page",
}

CHAPTER_PATTERN = re.compile(
    r"^\s*(chapter|part|book|section|bölüm|kısım)\s+"
    r"([ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
    re.IGNORECASE,
)


def detect_front_matter_units(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    detected = []
    for unit in units:
        text = _normalized(unit.get("text", ""))
        if any(term in text for term in FRONT_MATTER_TERMS):
            detected.append(unit)
    return detected


def detect_table_of_contents_units(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [unit for unit in units if _looks_like_toc(unit.get("text", ""))]


def detect_chapter_heading(unit: Dict[str, Any]) -> bool:
    text = " ".join((unit.get("text") or "").split()).strip()
    if not text or len(text) > 120 or len(text.split()) > 14:
        return False
    if CHAPTER_PATTERN.match(text):
        return True
    if re.fullmatch(r"[ivxlcdm]+", text, re.IGNORECASE):
        return True
    return bool(
        len(text.split()) <= 8
        and text.upper() == text
        and any(char.isalpha() for char in text)
        and not _looks_like_toc(text)
    )


def classify_book_unit(unit: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(unit)
    text = (unit.get("text") or "").strip()
    normalized = _normalized(text)
    if not text:
        unit_type = "blank"
    elif _looks_like_toc(text):
        unit_type = "table_of_contents"
    elif detect_chapter_heading(unit):
        unit_type = "chapter_heading"
    elif any(term in normalized for term in FRONT_MATTER_TERMS):
        unit_type = "title_page" if normalized in {"title page"} else "front_matter"
    elif unit.get("position") == "header":
        unit_type = "page_header"
    elif unit.get("position") == "footer":
        unit_type = "page_footer"
    elif len(text.split()) >= 18 or len(text) >= 120:
        unit_type = "body_paragraph"
    else:
        unit_type = "unknown"
    result["unit_type"] = unit_type
    result["confidence"] = _confidence(unit_type)
    return result


def build_structured_book_units(extracted: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_units = extracted.get("units") or _fallback_units(extracted)
    classified = []
    title = _normalized(str(extracted.get("title") or ""))
    for index, unit in enumerate(raw_units, start=1):
        value = classify_book_unit(
            {
                "unit_id": unit.get("unit_id") or f"unit_{index:04d}",
                "text": unit.get("text", ""),
                "source_page": unit.get("source_page"),
                "bbox": unit.get("bbox"),
                "source_tag": unit.get("source_tag"),
                "section_id": unit.get("section_id"),
                "position": unit.get("position"),
            }
        )
        if title and _normalized(value["text"]) == title:
            value["unit_type"] = "title_page"
            value["confidence"] = "high"
        classified.append(value)

    first_body = next(
        (index for index, unit in enumerate(classified) if unit["unit_type"] == "body_paragraph"),
        len(classified),
    )
    chapter_list = [
        unit for unit in classified[:first_body] if unit["unit_type"] == "chapter_heading"
    ]
    if len(chapter_list) >= 3:
        for unit in chapter_list:
            unit["unit_type"] = "table_of_contents"
            unit["confidence"] = "medium"
    toc_sections = {
        unit.get("section_id")
        for unit in classified
        if unit["unit_type"] == "table_of_contents" and unit.get("section_id")
    }
    for unit in classified:
        if unit.get("section_id") in toc_sections and unit["unit_type"] == "chapter_heading":
            unit["unit_type"] = "table_of_contents"
            unit["confidence"] = "medium"

    return classified


def _fallback_units(extracted: Dict[str, Any]) -> List[Dict[str, Any]]:
    units = []
    for index, paragraph in enumerate(
        part.strip() for part in re.split(r"\n\s*\n|\f", extracted.get("text", "")) if part.strip()
    ):
        units.append({"unit_id": f"unit_{index + 1:04d}", "text": paragraph})
    return units


def _looks_like_toc(text: str) -> bool:
    normalized = _normalized(text)
    if normalized in {"contents", "table of contents", "chapter list"}:
        return True
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    dotted = sum(bool(re.search(r"\.{3,}\s*\d+\s*$", line)) for line in lines)
    numbered = sum(bool(re.search(r"\S.+\s+\d+\s*$", line)) and len(line.split()) <= 14 for line in lines)
    chapters = sum(bool(CHAPTER_PATTERN.match(line)) for line in lines)
    roman_titles = sum(bool(re.match(r"^[ivxlcdm]+\s+\S.+\s+\d+\s*$", line, re.I)) for line in lines)
    return dotted >= 2 or numbered >= 3 or roman_titles >= 2 or (chapters >= 3 and numbered >= 2)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def _confidence(unit_type: str) -> str:
    if unit_type in {"table_of_contents", "chapter_heading", "body_paragraph", "blank"}:
        return "high"
    if unit_type in {"front_matter", "title_page", "page_header", "page_footer"}:
        return "medium"
    return "low"
