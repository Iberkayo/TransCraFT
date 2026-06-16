# Strategy Planner Diagnostics Report

## 1. Executive Summary

- Samples evaluated: 3
- Fallback strategies used: 3
- Meaning units generated: 3
- Structural risks detected: 3

This report validates planning, language-profile loading, and prompt guidance only. It does not run a full translation-quality benchmark.

## 2. Sample Source Text

### Alice sample

Source: Alice was beginning to get very tired of sitting by her sister on the bank.

## 3. Generated Translation Strategy

- Text type: literary_fiction
- Tone: literary, attentive to rhythm and atmosphere
- Register: literary
- Literalness level: medium_low
- Sentence reconstruction: Reconstruct sentences for natural Turkish while preserving intentional fragments and rhythm.
- Localization: Localize idioms and phrasing naturally while preserving source meaning.

## 4. Meaning Units

- Alice was beginning to get very tired of sitting by her sister on the bank.

## 5. Turkish Reconstruction Notes

- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- preserve sparse rhythm and intentional fragments when style requires it

## 6. Structural Risks Detected

- Check for Turkish translationese patterns listed in the target profile.

## 7. Translator Instructions

- preserve full meaning before polishing style
- translate by meaning units, not word by word
- avoid translationese and unnecessary pronoun repetition
- produce only the target-language translation
- respect work-specific names, terminology, and style decisions
- preserve narrative tone, imagery, and rhythm

## 8. Critic Checklist

- meaning preserved
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
- Sentence reconstruction: Reconstruct sentences for natural Turkish while preserving intentional fragments and rhythm.
- Localization: Localize idioms and phrasing naturally while preserving source meaning.

## 4. Meaning Units

- The judge watched the fire while the boy stood silent in the doorway.

## 5. Turkish Reconstruction Notes

- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- preserve sparse rhythm and intentional fragments when style requires it

## 6. Structural Risks Detected

- Check for Turkish translationese patterns listed in the target profile.

## 7. Translator Instructions

- preserve full meaning before polishing style
- translate by meaning units, not word by word
- avoid translationese and unnecessary pronoun repetition
- produce only the target-language translation
- respect work-specific names, terminology, and style decisions
- preserve narrative tone, imagery, and rhythm

## 8. Critic Checklist

- meaning preserved
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
- Sentence reconstruction: Prefer clear Turkish academic sentence boundaries; split long English sentences when helpful.
- Localization: Keep technical names stable; localize explanatory phrasing without changing terms.

## 4. Meaning Units

- The model relies on attention mechanisms to draw global dependencies between input and output.

## 5. Turkish Reconstruction Notes

- avoid literal English word order
- drop unnecessary pronouns when Turkish morphology or context is enough
- reconstruct meaning naturally in Turkish before final wording
- prioritize terminology consistency and clear claims

## 6. Structural Risks Detected

- Check for Turkish translationese patterns listed in the target profile.

## 7. Translator Instructions

- preserve full meaning before polishing style
- translate by meaning units, not word by word
- avoid translationese and unnecessary pronoun repetition
- produce only the target-language translation
- respect work-specific names, terminology, and style decisions
- prioritize terminology consistency and technical accuracy

## 8. Critic Checklist

- meaning preserved
- Turkish naturalness
- unnecessary pronouns avoided
- translationese patterns avoided
- long relative clause chains avoided
- register consistency
- terminology consistency

## 9. Before/After Translation Comparison

Not executed in this diagnostics run. The sprint intentionally checks planner output without adding a new translation benchmark path.

## 10. Risks / Limitations

- The planner is deterministic and conservative; it does not prove translation quality by itself.
- Strategy quality still depends on translator and critic adherence.
- Current diagnostics cover English to Turkish profiles only.
