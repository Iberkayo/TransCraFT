"""Run a synthetic, offline diagnostic for the generic book runner."""

from __future__ import annotations

import tempfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.book_runner import BookTranslationRunner, build_book_run_config


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "synthetic_book.txt"
        source.write_text(
            "The train reached the quiet station after midnight. "
            "A traveler stepped down and looked toward the empty road.",
            encoding="utf-8",
        )

        def translator(text: str, context: dict) -> str:
            assert context["tm_reference_usage"] == "metadata_only"
            return "Tren gece yarısından sonra sessiz istasyona ulaştı. Bir yolcu indi ve boş yola baktı."

        config = build_book_run_config(
            str(source),
            first_words=50,
            tm_enabled=False,
            output_root=str(root / "outputs"),
            write_pdf=False,
            write_side_by_side=True,
        )
        result = BookTranslationRunner(translator=translator).run(config)

    report = Path("outputs/book_runner_diagnostics_report.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# Generic Book Runner Diagnostics",
                "",
                "- Synthetic input: passed",
                f"- Chunks translated: {result.chunks_translated}",
                f"- Source words: {result.source_words}",
                f"- Target words: {result.target_words}",
                f"- Quality recommendation: {result.recommendation}",
                "- TM prompt injection: disabled",
                "- Real model call: not used",
                "- Human review required: yes",
                "",
                "The diagnostic validates orchestration and artifact contracts, not translation quality.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
