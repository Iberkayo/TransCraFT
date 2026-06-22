from pathlib import Path

import pytest

from src.tie.layout_export import (
    BookLayoutExportConfig,
    BookLayoutUnit,
    build_book_template_pages,
    export_book_template_pdf,
    export_preserve_source_pdf,
)


def _units():
    return [
        BookLayoutUnit("u1", "chapter_heading", "CHAPTER I", "BÖLÜM I"),
        BookLayoutUnit("u2", "body_paragraph", "Source paragraph.", "Türkçe deneme paragrafı."),
    ]


def test_book_template_layout_metadata(tmp_path: Path):
    result = export_book_template_pdf(
        str(tmp_path / "book.pdf"),
        _units(),
        {"title": "Synthetic", "target_language": "tr_TR"},
        {"recommendation": "accept"},
        BookLayoutExportConfig(page_size="A5"),
    )
    assert result["written"] is True
    assert result["layout"]["page_size"] == "A5"
    assert result["source_layout_preserved"] is False


def test_preserve_source_layout_falls_back_for_epub(tmp_path: Path):
    result = export_preserve_source_pdf(
        str(tmp_path / "book.pdf"),
        _units(),
        "synthetic.epub",
    )
    assert result["fallback_required"] is True
    assert result["written"] is False


def test_book_template_pages_break_before_chapter_heading():
    units = [
        BookLayoutUnit("u1", "body_paragraph", "A", "A" * 200),
        BookLayoutUnit("u2", "chapter_heading", "CHAPTER II", "BÖLÜM II"),
    ]
    pages = build_book_template_pages(units)
    assert len(pages) == 2


def test_preserve_source_writes_best_effort_pdf(tmp_path: Path):
    fitz = pytest.importorskip("fitz")
    source = tmp_path / "source.pdf"
    document = fitz.open()
    page = document.new_page(width=420, height=595)
    page.insert_text((50, 80), "Synthetic source block.")
    document.save(source)
    document.close()
    units = [
        BookLayoutUnit(
            "u1",
            "body_paragraph",
            "Synthetic source block.",
            "Sentetik hedef bloğu.",
            source_page=1,
            bbox=[50, 50, 370, 130],
        )
    ]
    result = export_preserve_source_pdf(str(tmp_path / "target.pdf"), units, str(source))
    assert result["written"] is True
    assert result["layout_preservation"] == "best_effort"
    assert Path(result["path"]).exists()
