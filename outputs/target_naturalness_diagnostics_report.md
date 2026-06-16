# Target-Only Naturalness Diagnostics Report

## 1. Executive Summary

Samples: 3
This is not a human evaluation. Deterministic rewrites are limited.
Naturalness scoring is approximate. Target-only pass cannot verify source meaning.
Protected terms and numbers must be preserved. Human review is still needed.

## business_translationese

### Input Turkish Text

> Bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu.

**Translationese before:** 2
**Translationese after:** 0
**Pronouns before:** 0
**Pronouns after:** 0
**Naturalness before:** 4.2
**Naturalness after:** 5.0

### Changes Made

- `merak etmesine neden oldu` → `soru işaretleri yarattı` (stiff literal 'wondering caused')

### Revised Text

> Bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini soru işaretleri yarattı.

**Recommendation:** accept
**Safe to apply:** True
**Verdict:** apply

## literary_fragment

### Input Turkish Text

> Kapıda durdu. Sessiz. Bekleyerek.

**Translationese before:** 0
**Translationese after:** 0
**Pronouns before:** 0
**Pronouns after:** 0
**Naturalness before:** 5.0
**Naturalness after:** 5.0

### Revised Text

> Kapıda durdu. Sessiz. Bekleyerek.

**Recommendation:** accept
**Safe to apply:** True
**Verdict:** apply

## with_numbers

### Input Turkish Text

> 25 Aralık 2024 tarihinde 150 TL ödeme yapıldı.

**Translationese before:** 0
**Translationese after:** 0
**Pronouns before:** 0
**Pronouns after:** 0
**Naturalness before:** 5.0
**Naturalness after:** 5.0

### Revised Text

> 25 Aralık 2024 tarihinde 150 TL ödeme yapıldı.

**Recommendation:** accept
**Safe to apply:** True
**Verdict:** apply

## Limitations

- Deterministic rewrites are high-confidence only; context may still require different wording.
- Naturalness scoring uses fixed heuristics; it cannot detect all translationese.
- This pass cannot verify source meaning because it only sees Turkish text.
- Protected terms and numbers must be provided or auto-extracted; extraction is regex-based.
