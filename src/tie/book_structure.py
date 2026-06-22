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
    "other works by",
    "also by",
    "by the same author",
    "works by the author",
    "to my dear friend",
    "preface",
    "introduction",
}

ORNAMENT_PATTERN = re.compile(r"/ornament\d+", re.IGNORECASE)
CONTROL_DECORATION_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

CHAPTER_PATTERN = re.compile(
    r"^\s*(chapter|part|book|section|bölüm|kısım)\s+"
    r"([ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
    re.IGNORECASE,
)

JOURNAL_HEADING_PATTERN = re.compile(
    r"\b(journal|diary|letter|correspondence|memorandum|log|entry)\b",
    re.IGNORECASE,
)

DATE_HEADING_PATTERN = re.compile(
    r"^\s*(\d{1,2}\s+[A-Za-z]{3,12}(?:\s+\d{2,4})?|"
    r"[A-Za-z]{3,12}\s+\d{1,2}(?:,\s*\d{2,4})?)\.?\s*$"
)


def remove_ornament_tokens(text: str) -> tuple[str, int]:
    matches = ORNAMENT_PATTERN.findall(text or "")
    controls = CONTROL_DECORATION_PATTERN.findall(text or "")
    cleaned = ORNAMENT_PATTERN.sub(" ", text or "")
    cleaned = CONTROL_DECORATION_PATTERN.sub(" ", cleaned)
    if re.fullmatch(r"\s*(?:[^\w\s/]\s*){2,}\s*", cleaned):
        cleaned = ""
        controls.append("isolated-decoration")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip(), len(matches) + len(controls)


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
    heading_text = _collapse_letter_spaced_heading(text)
    if CHAPTER_PATTERN.match(heading_text):
        return True
    if re.fullmatch(r"[ivxlcdm]+", text, re.IGNORECASE):
        return True
    return False


def classify_book_unit(unit: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(unit)
    original_text = unit.get("text") or ""
    text, ornament_count = remove_ornament_tokens(original_text)
    result["text"] = text
    result["ornament_tokens_removed"] = ornament_count
    normalized = _normalized(text)
    if ornament_count and not text:
        unit_type = "front_matter"
        result["decoration_only"] = True
    elif not text:
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


def find_body_start_index(units: List[Dict[str, Any]]) -> int:
    return find_body_start(units)["index"]


def find_body_start(units: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not units:
        return {"index": 0, "confidence": "low", "score": 0}

    candidates = []
    for index, unit in enumerate(units):
        score = _body_start_score(units, index)
        candidates.append((score, index))

    strong = [candidate for candidate in candidates if candidate[0] >= 8]
    score, index = strong[0] if strong else max(candidates, key=lambda item: (item[0], -item[1]))
    if score >= 8:
        confidence = "high"
    elif score >= 5:
        confidence = "medium"
    else:
        confidence = "low"
        fallback = _first_sustained_body_index(units)
        if fallback is not None:
            index = fallback
    return {"index": index, "confidence": confidence, "score": score}


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

    _propagate_front_matter_lists(classified)
    return classified


def _fallback_units(extracted: Dict[str, Any]) -> List[Dict[str, Any]]:
    units = []
    for index, paragraph in enumerate(
        part.strip() for part in re.split(r"\n\s*\n|\f", extracted.get("text", "")) if part.strip()
    ):
        units.append({"unit_id": f"unit_{index + 1:04d}", "text": paragraph})
    return units


def _looks_like_toc(text: str) -> bool:
    normalized = _normalized(_collapse_letter_spaced_heading(text))
    if normalized in {"contents", "table of contents", "chapter list"}:
        return True
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    dotted = sum(
        bool(re.search(r"(?:\.\s*){3,}\d+\s*$", line))
        for line in lines
    )
    numbered = sum(bool(re.search(r"\S.+\s+\d+\s*$", line)) and len(line.split()) <= 14 for line in lines)
    chapters = sum(bool(CHAPTER_PATTERN.match(line)) for line in lines)
    roman_titles = sum(bool(re.match(r"^[ivxlcdm]+\s+\S.+\s+\d+\s*$", line, re.I)) for line in lines)
    return dotted >= 1 or numbered >= 3 or roman_titles >= 2 or (chapters >= 3 and numbered >= 2)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def _confidence(unit_type: str) -> str:
    if unit_type in {"table_of_contents", "chapter_heading", "body_paragraph", "blank"}:
        return "high"
    if unit_type in {"front_matter", "title_page", "page_header", "page_footer"}:
        return "medium"
    return "low"


def _body_start_score(units: List[Dict[str, Any]], index: int) -> int:
    unit = units[index]
    unit_type = unit.get("unit_type")
    text = unit.get("text", "")
    score = 0
    if unit_type == "chapter_heading":
        score += 9
    if JOURNAL_HEADING_PATTERN.search(text) and len(text.split()) <= 14:
        score += 4
    if DATE_HEADING_PATTERN.match(text):
        score += 3
    if unit_type == "body_paragraph":
        score += 3
    if _consecutive_body_count(units, index) >= 2:
        score += 4
    if index > 0 and units[index - 1].get("unit_type") == "chapter_heading":
        score += 3

    if unit_type in {"title_page", "table_of_contents", "front_matter", "page_header", "page_footer", "blank"}:
        score -= 12
    if unit.get("decoration_only"):
        score -= 12
    if _is_page_number_only(text):
        score -= 8
    if _looks_like_short_title_list(units, index):
        score -= 5
    return score


def _first_sustained_body_index(units: List[Dict[str, Any]]) -> int | None:
    for index, unit in enumerate(units):
        if unit.get("unit_type") == "body_paragraph" and _consecutive_body_count(units, index) >= 2:
            return index
    for index, unit in enumerate(units):
        if unit.get("unit_type") == "body_paragraph":
            return index
    return None


def _consecutive_body_count(units: List[Dict[str, Any]], index: int) -> int:
    count = 0
    for unit in units[index : index + 4]:
        if unit.get("unit_type") in {"body_paragraph", "unknown"} and len(unit.get("text", "").split()) >= 8:
            count += 1
        else:
            break
    return count


def _looks_like_short_title_list(units: List[Dict[str, Any]], index: int) -> bool:
    window = units[index : index + 4]
    short = sum(
        1
        for unit in window
        if 0 < len(unit.get("text", "").split()) <= 8
        and unit.get("unit_type") in {"unknown", "front_matter"}
    )
    return len(window) >= 3 and short >= 3


def _is_page_number_only(text: str) -> bool:
    return bool(re.fullmatch(r"\s*(?:\d+|[ivxlcdm]+)\s*", text or "", re.IGNORECASE))


def _propagate_front_matter_lists(units: List[Dict[str, Any]]) -> None:
    in_front_list = False
    for unit in units:
        normalized = _normalized(unit.get("text", ""))
        if any(
            marker in normalized
            for marker in {"other works by", "also by", "by the same author", "works by the author"}
        ):
            in_front_list = True
            unit["unit_type"] = "front_matter"
            unit["confidence"] = "high"
            continue
        if unit["unit_type"] == "chapter_heading":
            in_front_list = False
        elif in_front_list:
            if unit["unit_type"] == "body_paragraph" and len(unit.get("text", "").split()) >= 18:
                in_front_list = False
            elif len(unit.get("text", "").split()) <= 12:
                unit["unit_type"] = "front_matter"
                unit["confidence"] = "medium"


def _collapse_letter_spaced_heading(text: str) -> str:
    value = " ".join((text or "").split()).strip()
    tokens = value.split()
    if len(tokens) < 4:
        return value
    if sum(len(token) == 1 and token.isalpha() for token in tokens) < 4:
        return value
    compact = "".join(token for token in tokens if token.isalpha())
    match = re.match(r"^(chapter|part|book|section|contents)(.+)?$", compact, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2) or ''}".strip()
    return compact
