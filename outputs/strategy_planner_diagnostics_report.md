# Strategy Planner Diagnostics Report

## 1. Executive Summary

- Samples evaluated: 3
- Fallback strategies used: 3
- Meaning units generated: 3
- Structural risks detected: 3

This report validates planning, language-profile loading, and prompt guidance only. It does not run a full translation-quality benchmark.

Fallback strategy was used for all current samples. Quality improvement is not proven here; the next evidence step is a small Strategy ON/OFF translation output comparison.

## 2. Sample Source Text

### Alice sample

Source: Alice was beginning to get very tired of sitting by her sister on the bank.

## 3. Generated Translation Strategy

- Text type: literary_fiction
- Tone: literary, attentive to rhythm and atmosphere
- Register: literary
- Literalness level: medium_low
- Sentence reconstruction: Reconstruct sentences for natural target-language flow while preserving intentional fragments and rhythm.
- Localization: Localize idioms and phrasing naturally while preserving source meaning.

## 4. Meaning Units

- Alice was beginning to get very tired of sitting by her sister on the bank.

## 5. Target-Language Reconstruction Notes

- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- preserve sparse rhythm and intentional fragments when style requires it

## 6. Structural Risks Detected

- translationese_risk: Alice was beginning to get very tired of sitting by her sister on the bank. | strategy: Check target-profile anti-translationese rules before final wording.

## 7. Translator Instructions

- treat strategy notes as constraints unless they harm source meaning
- preserve full meaning before polishing style
- translate by meaning units, not word by word
- avoid translationese and unnecessary repetition
- produce only the target-language translation
- respect work-specific names, terminology, and style decisions
- preserve narrative tone, imagery, and rhythm

## 8. Critic Checklist

- Turkish naturalness
- unnecessary pronouns avoided
- translationese patterns avoided
- long relative clause chains avoided
- register consistency
- terminology consistency
- style and rhythm preservation

## 9. Before/After Translation Comparison

Not executed in this diagnostics run. The sprint intentionally checks planner output without adding a new translation benchmark path.

### Frontier literary sample

Source: The judge watched the fire while the boy stood silent in the doorway.

## 3. Generated Translation Strategy

- Text type: literary_fiction
- Tone: literary, attentive to rhythm and atmosphere
- Register: literary
- Literalness level: medium_low
- Sentence reconstruction: Reconstruct sentences for natural target-language flow while preserving intentional fragments and rhythm.
- Localization: Localize idioms and phrasing naturally while preserving source meaning.

## 4. Meaning Units

- The judge watched the fire while the boy stood silent in the doorway.

## 5. Target-Language Reconstruction Notes

- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- preserve sparse rhythm and intentional fragments when style requires it

## 6. Structural Risks Detected

- translationese_risk: The judge watched the fire while the boy stood silent in the doorway. | strategy: Check target-profile anti-translationese rules before final wording.

## 7. Translator Instructions

- treat strategy notes as constraints unless they harm source meaning
- preserve full meaning before polishing style
- translate by meaning units, not word by word
- avoid translationese and unnecessary repetition
- produce only the target-language translation
- respect work-specific names, terminology, and style decisions
- preserve narrative tone, imagery, and rhythm

## 8. Critic Checklist

- Turkish naturalness
- unnecessary pronouns avoided
- translationese patterns avoided
- long relative clause chains avoided
- register consistency
- terminology consistency
- style and rhythm preservation

## 9. Before/After Translation Comparison

Not executed in this diagnostics run. The sprint intentionally checks planner output without adding a new translation benchmark path.

### Attention sample

Source: The model relies on attention mechanisms to draw global dependencies between input and output.

## 3. Generated Translation Strategy

- Text type: technical
- Tone: clear, precise, controlled
- Register: formal technical
- Literalness level: medium
- Sentence reconstruction: Prefer clear target-language sentence boundaries; split long source sentences when helpful.
- Localization: Keep technical names stable; localize explanatory phrasing without changing terms.

## 4. Meaning Units

- The model relies on attention mechanisms to draw global dependencies between input and output.

## 5. Target-Language Reconstruction Notes

- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- prioritize terminology consistency and clear claims
- Unpack the English noun stack into a clear Turkish possessive or explanatory phrase.

## 6. Structural Risks Detected

- noun_stack: draw global dependencies between input | strategy: Unpack the stack into a clear possessive or explanatory Turkish phrase.

## 7. Translator Instructions

- treat strategy notes as constraints unless they harm source meaning
- preserve full meaning before polishing style
- translate by meaning units, not word by word
- avoid translationese and unnecessary repetition
- produce only the target-language translation
- respect work-specific names, terminology, and style decisions
- prioritize terminology consistency and technical accuracy
- For noun_stack: Unpack the stack into a clear possessive or explanatory Turkish phrase.

## 8. Critic Checklist

- Turkish naturalness
- unnecessary pronouns avoided
- translationese patterns avoided
- long relative clause chains avoided
- register consistency
- terminology consistency
- Did the output unpack the noun stack into readable Turkish?

## 9. Before/After Translation Comparison

Not executed in this diagnostics run. The sprint intentionally checks planner output without adding a new translation benchmark path.

## 10. Strategy ON/OFF Prompt Smoke Test

Source: The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

Strategy Planner OFF context:

_None._

Strategy Planner ON context excerpt:

```text
### Translation Strategy Plan
- Source language: en_US
- Target language: tr_TR
- Text type: business
- Tone: natural and fluent
- Register: formal business
- Literalness level: medium_low
- Sentence reconstruction: Prefer natural target-language rhythm over literal source syntax.
- Localization: Localize idioms and phrasing naturally while preserving source meaning.

Meaning units:
- The legacy software is expected to be phased out by the end of Q3
- a decision which has left many departments wondering how their daily operations will be affected.

Structural risks:
- long_sentence: The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected. | risk: A long source sentence may become heavy or unclear in Turkish. | strategy: Split into natural Turkish sentence units when readability improves.
- long_relative_clause: , a decision which has left many departments wondering how their daily operations will be affected | risk: Literal English clause order may create unnatural Turkish. | strategy: Split into two Turkish sentences and reconstruct causality naturally.
- noun_stack: decision which has left many departments wondering | risk: Stacked English modifiers may become an opaque Turkish noun chain. | strategy: Unpack the stack into a clear possessive or explanatory Turkish phrase.
- passive_voice: is expected | risk: Mechanical passive transfer may sound stiff or obscure agency. | strategy: Decide whether Turkish should keep passive voice or use a natural active structure.
- double_passive: The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected. | risk: Multiple passive verbs can make Turkish bureaucratic and heavy. | strategy: Reduce passive stacking where meaning allows.
- business_translationese_risk: has left | risk: Literal business phrasing may lead to stiff Turkish such as 'neden oldu'. | strategy: Use natural corporate Turkish such as 'soru isaretleri yaratti' or 'endise yaratti' when meaning fits.

Target-language reconstruction notes:
- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- Split long sentences when Turkish readability improves.
- Use two Turkish sentences when the relative clause becomes heavy.
```

Observed difference: Strategy ON adds meaning units, target profile rules, reconstruction notes, and structural risks. This is prompt-level evidence only; no real translation output was generated.

Reduced literalness: Not proven by this diagnostics run.

## 11. Risks / Limitations

- The planner is deterministic and conservative; it does not prove translation quality by itself.
- Strategy quality still depends on translator and critic adherence.
- Current diagnostics cover English to Turkish profiles only.
- Prompt-level ON/OFF evidence is not a substitute for human review of actual translation outputs.
