# TransCraft Technical Audit

Date: 2026-06-15

## Executive Verdict

Final verdict: **Promising but Needs Refactor**.

I would continue investing in the broad TIE idea, but not in the current implementation shape. The useful core is real: scoped translation memory, handoff generation, and explicit style contracts are valuable product primitives. The current code does not yet prove that TIE improves translation quality. It proves that prompt context can influence output and that JSON memory files can be loaded, filtered, and written.

The strongest evidence against the current architecture is that the Blood Meridian benchmark is partly hard-coded into prompts and contracts. `src/tie/style_contract.py` has a special-case `cormac_mccarthy` contract with the benchmark line "See the child.", and both `src/agents/translator.py` and `src/agents/stylist.py` include the same example directly in their prompts. That makes the benchmark unsuitable as evidence that the memory architecture learned or retrieved the behavior.

## What Is Actually Working

- The LangGraph workflow compiles and the unit suite passes: 23 tests passed locally.
- TIE can load memory from `global`, `genre`, `work`, and `user` scopes.
- Work-level isolation works for the cases covered by tests.
- Pending memory exists and low-confidence items can be routed away from active memory.
- Handoff generation is a useful artifact pattern.
- Style contracts can be injected into translator and stylist prompts.

## What Only Appears To Be Working

- The style intelligence layer appears to improve Blood Meridian, but the key behavior is encoded directly in prompts/contracts rather than discovered by TIE.
- The Memory Reviewer appears to prevent pollution, but its default mode is heuristic and mostly checks hand-written known bad cases.
- Evaluation appears quantitative, but it is AI-as-judge over truncated text and experiment scripts parse formatted stdout.
- Observability appears production-grade in README, but failures are often swallowed and style critic metrics are not wired into MLflow despite the design doc calling for them.

## Architecture Review

| Subsystem | Score | Strengths | Weaknesses | Recommendation |
| --- | ---: | --- | --- | --- |
| Chunking | 6/10 | Simple paragraph-first splitter; supports txt/pdf/epub. | Regex sentence split is naive; no token budget awareness; PDF/EPUB extraction keeps boilerplate and layout noise. | Add token-aware chunking, boilerplate removal, section metadata, and stable chunk IDs. |
| Translation Pipeline | 6/10 | Clear router -> extractor -> analyst -> translator -> stylist -> critic -> polisher -> curator graph. | Too many serial LLM calls; stylist/critic loops have weak quality gates; terminology extraction mutates global runtime state. | Collapse analyst/stylist where possible; make glossary extraction document-scoped; add deterministic contract tests. |
| TIE | 5/10 | Good product direction: scoped memory, handoff, context router. | Retrieval is substring/key based; no experiment proves causal benefit; style logic is benchmark-specific. | Keep TIE as a memory product layer, redesign retrieval/evaluation before adding features. |
| Memory Layer | 4/10 | JSON files are debuggable; schema has confidence/status/usage metadata. | No DB/indexing/concurrency; global pollution exists; auto backups create repo noise; pending has no review workflow. | Move to SQLite/Postgres plus vector index; enforce schema with migrations; remove automatic backup side effects. |
| Style Layer | 4/10 | Style contracts are a useful abstraction. | Hard-coded known-author rules; no clear separation between style profile, prompt rule, and learned memory. | Treat style contracts as explicit user/editor assets first; evaluate learned profiles later. |
| Evaluation Layer | 3/10 | AI judge exists; style critic has structured output. | Circular LLM evaluation; truncated full-doc eval; stdout parsing; reports contain prewritten success claims. | Build a gold test set with source, candidate translations, expected preferences, and blinded pairwise evaluation. |
| Observability Layer | 4/10 | Langfuse/MLflow wrappers are present. | Silent failures; no persisted prompt/version registry; style metrics not logged in main metrics. | Make observability non-blocking but explicit; log prompt versions, memory IDs used, cost, latency, and style metrics. |

## Overengineering Review

- Remove or merge the standalone Style & Culture Analyst unless it produces structured constraints consumed downstream. Currently it mostly adds another LLM call before translator/stylist.
- Merge Translator and Stylist for many modes. A single translation pass with explicit constraints may outperform draft + style rewrite at lower cost.
- Do not keep both Translation Critic and StyleConsistencyCritic as independent evaluators until there is evidence the second improves accepted output. The current style critic can approve with issues and never revise.
- Remove automatic memory backup on `MemoryManager` init. The repo already has 16 `memory_backup_*` folders, which is operational noise.
- Stop writing document terms to a shared `data/runtime/auto_glossary_candidate.json`; it bypasses TIE scope isolation.
- Reduce memory types. Current types overlap: `style_rule`, `author_style`, `inferred_author_style`, `narrative_voice`, and `style_contract` should become fewer, clearer concepts.

## Failure Mode Analysis

- Benchmark leakage: Blood Meridian-specific examples are embedded in `src/tie/style_contract.py`, `src/agents/translator.py`, and `src/agents/stylist.py`.
- Global memory pollution: current `memory/global/rules.json` contains highly specific literary rules with no source work/genre metadata, and `data/runtime/auto_glossary_candidate.json` mixes Alice, Attention, and Blood Meridian terms.
- Retrieval brittleness: `ContextRouter` normalizes to alphanumeric substring matching. This misses morphology, synonyms, inflection, pronouns, and stylistic similarity.
- Scale risk: every retrieval loads JSON files and linearly scans them. Thousands of entries and many books will be slow, hard to debug, and unsafe under concurrent writes.
- Schema drift: docs mention `author_style`, `inferred_author_style`, `narrative_voice`, and `style_contract`, but `MemoryManager` mostly routes non-character work items to `glossary.json`.
- Evaluation circularity: the same model family writes, critiques, revises, and judges; this can reinforce prompt expectations rather than measure translation quality.
- Silent observability failures: Langfuse span/flush errors are swallowed, so missing telemetry can look like successful telemetry.
- Experiment validity risk: validation scripts generate success narratives after weak pass criteria such as TIE ON score being greater than or equal to TIE OFF.

## Roadmap Review

Current roadmap:

1. v0.4 Semantic Retrieval
2. v0.5 Distillation Dataset Builder
3. v1.0 Translation Intelligence Platform

Decision: **revise, do not follow as-is**.

Semantic retrieval is the right next technical direction, but it should not be v0.4 until the evaluation harness is fixed. Otherwise vector search will make the system more complex without proving quality.

Recommended roadmap:

1. v0.4 Evaluation Harness and Memory QA: blinded A/B tests, fixed seed cases, pairwise judgments, human override fields, memory precision/recall.
2. v0.5 Scoped Storage and Retrieval Redesign: SQLite/Postgres records, embedding index, lexical fallback, memory IDs logged per chunk.
3. v0.6 Pipeline Simplification: fewer agents, explicit prompt variants, cost/latency metrics.
4. v0.7 Distillation Dataset Builder: only after high-quality accepted/rejected examples exist.
5. v1.0 Translation Intelligence Platform: only after memory usefulness is measurable across books/users.

## Highest ROI Improvements

| Rank | Improvement | Impact | Cost | Priority |
| ---: | --- | --- | --- | --- |
| 1 | Build a real evaluation harness with blinded TIE ON/OFF pairwise tests | Very high | Medium | P0 |
| 2 | Remove Blood Meridian examples from generic prompts and rerun benchmarks | Very high | Low | P0 |
| 3 | Stop global `auto_glossary_candidate.json`; make it work/user scoped | High | Low | P0 |
| 4 | Replace automatic memory backups with explicit backup command | Medium | Low | P1 |
| 5 | Add memory provenance: source doc, chunk ID, prompt version, accepted_by | High | Medium | P1 |
| 6 | Add semantic retrieval with lexical fallback after evaluation exists | High | Medium | P1 |
| 7 | Reduce agents: test single-pass translator+stylist vs current graph | High | Medium | P1 |
| 8 | Log exact memory IDs injected into every chunk | Medium | Low | P1 |
| 9 | Define a stricter memory schema and migrations | Medium | Medium | P2 |
| 10 | Add concurrency-safe storage | Medium | Medium | P2 |

## Brutal Honesty

If this project were mine, I would stop building new agents immediately. I would stop adding style critic layers, reviewer layers, and distillation plans until the system can prove that memory improves translation quality on held-out passages without benchmark-specific prompt leakage.

I would also stop treating generated memory artifacts as product progress. Interesting memory is not the same as useful memory. The important metric is whether retrieved memory changes a future translation in the preferred direction without harming unrelated texts.

What I would build next:

1. A small, brutal benchmark set: 50 source passages, TIE OFF output, TIE ON output, preferred output, and reason codes.
2. A memory provenance and retrieval log: every output should say exactly which memory items affected it.
3. A scoped storage redesign: document/work/user memory must not share mutable global files.
4. A clean ablation suite: prompt-only style contract vs memory retrieval vs reviewer vs critic loop.

## Final Answer

Continue investing in TIE as a concept, but redesign significant parts of the current implementation. The direction is promising because scoped reusable translation knowledge is a real platform primitive. The current implementation is overcomplicated relative to its evidence. It needs a stronger evaluation foundation, cleaner storage, less benchmark leakage, and fewer agents before semantic retrieval or dataset distillation will pay off.

