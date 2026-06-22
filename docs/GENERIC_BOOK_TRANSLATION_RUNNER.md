# Generic Book Translation Runner

## Purpose

TransCraft v0.9.7 adds a bounded local runner for translating PDF, EPUB, TXT, and Markdown books through the existing translation and QA components.

The runner is book-independent. Input documents are local evaluation fixtures, not architecture or hard-coded translation rules.

## Range Semantics

For PDF input, `--first-pages` means physical PDF pages.

For EPUB, TXT, and Markdown input, `--first-pages` means page-equivalents. The default is 300 source words per page-equivalent and can be changed with `--words-per-page`.

Use `--first-words` when an exact word-based range is preferred. `--first-pages` and `--first-words` are mutually exclusive.

## Translation Memory Safety

The runner can retrieve local translation-memory references from `outputs/parallel/`. Retrieved examples are stored in run metadata as reference evidence.

They are not automatically copied, promoted, or injected into the translator prompt. Disable retrieval with `--no-tm`.

## Usage

```bash
python scripts/translate_book.py \
  --input data/inputs/example.epub \
  --target tr \
  --first-pages 5 \
  --pdf
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

## Diagnostics

The committed diagnostic uses synthetic text and a stub translator:

```bash
python scripts/run_book_runner_diagnostics.py
```

It validates orchestration and artifact contracts without calling a model.
