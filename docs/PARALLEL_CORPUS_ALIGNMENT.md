# Parallel Corpus Alignment

## Purpose

TransCraft v0.9.5 adds a generic local pipeline for pairing source and target documents, extracting comparable text units, producing conservative alignment candidates, and creating private translation-memory artifacts.

The engine is book-independent. Input books and documents are evaluation fixtures, not architecture.

## What A Parallel Corpus Means

A parallel corpus contains source-language text and a corresponding target-language translation. TransCraft processes paired documents in document order and creates candidate source-target alignments using:

- filename and metadata-based pair discovery
- page order
- paragraph order
- generic heading detection
- relative document position
- source/target length ratios

Cross-language lexical similarity is intentionally not the main signal. When structural evidence is weak, alignments are marked low confidence.

## Why This Is Not Fine-Tuning

The generated translation memory is local private reference data. It is not uploaded as a training dataset and is not used to update model weights.

Potential later uses include:

- retrieval/reference memory
- terminology review
- translator decision support
- consistency checking
- human-reviewed alignment datasets

Human review is required before reusing alignment or glossary candidates.

## EN/TR Folder Layout

Place local source and target PDFs under:

```text
data/inputs/EN/
data/inputs/TR/
```

These folders are ignored locally and must not be committed.

Example:

```text
data/inputs/EN/source_book.pdf
data/inputs/TR/translated_book.pdf
```

## Manifest Mode

If this file exists:

```text
data/inputs/parallel_manifest.json
```

the engine uses its explicit pair definitions. The real manifest is local-only.

Use the committed example as a template:

```text
data/inputs/parallel_manifest.example.json
```

Manifest pairing is preferred when filenames differ significantly across languages.

## Auto-Discovery Mode

If no local manifest exists, the engine:

1. Lists PDFs under the source and target language folders.
2. Normalizes filenames and available PDF metadata.
3. Scores candidate pairs with filename tokens, title metadata, author metadata, and page-count similarity.
4. Selects one-to-one pair candidates.
5. Marks pair confidence as high, medium, or low.

Auto-discovery does not guarantee that two documents are translations of each other. Review pair candidates before relying on their output.

## Building A Local Corpus

```bash
python scripts/build_parallel_corpus.py \
  --input-root data/inputs \
  --source-lang EN \
  --target-lang TR \
  --max-pages 20
```

Useful options:

```text
--max-pairs
--pair-id
--mode paragraph
--write-local-artifacts / --no-write-local-artifacts
```

The default page limit prevents accidental full-book processing during diagnostics.

## Generated Artifacts

Per pair:

```text
outputs/parallel/{pair_id}_alignment.jsonl
outputs/parallel/{pair_id}_translation_memory.jsonl
outputs/parallel/{pair_id}_glossary_candidates.json
outputs/parallel/{pair_id}_style_profile.json
outputs/parallel/{pair_id}_alignment_report.md
```

Combined:

```text
outputs/parallel/parallel_corpus_build_report.md
outputs/parallel/parallel_corpus_build_summary.json
```

JSONL alignment and translation-memory files may contain long copyrighted source and target text. They must remain local and untracked.

## Translation Memory

Translation-memory entries include:

- source and target text
- source and target word counts
- alignment confidence
- generic text type/register observations
- a local-private-reference usage policy

Low-confidence entries are retained for review rather than promoted as reliable memory.

## Glossary Candidates

Glossary extraction is conservative. It looks for repeated capitalized terms and recurring target candidates within non-low-confidence aligned units.

Every glossary candidate is marked for human review. The system does not silently promote candidates to global or work memory.

## Style/Profile Observations

The style profile contains descriptive statistics such as:

- source/target average sentence length
- dialogue density
- paragraph-length ratio
- target punctuation frequencies

This is a profile observation, not learned author style and not proof of translation quality.

## Copyright And Local Artifact Policy

- Do not commit input PDFs.
- Do not commit extracted full text.
- Do not commit full alignment or translation-memory JSONL.
- Do not print long excerpts to terminal output.
- Keep `outputs/parallel/` local and ignored.
- Commit only generic code, tests, documentation, and safe metadata examples.

## Support For The Generic Translation Engine

This layer establishes data contracts for future:

- human-reviewed translation memory retrieval
- terminology decision cards
- scoped memory candidates
- consistency maps
- review-priority explanations
- private corpus evaluation

It does not add book-specific translation behavior.

