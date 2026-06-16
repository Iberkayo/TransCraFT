# Target-Only Naturalness Benchmark

## 1. Executive Summary

- Cases: 12
- Improved: 3
- Worsened: 0
- Unchanged: 9
- Translationese before: 6
- Translationese after: 2
- Pronouns before: 5
- Pronouns after: 5
- Avg naturalness before: 4.30
- Avg naturalness after: 4.43
- Accepts: 11
- Reviews: 0
- Rejects: 1

This is a small synthetic benchmark. Deterministic rewrites are limited.
Naturalness scoring is approximate. Target-only pass cannot verify source meaning.
Protected terms and numbers must be preserved. Human review is still needed.

## 2. Case Results

| Case | T Before | T After | P Before | P After | Nat Before | Nat After | Rec |
| ---- | -------: | ------: | -------: | ------: | ---------: | --------: | --- |
| translationese_001 | 2 | 0 | 0 | 0 | 4.2 | 5.0 | accept |
| clean_business | 0 | 0 | 0 | 0 | 5.0 | 5.0 | accept |
| translationese_002 | 2 | 1 | 0 | 0 | 4.2 | 4.6 | accept |
| literary_fragment | 0 | 0 | 0 | 0 | 5.0 | 5.0 | accept |
| with_numbers_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | accept |
| pronoun_heavy | 0 | 0 | 3 | 3 | 4.4 | 4.4 | accept |
| clean_academic | 0 | 0 | 0 | 0 | 5.0 | 5.0 | accept |
| translationese_003 | 2 | 1 | 0 | 0 | 4.2 | 4.6 | accept |
| clean_literary | 0 | 0 | 0 | 0 | 5.0 | 5.0 | accept |
| empty_input | 0 | 0 | 0 | 0 | 0.0 | 0.0 | reject |
| non_turkish | 0 | 0 | 0 | 0 | 5.0 | 5.0 | accept |
| mixed_pronouns | 0 | 0 | 2 | 2 | 4.6 | 4.6 | accept |

## 3. Where It Helped

- **translationese_001**: [{'type': 'translationese_reduction', 'before': 'merak etmesine neden oldu', 'after': 'soru işaretleri yarattı', 'reason': "stiff literal 'wondering caused'"}]
- **translationese_002**: [{'type': 'translationese_reduction', 'before': 'anlamına gelir', 'after': 'demektir', 'reason': "calque of 'which means'"}]
- **translationese_003**: [{'type': 'translationese_reduction', 'before': 'anlamına gelmektedir', 'after': 'demektir', 'reason': "calque of 'which means'"}]

## 4. Where It Refused or Reviewed

- **empty_input**: ['Empty input text']

## 5. Limitations

- All cases are synthetic; no copyrighted text is used.
- Deterministic rewrites are high-confidence only; context may require different wording.
- This pass cannot verify source meaning because it only sees Turkish text.
- Human review is still needed.
