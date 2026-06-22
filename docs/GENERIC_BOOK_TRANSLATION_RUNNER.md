# Generic Book Translation Runner

## Purpose

TransCraft v0.9.7.1 adds structure-aware range selection and layout-aware export to the bounded local PDF, EPUB, TXT, and Markdown runner.

The runner is book-independent. Input documents are local evaluation fixtures, not architecture or hard-coded translation rules.

## Range Semantics

For PDF input, `--first-pages` means physical PDF pages.

For EPUB, TXT, and Markdown input, `--first-pages` means page-equivalents. The default is 300 source words per page-equivalent and can be changed with `--words-per-page`.

Use `--first-words` when an exact word-based range is preferred. `--first-pages` and `--first-words` are mutually exclusive.

By default, translation starts at the first likely chapter heading or strong body paragraph and excludes detected table-of-contents/front-matter units. Detection is heuristic and skipped units remain recorded in metadata.

Use `--start-at beginning --include-front-matter --no-exclude-toc` to intentionally translate from the beginning.

## Layout Modes

The default `book-template` mode produces a clean A5 book-style PDF with a title page, run metadata, chapter heading treatment, paragraph indentation, spacing, and page numbers.

`preserve-source` is a PDF-only best-effort mode. When PyMuPDF is available, source page dimensions and text-block bounding boxes are used to place translated blocks approximately. Translation expansion can still change line breaks, reduce font size, or create continuation pages.

For EPUB, TXT, or Markdown input, `preserve-source` falls back to `book-template` and records a layout warning.

## Translation Memory Safety

The runner can retrieve local translation-memory references from `outputs/parallel/`. Retrieved examples are stored in run metadata as reference evidence.

They are not automatically copied, promoted, or injected into the translator prompt. Disable retrieval with `--no-tm`.

## Usage

```bash
python scripts/translate_book.py \
  --input data/inputs/example.epub \
  --target tr \
  --first-pages 5 \
  --pdf \
  --layout book-template \
  --start-at body
```

Additional options:

```text
--source
--first-words
--words-per-page
--chunk-chars
--tm-dir
--tm-top-k
--tm-min-confidence
--no-tm
--output-root
--layout book-template|preserve-source
--page-size
--start-at body|beginning
--include-front-matter
--exclude-toc / --no-exclude-toc
--no-title-page
--md
--side-by-side
--quality-report
--metadata
```

When no output flags are supplied, the runner writes translation Markdown, metadata JSON, and a quality report. `--pdf` produces a Unicode PDF when a supported local font is available.

## Local Artifacts

Runs are written under:

```text
outputs/book_runs/{run_id}/
```

Possible files:

```text
translation.md
translation.pdf
side_by_side.md
metadata.json
quality_report.md
```

These files may contain copyrighted source or translated text. Keep `outputs/book_runs/` local and untracked.

## Quality Pipeline

The runner applies:

- source cleanup and extraction-quality checks
- sentence-safe chunking
- generic translation strategy planning
- the existing translation agent
- deterministic revision checklist evaluation
- target-only naturalness checks
- foreign-residue checks
- literary semantic QA
- Turkish fluency QA when applicable
- the deterministic quality gate

Quality reports are guardrails. They do not prove semantic equivalence, literary merit, or publication readiness. Human review remains required.

PDF layout preservation is best-effort. Translation length can change pagination and line breaks.

## Diagnostics

The committed diagnostic uses synthetic text and a stub translator:

```bash
python scripts/run_book_runner_diagnostics.py
python scripts/run_layout_export_diagnostics.py
```

It validates orchestration and artifact contracts without calling a model.
