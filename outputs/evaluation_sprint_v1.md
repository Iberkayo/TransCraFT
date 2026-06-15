# TransCraft Evaluation Sprint v1

## 1. Executive Summary

This sprint does **not** prove the full claim that TIE v0.3.1 improves translation quality across Alice, Blood Meridian, and Attention Is All You Need. The repository contains useful historical evidence, but it does not contain the complete required matrix of separately generated v0.2, v0.3, and v0.3.1 outputs for every benchmark.

The strongest observed value is from scoped memory and terminology guidance: it improves title/name consistency, technical terminology, and work isolation. The weakest observed value is the v0.3.1 Style Critic loop: the existing Blood Meridian artifact shows the critic found real style problems, but the pass was still approved/bypassed and the revised output is materially unchanged.

The outcome answer is therefore: **TIE is probably useful, but not yet proven by this sprint as a complete measurable translation-quality improvement.** More controlled versioned outputs are required before treating v0.3.1 as outcome-validated.

### Evidence Coverage

| Benchmark | Required Coverage | Available Evidence | Status |
| --- | --- | --- | --- |
| Alice in Wonderland, Chapter 1 | v0.2, v0.3, v0.3.1 outputs | TIE OFF/ON outputs and v0.1/v0.2 reports under `outputs/experiments/alice/` | Partial; not version-separated |
| Blood Meridian, first 10 pages | v0.2, v0.3, v0.3.1 outputs | v0.3 style comparison, v0.3.1 critic comparison, TIE OFF/ON chapter outputs under `outputs/experiments/blood/` | Partial; strongest version evidence, but historical leakage risk |
| Attention Is All You Need, Abstract + Introduction | v0.2, v0.3, v0.3.1 outputs | TIE OFF/ON outputs and v0.1/v0.2 reports under `outputs/experiments/attention/` | Partial; not version-separated |

### Method Note

No new features, agents, or architecture were added. This report audits existing benchmark artifacts and current guardrails. Scores are provided only where the artifacts support a defensible comparison. `N/E` means not enough evidence.

## 2. Alice Results

### Available Artifacts

| Artifact | Path |
| --- | --- |
| TIE OFF output | `outputs/experiments/alice/chapter1/tie_off/translated_tie_off.txt` |
| TIE ON output | `outputs/experiments/alice/chapter1/tie_on/translated_tie_on.txt` |
| TIE ON handoff | `outputs/experiments/alice/chapter1/tie_on/translation_handoff.md` |
| v0.2 memory quality report | `outputs/experiments/tie_v02_memory_quality_report.md` |

### Pairwise Scores

The required v0.2/v0.3/v0.3.1 version outputs are not present for Alice. The existing TIE OFF/ON outputs can show memory influence, but they cannot prove version-to-version improvement.

| Metric | v0.2 vs v0.3 | v0.3 vs v0.3.1 |
| --- | --- | --- |
| Translation Accuracy | N/E | N/E |
| Naturalness | N/E | N/E |
| Terminology Consistency | N/E | N/E |
| Style Preservation | N/E | N/E |
| Voice Consistency | N/E | N/E |
| Readability | N/E | N/E |
| Reader Preference | N/E | N/E |

### Best Translation

No defensible version winner can be selected for Alice because separate v0.2, v0.3, and v0.3.1 outputs are missing.

Among the available TIE OFF/ON artifacts, the TIE ON output improves title normalization (`Alice Harikalar Diyarında`) and some rhetorical phrasing. However, it also introduces less natural literal phrasing in places, such as rendering the heat sentence with `kendini uykulu ve aptal hissediyordu`.

### Worst Translation

No defensible version loser can be selected. The available TIE ON output is not consistently better than TIE OFF; it improves memory consistency but has naturalness regressions.

### Meaningful Differences

| Source Focus | TIE OFF | TIE ON | Commentary |
| --- | --- | --- | --- |
| Title | `Alice'in Harikalar Diyarı Maceraları` | `Alice Harikalar Diyarında` | TIE ON aligns better with the established Turkish title memory. |
| Book rhetorical question | `İçinde resim ya da konuşma olmayan bir kitabın ne faydası var?` | `Resimsiz ve konuşmasız bir kitabın ne anlamı var?` | TIE ON is more idiomatic and compact. |
| Heat/sleepiness sentence | `sıcak bir günün verdiği uyku sersemliğiyle` | `Sıcak bir gün olduğu için kendini uykulu ve aptal hissediyordu.` | TIE OFF reads more natural in Turkish; TIE ON is too literal. |

## 3. Blood Meridian Results

### Available Artifacts

| Artifact | Path |
| --- | --- |
| v0.3 style comparison | `outputs/experiments/blood/style_v03_comparison.md` |
| v0.3.1 style critic comparison | `outputs/experiments/blood/style_critic_comparison.md` |
| TIE OFF output | `outputs/experiments/blood/chapter1/tie_off/translated_tieoff.txt` |
| TIE ON output | `outputs/experiments/blood/chapter1/tie_on/translated_tieon.txt` |
| TIE ON handoff | `outputs/experiments/blood/chapter1/tie_on/translation_handoff.md` |

### Pairwise Scores

The Blood Meridian artifacts provide the clearest historical version evidence. Confidence is reduced because the old v0.3 report contains benchmark-specific style-contract examples that have since been removed from runtime prompts.

| Metric | v0.2 | v0.3 | v0.3.1 | Notes |
| --- | ---: | ---: | ---: | --- |
| Translation Accuracy | 4 | 4 | 4 | No major meaning regression observed in the available excerpt. |
| Naturalness | 3 | 4 | 4 | v0.3 improves literary flow; v0.3.1 does not clearly improve further. |
| Terminology Consistency | 4 | 4 | 4 | Stable, not the decisive factor for this benchmark. |
| Style Preservation | 3 | 4 | 4 | v0.3 better preserves stark fragment rhythm. |
| Voice Consistency | 3 | 4 | 4 | v0.3 moves toward harsher, more archaic register. |
| Readability | 4 | 4 | 4 | Similar readability; style choices matter more than clarity. |
| Reader Preference | 3 | 4 | 4 | v0.3 preferred over v0.2; v0.3.1 not proven superior to v0.3. |

Pairwise result:

| Pair | Winner | Confidence |
| --- | --- | --- |
| v0.2 vs v0.3 | v0.3 | Medium-low, because artifact is narrow and historically leaked |
| v0.3 vs v0.3.1 | Tie / no proven gain | Medium, because critic output shows little actual revision |

### Best Translation

The best supported Blood Meridian version is **v0.3**, not because v0.3.1 is worse, but because the visible improvement arrives with the style contract layer. The v0.3 artifact shows better handling of fragmentary pulse, lexical register, and line-break preservation.

### Worst Translation

The worst supported version is **v0.2** for this benchmark. It is grammatically serviceable, but more normalized and less style-aware.

### Meaningful Differences

| Source Focus | v0.2 | v0.3 | v0.3.1 | Commentary |
| --- | --- | --- | --- | --- |
| `He is pale and thin` | `Solgun ve sıskadır` | `Solgun ve sıska` | Similar to v0.3 output | v0.3 removes the declarative suffix and better preserves fragment rhythm. |
| `schoolmaster` | `okul öğretmeni` | `okul hocası` | Similar style target | v0.3 chooses a more archaic register. |
| Critic loop | N/A | Initial style output | Approved/bypassed with no suggestions applied | v0.3.1 detected issues but did not materially change output. |

### Critical Risk

The historical v0.3 style contract includes benchmark-specific examples. Current runtime prompts have been cleaned, but this artifact should not be treated as a clean held-out result.

## 4. Attention Results

### Available Artifacts

| Artifact | Path |
| --- | --- |
| TIE OFF output | `outputs/experiments/attention/tie_off/translated.txt` |
| TIE ON output | `outputs/experiments/attention/tie_on/translated.txt` |
| TIE ON handoff | `outputs/experiments/attention/tie_on/translation_handoff.md` |
| v0.1 A/B report | `outputs/experiments/tie_ab_test_report.md` |
| v0.2 memory quality report | `outputs/experiments/tie_v02_memory_quality_report.md` |

### Pairwise Scores

The required v0.2/v0.3/v0.3.1 outputs are not present for Attention. Existing reports conflict: the v0.1 A/B report claims a +1.00 TIE gain for Attention, while the v0.2 memory quality report reports 4.70 vs 4.70, delta 0.00.

| Metric | v0.2 vs v0.3 | v0.3 vs v0.3.1 |
| --- | --- | --- |
| Translation Accuracy | N/E | N/E |
| Naturalness | N/E | N/E |
| Terminology Consistency | N/E | N/E |
| Style Preservation | N/E | N/E |
| Voice Consistency | N/E | N/E |
| Readability | N/E | N/E |
| Reader Preference | N/E | N/E |

### Best Translation

No defensible version winner can be selected. The available TIE ON output often reads more direct and active, while TIE OFF is more formal and sometimes smoother for academic Turkish.

### Worst Translation

No defensible version loser can be selected. Both available outputs preserve core technical meaning.

### Meaningful Differences

| Source Focus | TIE OFF | TIE ON | Commentary |
| --- | --- | --- | --- |
| Transformer proposal | `Transformer önerilmektedir` | `Transformer'ı öneriyoruz` | TIE ON is more active and closer to the paper's authorial voice; TIE OFF is more formal. |
| Technical terminology | `dikkat mekanizması`, `yinelenen`, `evrişimli` | Similar terms, with more direct prose | Memory likely helps term consistency, but no version-separated proof exists. |
| BLEU/results sentence | More formal academic register | More direct and concise | Preference depends on target publication style. |

## 5. Memory Value Analysis

| Benchmark | Memories Loaded | Memories Used | Style Contracts Loaded | Provenance IDs | Material Influence |
| --- | --- | --- | --- | --- | --- |
| Alice | Handoff exists with title, character, and phrasing guidance | Visible title and phrase influence | No versioned style contract artifact found | Not present in historical output | Yes for title/phrasing; mixed for naturalness |
| Blood Meridian | Handoff exists; style memory and author mapping are relevant | Visible style influence in v0.3 artifact | Yes in historical v0.3/v0.3.1 artifacts | Not present in historical output | Yes for style, but historical leakage lowers confidence |
| Attention | Handoff exists with technical terminology | Visible terminology consistency | No author style contract expected | Not present in historical output | Likely useful for terminology; quality delta unproven |

Current v0.3.1 code can emit memory provenance IDs from the router, but the historical benchmark outputs were produced before provenance was added. Therefore the sprint cannot attach reliable provenance IDs to the existing benchmark artifacts.

The material memory-value finding is narrow: memory appears most useful for **terminology consistency, work-specific names, and style/phrase reminders**. It is not yet proven to improve whole-document translation quality across versions.

## 6. Style Intelligence Analysis

Style Intelligence is promising but not cleanly validated.

Observed positive signal:

- Blood Meridian v0.3 improves fragment rhythm by avoiding over-normalized Turkish suffixes.
- It makes more register-sensitive lexical choices.
- It preserves layout and authorial rhythm better than the v0.2 excerpt.

Observed risk:

- The strongest v0.3 evidence comes from a historical benchmark artifact that included Blood Meridian-specific examples in the style contract.
- Alice and Attention do not have clean v0.3/v0.3.1 outputs.
- Style Intelligence has not yet shown cross-domain measurable lift in a blinded pairwise setup.

Style Critic specifically is not yet proven useful. The v0.3.1 artifact shows the critic identified concrete style issues, but the feedback loop approved/bypassed the output and applied no substantive revision. Its current observed ROI is low.

## 7. Recommendations

1. Run a controlled versioned benchmark in clean worktrees for the exact commits representing v0.2, v0.3, and v0.3.1.
2. Store outputs under `outputs/evaluation_sprint_v1/{benchmark}/{version}/` with run metadata, prompt hash, model, memory snapshot, and provenance IDs.
3. Treat the current harness as a leakage/provenance guardrail, not a full translation-quality benchmark.
4. Use blinded human pairwise review before claiming quality improvement.
5. Freeze benchmark inputs and memory snapshots before each run.
6. Do not build new agents until the existing TIE, Style Intelligence, and Style Critic components have clean outcome evidence.

## Required Final Verdict

1. **Is TIE useful?** Probably yes, especially for terminology, work-specific memory, and consistency. It is not yet fully proven as a general translation-quality improver.
2. **Is Style Intelligence useful?** Promising for literary style, especially Blood Meridian, but current evidence is not clean enough for a strong claim.
3. **Is Style Critic useful?** Not proven. Existing evidence shows detection without meaningful revision.
4. **Which subsystem produced the highest ROI?** Scoped memory and terminology/handoff context.
5. **Which subsystem produced the lowest ROI?** Style Critic feedback loop in its current observed form.
6. **What should be built next?** Not a new feature: a controlled versioned evaluation run with frozen prompts, memory snapshots, provenance logging, and human pairwise review.
7. **What should NOT be built next?** No new agents, no larger style architecture, no vector-memory expansion, and no further prompt complexity until outcome evidence exists.

## Merge Readiness

This sprint should not be used as evidence that v0.3.1 has won the quality benchmark. It is useful as a merge-prep audit artifact because it identifies what is proven, what is only promising, and what remains unmeasured.
