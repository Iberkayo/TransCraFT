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
