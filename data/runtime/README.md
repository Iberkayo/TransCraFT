# Runtime Glossary Storage

`data/runtime/auto_glossary_candidate.json` is deprecated and kept only as a legacy artifact.

Current code must write runtime glossary candidates through `src/core/scoped_glossary.py`, which stores them under:

```text
data/runtime/glossaries/genre-<genre>__work-<work_id>__user-<user_id>/auto_glossary_candidate.json
```

Do not add new writes to the legacy global file. Existing data can be migrated manually into the appropriate scoped glossary directory.
