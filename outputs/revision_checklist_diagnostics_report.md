# Revision Checklist Diagnostics Report

## 1. Executive Summary

Samples tested: 3
This is not a human evaluation. Checklist heuristics are not perfect.
Naturalness scoring is approximate. Meaning preservation cannot be fully verified with heuristics.
Human review is still needed.

## business_translationese

### Source

> The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

### Draft Translation

> Eski yazılımın 3. çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor, bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu.

### Generated Checklist

- [CRITICAL] Is the source meaning preserved without omission or addition?
- [CRITICAL] Are there no invented details, explanations, or facts not present in the source?
- [MEDIUM] Are actors, actions, and objects correctly preserved?
- [MEDIUM] Is implied or non-literal meaning preserved appropriately?
- [CRITICAL] Does the Turkish read naturally without translationese?
- [MEDIUM] Is the Turkish word order natural, not copied from English?
- [MEDIUM] Are translationese patterns such as 'neden oldu', 'yol açtı', 'anlamına gelir' avoided?
- [MEDIUM] Are unnecessary pronouns such as o, onun, bu avoided unless needed for emphasis?
- [MEDIUM] Is the register (formal/informal) consistent and appropriate for the genre?
- [MEDIUM] Is the tone preserved without over-formalization or over-modernization?
- [MEDIUM] Are glossary terms used exactly as specified?
- [LOW] Is terminology consistent within the text?

### Checklist Evaluation

Overall score: 4.7/5
Critical failures: 0
Warnings: 1
Passed: 11/12

### Failed / Warning Items

- **no_translationese** [medium]: Translationese detected: neden oldu, merak etmesine neden oldu.

### Recommended Revisions

- Replace translationese patterns with natural Turkish wording.

Expected issues: translationese, long relative clause

## literary_fragment

### Source

> He stood at the door. Silent. Waiting.

### Draft Translation

> Kapıda durdu. Sessizce. Bekleyerek.

### Generated Checklist

- [CRITICAL] Is the source meaning preserved without omission or addition?
- [CRITICAL] Are there no invented details, explanations, or facts not present in the source?
- [MEDIUM] Are actors, actions, and objects correctly preserved?
- [MEDIUM] Is implied or non-literal meaning preserved appropriately?
- [CRITICAL] Does the Turkish read naturally without translationese?
- [MEDIUM] Is the Turkish word order natural, not copied from English?
- [MEDIUM] Are translationese patterns such as 'neden oldu', 'yol açtı', 'anlamına gelir' avoided?
- [MEDIUM] Are unnecessary pronouns such as o, onun, bu avoided unless needed for emphasis?
- [MEDIUM] Is the register (formal/informal) consistent and appropriate for the genre?
- [MEDIUM] Is the tone preserved without over-formalization or over-modernization?
- [MEDIUM] Is character voice preserved where applicable?
- [MEDIUM] Are glossary terms used exactly as specified?
- [LOW] Is terminology consistent within the text?
- [MEDIUM] Is literary rhythm and sentence flow preserved?
- [MEDIUM] Are intentional fragments preserved without over-explaining?
- [MEDIUM] Was over-smoothing of literary voice avoided?

### Checklist Evaluation

Overall score: 5.0/5
Critical failures: 0
Warnings: 0
Passed: 16/16

### Failed / Warning Items

_None._

Expected issues: none

## pronoun_heavy

### Source

> She told him that she would send him the file when she finished reviewing it.

### Draft Translation

> O, ona dosyayı incelemeyi bitirdiğinde onu ona göndereceğini söyledi.

### Generated Checklist

- [CRITICAL] Is the source meaning preserved without omission or addition?
- [CRITICAL] Are there no invented details, explanations, or facts not present in the source?
- [MEDIUM] Are actors, actions, and objects correctly preserved?
- [MEDIUM] Is implied or non-literal meaning preserved appropriately?
- [CRITICAL] Does the Turkish read naturally without translationese?
- [MEDIUM] Is the Turkish word order natural, not copied from English?
- [MEDIUM] Are translationese patterns such as 'neden oldu', 'yol açtı', 'anlamına gelir' avoided?
- [MEDIUM] Are unnecessary pronouns such as o, onun, bu avoided unless needed for emphasis?
- [MEDIUM] Is the register (formal/informal) consistent and appropriate for the genre?
- [MEDIUM] Is the tone preserved without over-formalization or over-modernization?
- [MEDIUM] Are glossary terms used exactly as specified?
- [LOW] Is terminology consistent within the text?

### Checklist Evaluation

Overall score: 4.7/5
Critical failures: 0
Warnings: 1
Passed: 11/12

### Failed / Warning Items

- **unnecessary_pronouns** [medium]: Excessive pronouns: ona.

### Recommended Revisions

- Reduce unnecessary pronoun repetition where Turkish verb marking implies the subject.

Expected issues: pronouns

## Notes on Limitations

- Heuristic evaluation cannot verify meaning preservation or register consistency.
- Translationese detection uses a fixed pattern list; it may miss novel patterns.
- Pronoun counting is approximate; context-dependent pronoun necessity is not modeled.
- Human review remains essential before accepting any checklist-driven revision.
