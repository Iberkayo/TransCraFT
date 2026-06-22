from src.tie.book_ingestion import select_book_range
from src.tie.book_structure import (
    build_structured_book_units,
    detect_chapter_heading,
    detect_front_matter_units,
    detect_table_of_contents_units,
)


def _extracted(units):
    return {
        "input_path": "synthetic.txt",
        "input_format": "txt",
        "title": "Synthetic",
        "author": None,
        "page_definition": "word_based_page_equivalents",
        "units": units,
        "text": "\n\n".join(unit["text"] for unit in units),
    }


def test_detect_table_of_contents_dotted_leaders():
    units = [{"text": "Chapter I ........ 1\nChapter II ....... 9\nChapter III ...... 17"}]
    assert detect_table_of_contents_units(units) == units


def test_detect_front_matter_contents():
    units = [{"text": "Copyright 2026 Example Publisher"}, {"text": "A long body paragraph follows."}]
    assert detect_front_matter_units(units) == [units[0]]


def test_detect_chapter_heading_generic():
    assert detect_chapter_heading({"text": "CHAPTER IV"})
    assert detect_chapter_heading({"text": "Bölüm 12"})


def test_start_at_body_skips_toc():
    extracted = _extracted(
        [
            {"text": "Contents\nChapter I .... 1\nChapter II .... 8\nChapter III .... 16"},
            {"text": "CHAPTER I"},
            {"text": "This is a sufficiently long opening body paragraph with more than eighteen words so it is confidently treated as body text."},
        ]
    )
    selected = select_book_range(extracted, first_words=100)
    assert "Contents" not in selected["selected_text"]
    assert selected["front_matter"]["toc_units_skipped"] == 1


def test_repeated_chapter_list_in_toc_section_is_skipped():
    extracted = _extracted(
        [
            {"text": "Contents", "section_id": "toc.xhtml"},
            {"text": "CHAPTER I", "section_id": "toc.xhtml"},
            {"text": "CHAPTER II", "section_id": "toc.xhtml"},
            {"text": "CHAPTER III", "section_id": "toc.xhtml"},
            {"text": "A sufficiently long opening paragraph begins the actual synthetic body after the chapter list and contains enough words for classification."},
        ]
    )
    selected = select_book_range(extracted, first_words=100)
    assert selected["front_matter"]["toc_units_skipped"] == 4
    assert all(unit["unit_type"] != "table_of_contents" for unit in selected["selected_units"])


def test_start_at_beginning_keeps_front_matter():
    extracted = _extracted(
        [
            {"text": "Copyright 2026 Example Publisher"},
            {"text": "CHAPTER I"},
            {"text": "This is a sufficiently long body paragraph that follows the front matter and begins the synthetic story for testing."},
        ]
    )
    selected = select_book_range(
        extracted,
        first_words=100,
        start_at="beginning",
        include_front_matter=True,
        exclude_toc=False,
    )
    assert "Copyright" in selected["selected_text"]


def test_no_book_specific_layout_rules():
    source = __import__("inspect").getsource(__import__("src.tie.book_structure", fromlist=["x"]))
    forbidden = ["Dracula", "Blood Meridian", "Judge Holden", "Cormac McCarthy"]
    assert not any(value.casefold() in source.casefold() for value in forbidden)
