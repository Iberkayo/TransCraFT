# English → Turkish literary translation: controlled A/B experiment

This is an **isolated experiment** on `experiment/novel-translation-ab`. It does **not** change the TransCraFT main branch.

## The precise research question

> On the same English novel passage, how does the current generic
> `BookTranslationRunner` output compare with a direct translation by
> a chosen stronger model, judged blind by a human reader?

**Important limitation:** The baseline is the *current generic BookTranslationRunner*:
its draft translator plus its strategy, deterministic naturalness, and QA checks.
It is **not** the entire `main.py` LangGraph/TIE agent pipeline.
The direct challenger uses the **same** BookTranslationRunner ingestion,
chunking, and deterministic checks, replacing only the translation function.
This keeps the text selection and output QA comparable. The project does not
yet establish that full TIE beats a direct strong model.

## Prerequisites

- Python environment with the dependencies from `requirements.txt`
- Your own input book in `data/inputs/` (EPUB, PDF, TXT, or Markdown)
- API credentials **only if running a real comparison**, not for tests/dry-run
- Permission/rights to use the supplied text

For the standard baseline, set `OPENAI_API_KEY` and optionally
`DEFAULT_MINI_MODEL`. The baseline uses the current default
`gpt-4o-mini`, unless changed in your environment.

For a direct OpenAI challenger, choose the model explicitly via `--model`;
do **not** assume the default `DEFAULT_MAIN_MODEL` is the newest model.
For Anthropic install the optional extra:

```bash
pip install langchain-anthropic
```

Set `ANTHROPIC_API_KEY` for Claude. Exact model IDs and pricing can change;
use an available model ID from your provider's current documentation.

## 1. Smoke test: no API calls or cost

```bash
python -m pytest tests/test_novel_ab.py tests/test_score_novel_ab.py -q
python scripts/compare_novel_ab.py \
  --input data/inputs/your_novel.epub \
  --first-words 1000 \
  --dry-run
```

A dry run uses obvious **synthetic placeholders**. It only validates
document ingestion, chunk alignment, artifact export, and blinded format.
**It is not a translation quality benchmark.**

## 2. Real model comparison

```bash
# Keep your input file private; never commit full copyrighted books.
cp .env.example .env
# Set OPENAI_API_KEY in .env.

python scripts/compare_novel_ab.py \
  --input data/inputs/your_novel.epub \
  --first-words 1000 \
  --chunk-chars 3200 \
  --provider openai \
  --model YOUR_ACCESSIBLE_OPENAI_MODEL_ID
```

Or for Claude:

```bash
python scripts/compare_novel_ab.py \
  --input data/inputs/your_novel.epub \
  --first-words 1000 \
  --provider anthropic \
  --model YOUR_ACCESSIBLE_CLAUDE_MODEL_ID
```

For a file with front-matter detection mistakes, choose
`--start-at beginning` and confirm the source snippets in the blinded pack.
This first experiment only translates a bounded word count, not an entire
book. To avoid truncation, use complete chapters or adjust the selection.

**Warning:** A real run makes paid API calls (and may transfer text to model
providers). There is no cost ceiling or full retry/resume mechanism in this
experimental harness. Start with a short passage.

## 3. Read results without model labels

Find the new folder at `outputs/novel_ab/<run_id>/`:

| Output | Meaning |
| --- | --- |
| `blind_review.md` | English source + Candidate A/B, order independently randomized by passage, scorecard |
| `answer_key.json` | Reveals which model generated A/B for each passage — do not open yet |
| `human_scores.template.json` | Fillable A/B ratings and preference per passage; copy before editing |
| `comparison.json` | Run configuration, elapsed seconds and counts; no fabricated model ranking |
| `baseline/.../translation.md` | Existing generic Book Runner's output |
| `direct/.../translation.md` | Direct model's output |
| `*/.../metadata.json` | Every original source chunk, output chunk and QA flags |

Ask a fluent bilingual reader to score *fidelity, Turkish naturalness,
literary voice, dialogue, paragraph preservation, omissions and invented
meaning*. Record their preference before revealing `answer_key.json`.
For a stronger claim, repeat on multiple genres with more than one reviewer.

After scoring, save a filled-in copy of the JSON score template (for example
`human_scores.json`), and **only then** aggregate the blinded human scores:

```bash
python scripts/score_novel_ab.py \
  --run-dir outputs/novel_ab/YOUR_RUN_ID \
  --scores outputs/novel_ab/YOUR_RUN_ID/human_scores.json
```

The scoring script reveals the arm mapping only for aggregation and writes
`human_review_summary.json` and `human_review_summary.md`. It refuses
to score dry-run placeholders or incomplete human scorecards. Keep the
answer key concealed from reviewers until their submissions are final.

**Do not interpret** deterministic QA recommendations or word counts as an
automatic proof that either model won. This tool records wall-clock time,
but **does not** claim accurate per-provider token usage or API costs.
No actual comparative literary result exists until models have run and
human assessments have been recorded.

## Baseline and fairness

Both arms receive **identical extracted source chunks**. The tool refuses to
create a review if chunk texts differ. It does not randomize run order
(baseline runs first), so elapsed seconds may include provider-load effects.
The direct prompt uses the full current passage but not long-term TIE memory
or previous chunk summaries; the baseline generic runner likewise does not
inject TIE memory into its translator.

The current generic Book Runner runs deterministic target-language checks
after *both* translations. To understand raw differences, open individual
metadata outputs and the translator traces. This experiment does not quantify
cost, and the Claude adapter is opt-in, not an installed dependency.

## Next experiment

Compare **three** modes — current Book Runner, full LangGraph/TIE, and direct
model — using controlled model choices, per-chapter narrative memory,
real usage counters and a hidden, held-out human evaluation corpus.
Only after that should we decide which agents improve literary quality.
