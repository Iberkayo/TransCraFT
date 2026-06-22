"""Generic Unicode PDF export for local book runs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/calibri.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
]

BOLD_FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("C:/Windows/Fonts/calibrib.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
]


def find_unicode_font() -> Optional[Path]:
    return next((path for path in FONT_CANDIDATES if path.exists()), None)


def export_translation_pdf(
    output_path: str,
    translation_chunks: Iterable[str],
    run_metadata: Dict[str, Any],
    qa_summary: Dict[str, Any],
) -> Dict[str, Any]:
    font_path = find_unicode_font()
    if font_path is None:
        return {
            "written": False,
            "path": None,
            "warning": "No local Unicode font was found; PDF export skipped.",
        }

    from fpdf import FPDF

    bold_path = next((path for path in BOLD_FONT_CANDIDATES if path.exists()), None)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("BookUnicode", "", str(font_path))
    if bold_path:
        pdf.add_font("BookUnicode", "B", str(bold_path))
    bold_style = "B" if bold_path else ""

    pdf.add_page()
    pdf.set_font("BookUnicode", bold_style, 16)
    pdf.multi_cell(0, 9, "TransCraft Book Translation Test", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("BookUnicode", "", 10)
    summary_lines = [
        f"Input: {run_metadata.get('input_path')}",
        f"Target language: {run_metadata.get('target_language')}",
        f"Range: {_format_range(run_metadata.get('range', {}))}",
        f"Page definition: {run_metadata.get('page_definition')}",
        f"TM retrieval: {'enabled' if run_metadata.get('tm_retrieval', {}).get('enabled') else 'disabled'}",
        "Human review required: yes",
    ]
    for line in summary_lines:
        pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    pdf.add_page()
    for index, chunk in enumerate(translation_chunks, start=1):
        text = (chunk or "").strip()
        if not text:
            continue
        pdf.set_font("BookUnicode", bold_style, 12)
        pdf.multi_cell(0, 7, f"Section {index}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("BookUnicode", "", 10.5)
        for paragraph in re.split(r"\n\s*\n", text):
            if paragraph.strip():
                pdf.multi_cell(0, 6, paragraph.strip(), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1.5)

    pdf.add_page()
    pdf.set_font("BookUnicode", bold_style, 13)
    pdf.multi_cell(0, 8, "QA Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("BookUnicode", "", 10)
    for key, value in qa_summary.items():
        pdf.multi_cell(0, 6, f"{key}: {value}", new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(output))
    return {"written": True, "path": str(output), "warning": None, "font_path": str(font_path)}


def _format_range(range_data: Dict[str, Any]) -> str:
    mode = range_data.get("mode", "unknown")
    if mode == "first_physical_pages":
        return f"{range_data.get('selected_pages')} physical pages"
    if mode == "first_page_equivalents":
        return (
            f"{range_data.get('estimated_page_equivalents')} page-equivalents / "
            f"{range_data.get('selected_word_count')} words"
        )
    return f"{range_data.get('selected_word_count')} words ({mode})"
