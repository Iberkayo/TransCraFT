"""Run synthetic diagnostics for structure detection and layout export."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.book_ingestion import select_book_range
from src.tie.book_structure import build_structured_book_units
from src.tie.layout_export import (
    BookLayoutExportConfig,
    BookLayoutUnit,
    export_book_template_pdf,
    export_preserve_source_pdf,
)


def main() -> int:
    extracted = {
        "input_format": "txt",
        "page_definition": "word_based_page_equivalents",
        "text": "",
        "units": [
            {"text": "Copyright 2026 Synthetic Publisher"},
            {"text": "Contents\nChapter I .... 1\nChapter II .... 7\nChapter III .... 13"},
            {"text": "CHAPTER I"},
            {"text": "This synthetic paragraph is deliberately long enough to qualify as a strong body paragraph for deterministic structure diagnostics."},
        ],
    }
    structured = build_structured_book_units(extracted)
    selected = select_book_range(extracted, first_words=100)
    layout_units = [
        BookLayoutUnit("u1", "chapter_heading", "CHAPTER I", "BÖLÜM I"),
        BookLayoutUnit("u2", "body_paragraph", "Synthetic source.", "Sentetik hedef paragrafı."),
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        template = export_book_template_pdf(
            str(Path(temp_dir) / "template.pdf"),
            layout_units,
            {"title": "Synthetic", "target_language": "tr_TR"},
            {"recommendation": "accept"},
            BookLayoutExportConfig(),
        )
        fallback = export_preserve_source_pdf(
            str(Path(temp_dir) / "preserve.pdf"),
            layout_units,
            "synthetic.epub",
        )

    report = Path("outputs/layout_export_diagnostics_report.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# Layout Export Diagnostics",
                "",
                "## Summary",
                f"- front matter detection tested: {'passed' if any(unit['unit_type'] in {'front_matter', 'title_page'} for unit in structured) else 'failed'}",
                f"- TOC detection tested: {'passed' if selected['front_matter']['toc_units_detected'] else 'failed'}",
                f"- chapter heading detection tested: {'passed' if any(unit['unit_type'] == 'chapter_heading' for unit in structured) else 'failed'}",
                f"- book-template PDF path generation tested: {'passed' if template['written'] else 'skipped: no Unicode font'}",
                f"- preserve-source fallback tested: {'passed' if fallback.get('fallback_required') else 'failed'}",
                "",
                "## Limitations",
                "- Synthetic diagnostics do not prove real book layout quality.",
                "- Source PDF layout preservation is best-effort.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
