"""Generic ingestion and range selection for local book translation runs."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.tie.book_structure import build_structured_book_units
from src.tie.source_cleanup import SourceExtractionCleaner


SUPPORTED_FORMATS = {".pdf": "pdf", ".epub": "epub", ".txt": "txt", ".md": "md"}


def detect_input_format(input_path: str) -> str:
    path = Path(input_path)
    suffix = path.suffix.casefold()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported input format: {suffix or '<none>'}")
    return SUPPORTED_FORMATS[suffix]


def extract_book_text(input_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    input_format = detect_input_format(input_path)
    if input_format == "pdf":
        return extract_pdf_book_text(input_path, max_pages=max_pages)
    if input_format == "epub":
        return extract_epub_book_text(input_path)
    return extract_txt_book_text(input_path)


def extract_pdf_book_text(input_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    from pypdf import PdfReader

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(path)
    reader = PdfReader(str(path))
    page_limit = len(reader.pages) if max_pages is None else min(max_pages, len(reader.pages))
    pages = []
    units = _extract_pdf_geometry_units(path, page_limit)
    for index in range(page_limit):
        text = reader.pages[index].extract_text() or ""
        pages.append({"page_number": index + 1, "text": text, "word_count": _word_count(text)})
        if not any(unit.get("source_page") == index + 1 for unit in units):
            for paragraph_index, paragraph in enumerate(re.split(r"\n\s*\n", text), start=1):
                if paragraph.strip():
                    units.append(
                        {
                            "unit_id": f"page_{index + 1:04d}_{paragraph_index:03d}",
                            "text": paragraph.strip(),
                            "source_page": index + 1,
                        }
                    )
    metadata = reader.metadata
    return {
        "input_path": str(path),
        "input_format": "pdf",
        "title": metadata.title if metadata and metadata.title else path.stem,
        "author": metadata.author if metadata else None,
        "page_definition": "physical_pdf_pages",
        "total_pages": len(reader.pages),
        "pages_extracted": page_limit,
        "pages": pages,
        "units": units,
        "text": "\f".join(page["text"] for page in pages),
        "word_count": sum(page["word_count"] for page in pages),
    }


def extract_epub_book_text(input_path: str, max_words: Optional[int] = None) -> Dict[str, Any]:
    from bs4 import BeautifulSoup
    from ebooklib import epub

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(path)
    book = epub.read_epub(str(path))
    title_data = book.get_metadata("DC", "title")
    author_data = book.get_metadata("DC", "creator")
    sections: List[Dict[str, Any]] = []
    total_words = 0
    for item_id, _linear in book.spine:
        item = book.get_item_with_id(item_id)
        if item is None:
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for node in soup(["script", "style", "nav"]):
            node.decompose()
        blocks = []
        for element in soup.find_all(["h1", "h2", "h3", "p", "blockquote"]):
            value = " ".join(element.get_text(" ", strip=True).split())
            if value:
                blocks.append({"text": value, "source_tag": element.name})
        text = "\n\n".join(block["text"] for block in blocks).strip()
        if not text:
            continue
        if max_words is not None:
            remaining = max_words - total_words
            if remaining <= 0:
                break
            text = _truncate_words_at_sentence(text, remaining)
        words = _word_count(text)
        if not words:
            continue
        sections.append(
            {
                "section_id": item.get_name(),
                "text": text,
                "word_count": words,
                "blocks": blocks,
            }
        )
        total_words += words
        if max_words is not None and total_words >= max_words:
            break
    units = []
    for section in sections:
        for block_index, block in enumerate(section["blocks"], start=1):
            units.append(
                {
                    "unit_id": f"section_{len(units) + 1:04d}",
                    "text": block["text"],
                    "source_tag": block["source_tag"],
                    "section_id": section["section_id"],
                }
            )
    return {
        "input_path": str(path),
        "input_format": "epub",
        "title": title_data[0][0] if title_data else path.stem,
        "author": author_data[0][0] if author_data else None,
        "page_definition": "word_based_page_equivalents",
        "sections": sections,
        "units": units,
        "text": "\n\n".join(section["text"] for section in sections),
        "word_count": total_words,
    }


def extract_txt_book_text(input_path: str, max_words: Optional[int] = None) -> Dict[str, Any]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if max_words is not None:
        text = _truncate_words_at_sentence(text, max_words)
    units = [
        {"unit_id": f"unit_{index:04d}", "text": paragraph.strip()}
        for index, paragraph in enumerate(re.split(r"\n\s*\n", text), start=1)
        if paragraph.strip()
    ]
    return {
        "input_path": str(path),
        "input_format": detect_input_format(str(path)),
        "title": path.stem,
        "author": None,
        "page_definition": "word_based_page_equivalents",
        "units": units,
        "text": text,
        "word_count": _word_count(text),
    }


def select_book_range(
    extracted: Dict[str, Any],
    first_pages: Optional[int] = None,
    first_words: Optional[int] = None,
    words_per_page: int = 300,
    start_at: str = "body",
    include_front_matter: bool = False,
    exclude_toc: bool = True,
) -> Dict[str, Any]:
    if first_pages is not None and first_words is not None:
        raise ValueError("Choose either first_pages or first_words, not both.")
    if words_per_page <= 0:
        raise ValueError("words_per_page must be positive.")

    if start_at not in {"body", "beginning"}:
        raise ValueError("start_at must be 'body' or 'beginning'.")

    structured = build_structured_book_units(extracted)
    selected_candidates, structure_summary = _filter_structured_units(
        structured,
        start_at=start_at,
        include_front_matter=include_front_matter,
        exclude_toc=exclude_toc,
    )
    input_format = extracted["input_format"]
    if input_format == "pdf" and first_pages is not None:
        available_pages = [unit.get("source_page") for unit in selected_candidates if unit.get("source_page")]
        first_source_page = min(available_pages) if available_pages else 1
        last_source_page = first_source_page + first_pages - 1
        selected_units = [
            unit
            for unit in selected_candidates
            if unit.get("source_page") is None or unit.get("source_page") <= last_source_page
        ]
        text = "\n\n".join(unit["text"] for unit in selected_units)
        range_data = {
            "mode": "first_physical_pages",
            "requested_pages": first_pages,
            "selected_pages": len(set(unit.get("source_page") for unit in selected_units if unit.get("source_page"))),
            "first_source_page": first_source_page,
            "words_per_page": None,
            "selected_word_count": _word_count(text),
        }
    else:
        if first_words is not None:
            word_limit = first_words
            mode = "first_words"
        elif first_pages is not None:
            word_limit = first_pages * words_per_page
            mode = "first_page_equivalents"
        else:
            word_limit = sum(_word_count(unit["text"]) for unit in selected_candidates)
            mode = "full_extracted_text"
        selected_units = _take_units_by_word_limit(selected_candidates, word_limit)
        text = "\n\n".join(unit["text"] for unit in selected_units)
        range_data = {
            "mode": mode,
            "requested_pages": first_pages,
            "requested_words": first_words,
            "words_per_page": words_per_page,
            "selected_word_count": _word_count(text),
            "estimated_page_equivalents": round(_word_count(text) / words_per_page, 2),
        }

    return {
        **extracted,
        "selected_text": text.strip(),
        "selected_units": selected_units,
        "structured_units": structured,
        "front_matter": structure_summary,
        "selected_word_count": _word_count(text),
        "range": range_data,
    }


def slugify_book_run_name(input_path: str) -> str:
    stem = Path(input_path).stem
    folded = "".join(
        char
        for char in unicodedata.normalize("NFKD", stem)
        if not unicodedata.combining(char)
    ).casefold()
    slug = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return slug[:80] or "book_run"


def clean_selected_book_text(selected: Dict[str, Any]) -> Dict[str, Any]:
    cleaner = SourceExtractionCleaner()
    cleanup = cleaner.clean(
        selected.get("selected_text", ""),
        document_type=selected.get("input_format", "unknown"),
        genre="literary_fiction",
    )
    return {**selected, "source_cleanup": cleanup, "cleaned_text": cleanup["cleaned_text"]}


def _filter_structured_units(
    units: List[Dict[str, Any]],
    start_at: str,
    include_front_matter: bool,
    exclude_toc: bool,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    first_body = 0
    if start_at == "body":
        for index, unit in enumerate(units):
            if unit["unit_type"] in {"chapter_heading", "body_paragraph"}:
                first_body = index
                break
    candidates = units[first_body:] if start_at == "body" else list(units)
    selected = []
    skipped_front = 0
    skipped_toc = 0
    for unit in candidates:
        if exclude_toc and unit["unit_type"] == "table_of_contents":
            skipped_toc += 1
            continue
        if not include_front_matter and unit["unit_type"] in {"front_matter", "title_page"}:
            skipped_front += 1
            continue
        if unit["unit_type"] in {"blank", "page_header", "page_footer"}:
            continue
        selected.append(unit)
    skipped_before_body = first_body if start_at == "body" else 0
    skipped_front += sum(
        unit["unit_type"] in {"front_matter", "title_page"} for unit in units[:skipped_before_body]
    )
    skipped_toc += sum(unit["unit_type"] == "table_of_contents" for unit in units[:skipped_before_body])
    return selected, {
        "toc_units_detected": sum(unit["unit_type"] == "table_of_contents" for unit in units),
        "front_matter_units_detected": sum(
            unit["unit_type"] in {"front_matter", "title_page"} for unit in units
        ),
        "front_matter_units_skipped": skipped_front,
        "toc_units_skipped": skipped_toc,
        "start_at": start_at,
        "include_front_matter": include_front_matter,
        "exclude_toc": exclude_toc,
    }


def _take_units_by_word_limit(
    units: List[Dict[str, Any]],
    word_limit: int,
) -> List[Dict[str, Any]]:
    selected = []
    count = 0
    for unit in units:
        remaining = word_limit - count
        if remaining <= 0:
            break
        unit_words = _word_count(unit["text"])
        if unit_words <= remaining:
            selected.append(unit)
            count += unit_words
            continue
        truncated = _truncate_words_at_sentence(unit["text"], remaining)
        if truncated:
            selected.append({**unit, "text": truncated, "truncated": True})
        break
    return selected


def _truncate_words_at_sentence(text: str, word_limit: int) -> str:
    if word_limit <= 0:
        return ""
    if _word_count(text) <= word_limit:
        return text.strip()
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chosen = []
    count = 0
    for sentence in sentences:
        sentence_words = _word_count(sentence)
        if chosen and count + sentence_words > word_limit:
            break
        chosen.append(sentence)
        count += sentence_words
        if count >= word_limit:
            break
    return " ".join(chosen).strip()


def _extract_pdf_geometry_units(path: Path, page_limit: int) -> List[Dict[str, Any]]:
    try:
        import fitz
    except ImportError:
        return []
    document = fitz.open(str(path))
    units = []
    try:
        for page_index in range(min(page_limit, len(document))):
            page = document[page_index]
            for block_index, block in enumerate(page.get_text("blocks"), start=1):
                x0, y0, x1, y1, text = block[:5]
                value = " ".join(str(text).split())
                if not value:
                    continue
                position = None
                if y1 <= page.rect.height * 0.1:
                    position = "header"
                elif y0 >= page.rect.height * 0.9:
                    position = "footer"
                units.append(
                    {
                        "unit_id": f"page_{page_index + 1:04d}_block_{block_index:03d}",
                        "text": value,
                        "source_page": page_index + 1,
                        "bbox": [float(x0), float(y0), float(x1), float(y1)],
                        "page_size": [float(page.rect.width), float(page.rect.height)],
                        "position": position,
                    }
                )
    finally:
        document.close()
    return units


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text or "", flags=re.UNICODE))
