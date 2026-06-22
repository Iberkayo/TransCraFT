# Translation Memory Retrieval Diagnostics

## Summary

- Synthetic TM entries: `4`
- Queries tested: `3`
- Default minimum confidence: `medium`
- Low-confidence entries are excluded by default.

## Retrieval Examples

### Query 1

- Query: `The coach arrived late at night.`
- References retrieved: `2`
- TM IDs: `['tm_syn_001', 'tm_syn_003']`
- Scores: `[1.0, 0.163368]`
- Reference-only flags: `True`

### Query 2

- Query: `A carriage entered the village before sunrise.`
- References retrieved: `2`
- TM IDs: `['tm_syn_002', 'tm_syn_003']`
- Scores: `[0.512537, 0.164899]`
- Reference-only flags: `True`

### Query 3

- Query: `Rain fell over the fields.`
- References retrieved: `2`
- TM IDs: `['tm_syn_003', 'tm_syn_001']`
- Scores: `[0.385673, 0.151445]`
- Reference-only flags: `True`

## Confidence Filtering

- High-only results: `2`
- Low-allowed results: `4`
- Total references retrieved across example queries: `6`

## Limitations

- This is retrieval infrastructure, not fine-tuning.
- Retrieved examples are reference-only.
- Human review is required.
- Local real TM artifacts may contain copyrighted text and must remain untracked.
