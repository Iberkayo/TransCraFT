# Translation Memory Retrieval

## Purpose

TransCraft v0.9.6 retrieves relevant source-target examples from local private translation-memory artifacts. The examples are reference evidence for translators and reviewers.

Retrieved examples are not automatic truth and are never applied to a translation by this layer.

## Relationship To v0.9.5

v0.9.5 creates local alignment and translation-memory JSONL files under:

```text
outputs/parallel/
```

v0.9.6 reads those files, filters entries by alignment confidence, ranks source segments against a new source chunk, and builds a reference pack.

The two layers remain separate:

- v0.9.5: extraction, alignment, and local TM generation
- v0.9.6: local TM loading, filtering, ranking, and reference packaging

## Why This Is Not Fine-Tuning

The retrieval layer does not train or update model weights. It performs deterministic local search over private JSONL files.

Translation-memory examples may later be supplied to a translation runner as optional context, but only when a caller explicitly chooses to use the reference pack.

## How Local Retrieval Works

The retriever:

1. Loads `*_translation_memory.jsonl` files from a local directory.
2. Handles missing optional fields with conservative defaults.
3. Excludes low-confidence alignments by default.
4. Normalizes the new source query.
5. Computes lightweight similarity using:
   - normalized token overlap
   - character trigram overlap
   - source-length ratio
6. Returns the highest-scoring references above a minimum score.
7. Builds previews and explicit safety flags.

No heavy embedding or machine-learning dependency is required.

## Confidence Filtering

Supported minimum alignment confidence levels:

```text
high
medium
low
```

The default retrieval minimum is `medium`. The future integration helper defaults to `high`.

Low-confidence alignment entries are not deleted. They remain local for explicit review or lower-threshold diagnostics.

## Reference-Only Usage

Every retrieved example is marked:

```json
{
  "use_mode": "reference_only",
  "human_review_required": true,
  "do_not_auto_copy": true
}
```

The retrieval API:

- does not modify a translation
- does not write to translation memory
- does not promote an example to global/work memory
- does not automatically add examples to model prompts

## Human Review Requirement

Alignment confidence and retrieval similarity do not prove semantic correctness. Translators should verify:

- whether the source situation is genuinely comparable
- whether terminology matches the current domain
- whether register and style are appropriate
- whether the historical TM translation itself is correct

## Querying Local Translation Memory

```bash
python scripts/query_translation_memory.py \
  --tm-dir outputs/parallel \
  --query "The coach arrived late at night." \
  --top-k 5
```

The terminal displays short previews only.

To write a local reference pack:

```bash
python scripts/query_translation_memory.py \
  --tm-dir outputs/parallel \
  --query-file local_query.txt \
  --output-json reference_pack.json
```

Simple output filenames are written under:

```text
outputs/tm_retrieval/
```

This directory must remain local and ignored.

## Future Translation Runner Integration

Future translation code can call:

```python
build_translation_reference_context(
    source_chunk,
    tm_dir="outputs/parallel",
    top_k=3,
    min_alignment_confidence="high",
)
```

The function returns a reference pack. It does not mutate translation state or automatically inject content into a prompt.

## Copyright And Local Artifact Policy

Real translation-memory files and runtime reference packs may contain copyrighted source and target text.

- Do not commit `outputs/parallel/`.
- Do not commit `outputs/tm_retrieval/`.
- Do not commit source/target PDFs.
- Do not put long real excerpts in committed diagnostics.
- Use synthetic examples for committed tests and reports.
- Keep all real retrieved text local/private.

## Limitations

- Similarity is lexical and structural, not semantic embedding search.
- A high similarity score does not prove that a translation should be reused.
- Poor alignment can produce misleading references.
- Human review remains required.

