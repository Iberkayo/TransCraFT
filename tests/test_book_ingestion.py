from pathlib import Path

import pytest

from src.tie.book_ingestion import (
    detect_input_format,
    extract_txt_book_text,
    select_book_range,
    slugify_book_run_name,
)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("book.pdf", "pdf"),
        ("book.epub", "epub"),
        ("book.txt", "txt"),
        ("book.md", "md"),
    ],
)
def test_detect_input_format(filename, expected):
    assert detect_input_format(filename) == expected


def test_rejects_unsupported_format():
    with pytest.raises(ValueError):
        detect_input_format("book.docx")


def test_text_first_pages_use_word_based_page_equivalents(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("One two three four. Five six seven eight. Nine ten.", encoding="utf-8")
    extracted = extract_txt_book_text(str(path))

    selected = select_book_range(extracted, first_pages=2, words_per_page=4)

    assert selected["range"]["mode"] == "first_page_equivalents"
    assert selected["range"]["requested_pages"] == 2
    assert selected["selected_word_count"] == 8


def test_first_words_and_pages_are_mutually_exclusive(tmp_path: Path):
    path = tmp_path / "sample.md"
    path.write_text("A complete sentence.", encoding="utf-8")
    with pytest.raises(ValueError):
        select_book_range(extract_txt_book_text(str(path)), first_pages=1, first_words=3)


def test_slug_is_generic_and_filesystem_safe():
    assert slugify_book_run_name("A Generic Book!.epub") == "a_generic_book"


def _pdf_extracted(units):
    return {
        "input_path": "synthetic.pdf",
        "input_format": "pdf",
        "title": "Synthetic",
        "author": None,
        "page_definition": "physical_pdf_pages",
        "units": units,
        "text": "\n\n".join(unit["text"] for unit in units),
    }


def test_first_pages_count_from_body_start_for_pdf():
    units = [
        {"text": "Copyright 2026 Example Publisher", "source_page": 1},
        {"text": "Other Works by the Author", "source_page": 2},
        {"text": "Earlier Title", "source_page": 3},
        {"text": "CHAPTER I", "source_page": 9},
    ]
    units.extend(
        {
            "text": f"This sustained body paragraph belongs to physical source page {page} and contains enough words for deterministic classification.",
            "source_page": page,
        }
        for page in range(9, 15)
    )
    selected = select_book_range(_pdf_extracted(units), first_pages=5, start_at="body")
    assert selected["range"]["mode"] == "first_physical_pages_after_body_start"
    assert selected["range"]["source_page_start"] == 9
    assert selected["range"]["source_page_end"] == 13
    assert max(unit["source_page"] for unit in selected["selected_units"]) == 13


def test_first_pages_beginning_counts_from_page_one():
    units = [
        {"text": "Copyright 2026 Example Publisher", "source_page": 1},
        {"text": "A sufficiently long front page paragraph used for deterministic page selection testing.", "source_page": 2},
        {"text": "CHAPTER I", "source_page": 9},
    ]
    selected = select_book_range(
        _pdf_extracted(units),
        first_pages=5,
        start_at="beginning",
        include_front_matter=True,
        exclude_toc=False,
    )
    assert selected["range"]["mode"] == "first_physical_pages_from_beginning"
    assert selected["range"]["source_page_start"] == 1
    assert selected["range"]["source_page_end"] == 5
