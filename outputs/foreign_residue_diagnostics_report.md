# Foreign Residue Diagnostics

## Summary

Synthetic diagnostics for target-side English residue detection in Turkish output.

## Cases

### critical_phrase

**Input**

```text
All races, all breeds. İnsanlar oradaydı.
```

- Residue count: `4`
- Residues: `[{'text': 'All races, all breeds', 'type': 'english_phrase', 'severity': 'critical', 'recommendation': 'translate or review'}, {'text': 'All races, all breeds.', 'type': 'english_function_word_phrase', 'severity': 'critical', 'recommendation': 'translate sentence fragment or review'}, {'text': 'races', 'type': 'untranslated_english_noun', 'severity': 'review', 'recommendation': 'translate or confirm intentional protected term'}, {'text': 'breeds', 'type': 'untranslated_english_noun', 'severity': 'review', 'recommendation': 'translate or confirm intentional protected term'}]`
- Recommendation: `reject`

### merged_token

**Input**

```text
Hisshoulders dardır.
```

- Residue count: `1`
- Residues: `[{'text': 'Hisshoulders', 'type': 'english_token', 'severity': 'critical', 'recommendation': 'translate or review'}]`
- Recommendation: `reject`

### isolated_nouns

**Input**

```text
Tarlalarda Blacks çalışır; konuşmaları kaba olan Men geçer.
```

- Residue count: `4`
- Residues: `[{'text': 'Men', 'type': 'english_token', 'severity': 'critical', 'recommendation': 'translate or review'}, {'text': 'Blacks', 'type': 'english_token', 'severity': 'critical', 'recommendation': 'translate or review'}, {'text': 'Blacks', 'type': 'untranslated_english_noun', 'severity': 'critical', 'recommendation': 'translate or confirm intentional protected term'}, {'text': 'Men', 'type': 'untranslated_english_noun', 'severity': 'critical', 'recommendation': 'translate or confirm intentional protected term'}]`
- Recommendation: `reject`

### protected_places

**Input**

```text
Memphis'ten Saint Louis'e, oradan New Orleans'a gider.
```

- Residue count: `0`
- Residues: `[]`
- Recommendation: `accept`

## Limitations

- Proper nouns must be passed as protected terms when the workflow knows them.
- The detector is conservative and may mark uncertain English-looking nouns for review.
- It is a QA guardrail, not a translation-quality scorer.
