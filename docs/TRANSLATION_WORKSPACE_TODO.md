# Translation Workspace TODO

## v0.9.5 - Terminology Decision Point Detector

Goal:

```text
Detect terms and phrases that should be decided by the human before translation.
```

The detector should generate decision cards like:

```json
{
  "term": "schoolmaster",
  "risk_type": "semantic_ambiguity",
  "recommended_translation": "okul hocası",
  "options": ["okul hocası", "öğretmen", "okul müdürü"],
  "occurrences": [
    {
      "sentence": "His father has been a schoolmaster.",
      "page": 5,
      "chapter": 1
    }
  ],
  "ask_user": true,
  "scope_options": ["sentence", "chapter", "work"]
}
```

Requirements:

- Show all occurrence sentences.
- Show source page/chapter if available.
- Generate translation options.
- Use human correction dataset and QA risk maps.
- Do not ask every word.
- Ask only high-value decisions.

Target decision types:

- semantic ambiguity
- literary term
- character/title consistency
- religious/historical reference
- cultural reference
- repeated motif
- previously corrected term
- translation risk from human feedback

Blood Meridian examples:

- schoolmaster
- scullery fire
- Dipper
- flatboat
- full house
- kid / boy / child
- Judge
- Reverend

## v0.9.6 - Decision Memory / Apply Scope

Goal:

```text
When the user chooses a translation decision, save it with scope.
```

Scope options:

- this sentence
- this chunk
- this chapter
- entire work
- global memory

Example:

```json
{
  "source_term": "schoolmaster",
  "chosen_translation": "okul hocası",
  "scope": "work",
  "work_id": "blood_meridian",
  "reason": "Human reviewer selected this as better than okul müdürü."
}
```

Requirements:

- Do not overwrite memory silently.
- Ask before promoting to work/global memory.
- Track who/what created the decision.
- Allow later revision.

## v0.9.7 - Review Priority + Why Review Panel Data

Goal:

```text
Replace vague QA with clear review priority and explanation.
```

Output example:

```json
{
  "chunk_id": "bm_first5_02",
  "review_priority": "high",
  "why_review": [
    "Potential semantic mistranslation: flatboat rendered as düz tekne/sal decision needed.",
    "Literary register issue: schoolmaster may not mean okul müdürü.",
    "Turkish fluency warning: phrase may sound unnatural."
  ],
  "suggested_actions": [
    "Confirm flatboat translation.",
    "Confirm schoolmaster translation.",
    "Review literary rhythm."
  ]
}
```

Priority levels:

- low
- medium
- high
- critical

High priority examples:

- meaning loss
- wrong term
- English residue
- broken Turkish
- chunk boundary risk
- character/title inconsistency
- protected term loss

## v0.9.8 - Translation Heatmap Data

Goal:

```text
Generate heatmap metadata for UI.
```

The UI should be able to color chunks/spans by risk:

- green = clean
- yellow = review recommended
- red = semantic/term risk
- purple = style/rhythm risk
- blue = user decision needed

Output should include:

```json
{
  "span": "schoolmaster",
  "start": 120,
  "end": 132,
  "risk_color": "blue",
  "risk_type": "decision_needed",
  "message": "Choose translation for schoolmaster."
}
```

Do not build UI yet. Only produce data.

## v0.9.9 - Character / Term Consistency Map

Goal:

```text
Track repeated terms, characters, titles, places, and chosen translations across a work.
```

Example map:

```json
{
  "Judge Holden": "Yargıç Holden",
  "Reverend Green": "Papaz Green",
  "the kid": "çocuk / oğlan decision needed",
  "flatboat": "sal",
  "Dipper": "Büyük Kepçe"
}
```

Requirements:

- Detect inconsistent translations.
- Warn when chosen memory conflicts with current output.
- Support accepted alternatives if intentional.

## v0.10 - React Translation Workspace MVP

Goal:

```text
Build the first interactive UI.
```

Suggested stack:

- Frontend: React + Vite + Tailwind
- Backend: FastAPI
- Streaming: WebSocket or Server-Sent Events
- Storage: SQLite first, PostgreSQL later

### 1. Project Upload

- Upload PDF/TXT/DOCX
- Select source language
- Select target language
- Select genre
- Select author/work profile

### 2. Source Review

- Show extracted text
- Show source cleanup warnings
- Show page/chapter boundaries
- Let user approve extraction before translation

### 3. Decision Queue

Cards should show:

- source term
- recommended translation
- options
- all occurrence sentences
- page/chapter
- reason
- scope selection

Buttons:

- Accept recommended
- Choose alternative
- Custom translation
- Apply to sentence/chapter/work
- Skip

### 4. Translation Workspace

Three-panel layout:

- Left: source text with highlighted risk terms
- Center: live Turkish translation
- Right: QA flags, suggested edits, decision cards

### 5. Review Panel

Show:

- Review Priority
- Why Review?
- Suggested Edits
- Human Correction Feedback
- Foreign Residue
- Semantic QA
- Fluency QA

### 6. Export

Export:

- Final Translation.docx
- Final Translation.md
- Source + Translation side-by-side.docx
- QA Report.md
- Glossary Decisions.json
- Human Corrections.json
- Suggested Edits.md

## Future Product Ideas

### Ask Before Translate Mode

Before translating, system asks the user critical terms and style decisions.

### Style Lock

User can mark a paragraph as:

```text
Use this tone as reference.
```

System extracts style notes and applies them to later chunks.

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

Export final text plus all supporting review artifacts.
