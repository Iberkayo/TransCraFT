# End-to-End Translation Quality Benchmark

## 1. Executive Summary

- Cases tested: 20
- Modes: baseline_translator_only, strategy_only, full_tie_quality_chain
- Baseline wins: 0
- Strategy-only wins: 0
- Full-chain wins: 4
- Ties: 16
- Full-chain harms: 0
- Translationese baseline/strategy/full: 5 / 1 / 1
- Naturalness baseline/strategy/full: 4.85 / 4.94 / 4.93
- Protected term failures: 5
- Translation errors: 0
- Impact label: **inconclusive**

This is not a human evaluation. Heuristic scores are approximate.
Meaning preservation cannot be fully verified automatically.
Human review pack must be consulted before drawing conclusions.
Synthetic cases are limited. Broad quality claims need human review.

## 2. Benchmark Modes

- **baseline_translator_only**: Translator without strategy planner, revision checklist, or target naturalness.
- **strategy_only**: Translator with strategy planner and language profile.
- **full_tie_quality_chain**: Full TIE chain including strategy planner, revision checklist, and target-only Turkish naturalness pass.

## 3. Overall Results

| Case | Genre | Preferred | Base T | Strat T | Full T | Base Nat | Strat Nat | Full Nat |
| ---- | ----- | --------- | -----: | ------: | -----: | -------: | --------: | -------: |
| business_relative_clause_001 | business | full_chain | 1 | 0 | 0 | 4.4 | 4.8 | 4.8 |
| noun_stack_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| passive_double_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| phrasal_verb_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| corporate_translationese_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 4.8 |
| academic_abstract_001 | academic | tie | 0 | 0 | 0 | 4.8 | 4.8 | 4.8 |
| literary_fragments_001 | literary | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| idiom_metaphor_001 | general | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| pronoun_heavy_001 | general | full_chain | 0 | 0 | 0 | 4.8 | 5.0 | 5.0 |
| preposition_heavy_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| nested_relative_clause_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| academic_noun_pile_001 | academic | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| literary_implied_subject_001 | literary | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| metaphor_nonliteral_001 | general | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| clear_split_required_001 | business | full_chain | 2 | 0 | 0 | 3.8 | 4.6 | 4.6 |
| numbers_dates_001 | business | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| meaning_preservation_trap_001 | general | tie | 1 | 1 | 1 | 4.6 | 4.6 | 4.6 |
| no_rewrite_needed_001 | literary | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |
| target_naturalness_opportunity_001 | business | full_chain | 1 | 0 | 0 | 4.6 | 5.0 | 5.0 |
| aggressive_rewrite_danger_001 | literary | tie | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 |

## 4. Where Full Chain Helped

- **business_relative_clause_001**: T 1→0, Nat 4.4→4.8
- **pronoun_heavy_001**: T 0→0, Nat 4.8→5.0
- **clear_split_required_001**: T 2→0, Nat 3.8→4.6
- **target_naturalness_opportunity_001**: T 1→0, Nat 4.6→5.0

## 5. Where Full Chain Did Not Help

- **noun_stack_001**: scores comparable across modes
- **passive_double_001**: scores comparable across modes
- **phrasal_verb_001**: scores comparable across modes
- **corporate_translationese_001**: scores comparable across modes
- **academic_abstract_001**: scores comparable across modes
- **literary_fragments_001**: scores comparable across modes
- **idiom_metaphor_001**: scores comparable across modes
- **preposition_heavy_001**: scores comparable across modes
- **nested_relative_clause_001**: scores comparable across modes
- **academic_noun_pile_001**: scores comparable across modes
- **literary_implied_subject_001**: scores comparable across modes
- **metaphor_nonliteral_001**: scores comparable across modes
- **numbers_dates_001**: scores comparable across modes
- **meaning_preservation_trap_001**: scores comparable across modes
- **no_rewrite_needed_001**: scores comparable across modes
- **aggressive_rewrite_danger_001**: scores comparable across modes

## 6. Where Full Chain Harmed or Over-edited

_None._

## 7. Protected Term / Number Safety

Total protected term failures: 5
- **corporate_translationese_001**: 1 protected term(s) lost in full chain
- **numbers_dates_001**: 2 protected term(s) lost in full chain
- **meaning_preservation_trap_001**: 2 protected term(s) lost in full chain

## 8. Human Review Needed

See `outputs/end_to_end_human_review_pack.md` for case-by-case human review template.
Heuristic metrics cannot replace human judgment on meaning preservation and naturalness.

## 9. Recommendation

Results are inconclusive. The TIE quality infrastructure is sound but differences are not large enough to draw strong conclusions from this synthetic benchmark alone.
