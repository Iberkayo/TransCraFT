from src.tie.book_ingestion import select_book_range
from src.tie.book_structure import (
    build_structured_book_units,
    detect_chapter_heading,
    detect_front_matter_units,
    detect_table_of_contents_units,
    find_body_start,
    find_body_start_index,
    remove_ornament_tokens,
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


def test_no_book_specific_body_start_rules():
    source = __import__("inspect").getsource(__import__("src.tie.book_structure", fromlist=["x"]))
    forbidden = ["Bram Stoker", "Jonathan Harker", "Bistritz", "Mina Harker"]
    assert not any(value.casefold() in source.casefold() for value in forbidden)


def test_remove_ornament_tokens():
    cleaned, count = remove_ornament_tokens("/ornament20/ornament20 Normal / path")
    assert cleaned == "Normal / path"
    assert count == 2


def test_ornament_units_are_not_body_paragraphs():
    units = build_structured_book_units(_extracted([{"text": "/ornament5 /ornament20"}]))
    assert units[0]["unit_type"] == "front_matter"
    assert units[0]["decoration_only"] is True


def test_detect_other_works_front_matter():
    units = [{"text": "Other Works by the Author"}]
    assert detect_front_matter_units(units) == units


def test_detect_dedication_front_matter():
    units = [{"text": "To My Dear Friend"}]
    assert detect_front_matter_units(units) == units


def test_detect_preface_front_matter():
    units = [{"text": "PREFACE"}]
    assert detect_front_matter_units(units) == units


def test_find_body_start_prefers_chapter_heading():
    units = build_structured_book_units(
        _extracted(
            [
                {"text": "Copyright 2026 Example Publisher"},
                {"text": "CHAPTER I"},
                {"text": "This opening narrative paragraph contains enough words to be recognized as sustained body prose after the chapter heading."},
            ]
        )
    )
    result = find_body_start(units)
    assert result["index"] == 1
    assert result["confidence"] == "high"


def test_find_body_start_skips_other_works_and_dedication():
    units = build_structured_book_units(
        _extracted(
            [
                {"text": "Other Works by the Author"},
                {"text": "A Short Earlier Title"},
                {"text": "To My Dear Friend"},
                {"text": "CHAPTER I"},
                {"text": "This opening narrative paragraph contains enough words to be recognized as the actual body of the synthetic book."},
            ]
        )
    )
    assert find_body_start_index(units) == 3


def test_find_body_start_fallback_to_sustained_body_paragraph():
    units = build_structured_book_units(
        _extracted(
            [
                {"text": "Copyright 2026 Example Publisher"},
                {"text": "This is the first sustained narrative paragraph and it contains enough words to classify as body prose without a chapter heading."},
                {"text": "This is the second sustained narrative paragraph and it confirms that the main body has started in this synthetic fixture."},
            ]
        )
    )
    assert find_body_start_index(units) == 1
