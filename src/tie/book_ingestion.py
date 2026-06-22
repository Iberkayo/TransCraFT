"""Generic ingestion and range selection for local book translation runs."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    for index in range(page_limit):
        text = reader.pages[index].extract_text() or ""
        pages.append({"page_number": index + 1, "text": text, "word_count": _word_count(text)})
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
                blocks.append(value)
        text = "\n\n".join(blocks).strip()
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
        sections.append({"section_id": item.get_name(), "text": text, "word_count": words})
        total_words += words
        if max_words is not None and total_words >= max_words:
            break
    return {
        "input_path": str(path),
        "input_format": "epub",
        "title": title_data[0][0] if title_data else path.stem,
        "author": author_data[0][0] if author_data else None,
        "page_definition": "word_based_page_equivalents",
        "sections": sections,
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
    return {
        "input_path": str(path),
        "input_format": detect_input_format(str(path)),
        "title": path.stem,
        "author": None,
        "page_definition": "word_based_page_equivalents",
        "text": text,
        "word_count": _word_count(text),
    }


def select_book_range(
    extracted: Dict[str, Any],
    first_pages: Optional[int] = None,
    first_words: Optional[int] = None,
    words_per_page: int = 300,
) -> Dict[str, Any]:
    if first_pages is not None and first_words is not None:
        raise ValueError("Choose either first_pages or first_words, not both.")
    if words_per_page <= 0:
        raise ValueError("words_per_page must be positive.")

    input_format = extracted["input_format"]
    if input_format == "pdf" and first_pages is not None:
        pages = extracted.get("pages", [])[:first_pages]
        text = "\f".join(page["text"] for page in pages)
        range_data = {
            "mode": "first_physical_pages",
            "requested_pages": first_pages,
            "selected_pages": len(pages),
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
            word_limit = _word_count(extracted.get("text", ""))
            mode = "full_extracted_text"
        text = _truncate_words_at_sentence(extracted.get("text", ""), word_limit)
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


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text or "", flags=re.UNICODE))
