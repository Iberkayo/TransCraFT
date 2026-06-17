# Interactive Translation Workspace Roadmap

## 1. Product Vision

TransCraft should not compete as a simple one-click translator. It should become a professional translation workspace for translators who need consistency, context, traceability, and human control.

DeepL translates quickly. TransCraft helps translators make consistent, context-aware, reviewable decisions.

The core product idea:

- Ask before translating.
- Translate with memory.
- Show live QA.
- Let human corrections become reusable knowledge.

The product should move from a terminal-based translation QA pipeline into an interactive workspace where translators can inspect source extraction, answer important terminology and style questions, review chunk-level risks, apply suggested edits, and export both the final translation and the review evidence behind it.

## 2. Core User Workflow

1. User uploads PDF/TXT/DOCX.
2. TransCraft extracts and cleans source text.
3. System detects risky terms, ambiguous expressions, character names, motifs, and style decisions.
4. User answers decision cards before translation.
5. System translates chunk by chunk.
6. Translation appears live in the workspace.
7. QA flags and suggested edits appear in a side panel.
8. User accepts, rejects, or modifies suggestions.
9. Accepted decisions are saved to scoped memory.
10. Final translation and reports are exported.

## 3. Product Principles

- Human decisions should happen before high-risk translation choices are locked in.
- Memory must be scoped and explainable.
- QA should explain why a passage needs review, not just say that it needs review.
- Suggested edits should remain suggestions unless a human accepts them.
- The workspace should make uncertainty visible.
- The system should preserve source/target alignment wherever possible.
- Exported artifacts should support review, handoff, and later reuse.

## 4. What The Workspace Is Not

- Not a one-click publication engine.
- Not a replacement for literary review.
- Not a UI wrapper around a raw LLM prompt.
- Not a global-memory dump that contaminates unrelated works.

## 5. Near-Term Product Direction

The next releases should create the data foundation for a future UI:

- Decision cards for high-value terms and style choices.
- Scoped decision memory.
- Review priority and "why review" explanations.
- Heatmap metadata for source/target risk spans.
- Character and term consistency maps.

These should be built as backend/data capabilities first. The React workspace should come after the data contracts are stable.

## 6. Future Product Ideas

### Ask Before Translate Mode

Before translating, the system asks the user critical terms and style decisions. This prevents recurring mistranslations such as ambiguous titles, character labels, religious references, or repeated motifs.

### Style Lock

User can mark a paragraph as:

```text
Use this tone as reference.
```

The system extracts style notes and applies them to later chunks.

### Side-by-Side Diff Mode

Compare:

```text
raw translation
QA revised translation
human edited translation
```

Show differences:

```text
okul müdürüymüş -> okul hocasıymış
düz tekne -> sal
Kepçe -> Büyük Kepçe
```

### Human Correction Memory

Accepted human edits become memory candidates.

System asks:

```text
Save this correction for this sentence / chapter / whole work / globally?
```

### Export Pack

Export final text plus all supporting review artifacts:

- Final translation
- Side-by-side source/target review copy
- QA report
- Glossary decisions
- Human corrections
- Suggested edits
- Memory candidates

