"""Layout-aware PDF export for generic book runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.tie.export_pdf import BOLD_FONT_CANDIDATES, find_unicode_font


@dataclass
class BookLayoutExportConfig:
    mode: str = "book_template"
    page_size: str = "A5"
    title_page: bool = True
    body_font_size: float = 10.5
    min_preserve_font_size: float = 7.0


@dataclass
class BookLayoutUnit:
    unit_id: str
    unit_type: str
    source_text: str
    target_text: str
    source_page: Optional[int] = None
    bbox: Optional[List[float]] = None


def build_book_template_pages(units: List[BookLayoutUnit]) -> List[List[BookLayoutUnit]]:
    pages: List[List[BookLayoutUnit]] = []
    current: List[BookLayoutUnit] = []
    char_budget = 1800
    used = 0
    for unit in units:
        if unit.unit_type == "chapter_heading" and current:
            pages.append(current)
            current = []
            used = 0
        size = len(unit.target_text)
        if current and used + size > char_budget:
            pages.append(current)
            current = []
            used = 0
        current.append(unit)
        used += size
    if current:
        pages.append(current)
    return pages


def export_book_template_pdf(
    output_path: str,
    units: List[BookLayoutUnit],
    run_metadata: Dict[str, Any],
    qa_summary: Dict[str, Any],
    config: Optional[BookLayoutExportConfig] = None,
) -> Dict[str, Any]:
    config = config or BookLayoutExportConfig()
    font_path = find_unicode_font()
    if font_path is None:
        return {"written": False, "path": None, "warning": "No local Unicode font was found."}

    from fpdf import FPDF

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    bold_path = next((path for path in BOLD_FONT_CANDIDATES if path.exists()), None)
    pdf = FPDF(format=config.page_size)
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("BookUnicode", "", str(font_path))
    if bold_path:
        pdf.add_font("BookUnicode", "B", str(bold_path))
    bold = "B" if bold_path else ""
    pdf.set_title(str(run_metadata.get("title") or "Translated Book"))

    if config.title_page:
        pdf.add_page()
        pdf.set_y(pdf.h * 0.28)
        pdf.set_font("BookUnicode", bold, 18)
        pdf.multi_cell(
            0,
            10,
            str(run_metadata.get("title") or "Translated Book"),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        author = run_metadata.get("author")
        if author:
            pdf.ln(4)
            pdf.set_font("BookUnicode", "", 11)
            pdf.multi_cell(0, 7, str(author), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.add_page()
    pdf.set_font("BookUnicode", bold, 12)
    pdf.multi_cell(0, 8, "Run Metadata", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("BookUnicode", "", 9)
    for line in [
        f"Target language: {run_metadata.get('target_language')}",
        f"Layout: {config.mode}",
        f"Page size: {config.page_size}",
        "Human review required: yes",
    ]:
        pdf.multi_cell(0, 5.5, line, new_x="LMARGIN", new_y="NEXT")

    for page_units in build_book_template_pages(units):
        pdf.add_page()
        for unit in page_units:
            text = unit.target_text.strip()
            if not text:
                continue
            if unit.unit_type == "chapter_heading":
                pdf.ln(12)
                pdf.set_font("BookUnicode", bold, 15)
                pdf.multi_cell(0, 9, text, align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(8)
            else:
                pdf.set_font("BookUnicode", "", config.body_font_size)
                pdf.set_x(pdf.l_margin + 6)
                pdf.multi_cell(
                    pdf.epw - 6,
                    6.2,
                    text,
                    align="J",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
                pdf.ln(2)
        _page_number(pdf)

    pdf.add_page()
    pdf.set_font("BookUnicode", bold, 12)
    pdf.multi_cell(0, 8, "QA Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("BookUnicode", "", 9)
    for key, value in qa_summary.items():
        pdf.multi_cell(0, 5.5, f"{key}: {value}", new_x="LMARGIN", new_y="NEXT")
    _page_number(pdf)
    pdf.output(str(output))
    return {
        "written": True,
        "path": str(output),
        "warning": None,
        "layout": asdict(config),
        "source_layout_preserved": False,
        "overflow_blocks": 0,
    }


def export_preserve_source_pdf(
    output_path: str,
    units: List[BookLayoutUnit],
    source_pdf_path: str,
    config: Optional[BookLayoutExportConfig] = None,
) -> Dict[str, Any]:
    config = config or BookLayoutExportConfig(mode="preserve_source", page_size="source")
    if Path(source_pdf_path).suffix.casefold() != ".pdf":
        return {
            "written": False,
            "path": None,
            "warning": "preserve-source is PDF-only; use book-template for this input.",
            "fallback_required": True,
            "overflow_blocks": 0,
        }
    try:
        import fitz
    except ImportError:
        return {
            "written": False,
            "path": None,
            "warning": "PyMuPDF is unavailable; preserve-source fallback required.",
            "fallback_required": True,
            "overflow_blocks": 0,
        }

    source = fitz.open(source_pdf_path)
    output = fitz.open()
    unicode_font = find_unicode_font()
    font_name = "bookunicode" if unicode_font else "helv"
    font_file = str(unicode_font) if unicode_font else None
    overflow = 0
    by_page: Dict[int, List[BookLayoutUnit]] = {}
    for unit in units:
        by_page.setdefault(unit.source_page or 1, []).append(unit)
    for page_number in sorted(by_page):
        source_page = source[min(max(page_number - 1, 0), len(source) - 1)]
        page = output.new_page(width=source_page.rect.width, height=source_page.rect.height)
        for unit in by_page[page_number]:
            bbox = unit.bbox or [54, 54, source_page.rect.width - 54, source_page.rect.height - 54]
            rect = fitz.Rect(*bbox)
            font_size = 10.0
            remaining = page.insert_textbox(
                rect,
                unit.target_text,
                fontsize=font_size,
                fontname=font_name,
                fontfile=font_file,
            )
            while remaining < 0 and font_size > config.min_preserve_font_size:
                page.draw_rect(rect, color=None, fill=(1, 1, 1), overlay=True)
                font_size -= 0.5
                remaining = page.insert_textbox(
                    rect,
                    unit.target_text,
                    fontsize=font_size,
                    fontname=font_name,
                    fontfile=font_file,
                )
            if remaining < 0:
                overflow += 1
                continuation = output.new_page(width=source_page.rect.width, height=source_page.rect.height)
                continuation.insert_textbox(
                    fitz.Rect(54, 54, source_page.rect.width - 54, source_page.rect.height - 54),
                    unit.target_text,
                    fontsize=config.min_preserve_font_size,
                    fontname=font_name,
                    fontfile=font_file,
                )
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output.save(str(output_path_obj))
    output.close()
    source.close()
    return {
        "written": True,
        "path": str(output_path_obj),
        "warning": None,
        "layout": asdict(config),
        "source_layout_preserved": True,
        "layout_preservation": "best_effort",
        "overflow_blocks": overflow,
    }


def _page_number(pdf: Any) -> None:
    pdf.set_y(-12)
    pdf.set_font("BookUnicode", "", 8)
    pdf.cell(0, 5, str(pdf.page_no()), align="C")
