# Strategy Planner ON/OFF Benchmark

## 1. Executive Summary

This benchmark compares the real draft translator prompt with Strategy Planner OFF and ON. Scores are lightweight heuristics plus human-readable comparisons; they are not a full human evaluation platform.

- Cases tested: 10
- Strategy ON wins: 1
- Strategy OFF wins: 1
- Ties: 8
- Translation errors: 0

## 2. Overall Result

Keep Strategy Planner, but treat the default-enabled decision as inconclusive.

| Case | Risk Type | Preferred | OFF Naturalness | ON Naturalness | ON Reduced Literalness? | Notes |
| ---- | --------- | --------- | --------------: | -------------: | ----------------------- | ----- |
| business_relative_clause_001 | relative_clause, translationese, sentence_splitting | Tie | 2 | 2 | no | Strategy ON changes wording or structure. |
| noun_stack_001 | noun_stack, terminology, clarity | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| passive_voice_001 | passive_voice, formal_register | Tie | 4 | 4 | no | Strategy ON changes wording or structure. |
| phrasal_verb_001 | phrasal_verb, business_register | Tie | 5 | 5 | no | No visible wording difference. |
| corporate_sentence_001 | corporate_sentence, idiomatic_balance | OFF | 5 | 4 | no | Strategy ON changes wording or structure. |
| academic_abstract_001 | academic_abstract, terminology, naturalness | Tie | 4 | 4 | no | Strategy ON changes wording or structure. |
| literary_fragments_001 | literary_short_sentence, fragment_preservation, rhythm | Tie | 5 | 5 | no | No visible wording difference. |
| idiom_metaphor_001 | idiom, metaphor, literalness | ON | 4 | 5 | yes | Strategy ON changes wording or structure. |
| pronoun_heavy_001 | pronoun_heavy, ambiguity, naturalness | Tie | 5 | 5 | no | Strategy ON is more concise. |
| preposition_heavy_001 | preposition_heavy, noun_stack, sentence_reconstruction | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |

## 3. Case-by-Case Comparisons

### business_relative_clause_001

Risk type: relative_clause, translationese, sentence_splitting

Expected improvement: Strategy ON should split the sentence and avoid literal English clause order.

Source:

> The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

Strategy OFF translation:

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor; bu karar, birçok departmanın günlük operasyonlarının bundan nasıl etkileneceği konusunda kafa karışıklığı yaşamasına neden oldu.

Strategy ON translation:

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor; bu karar, birçok departmanın günlük operasyonlarının nasıl etkileneceği konusunda kafa karışıklığı yaşamasına neden oldu.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### noun_stack_001

Risk type: noun_stack, terminology, clarity

Expected improvement: Strategy ON should unpack the noun stack into clear Turkish.

Source:

> The customer data privacy compliance monitoring system needs to be updated before the audit.

Strategy OFF translation:

> Müşteri veri gizliliği uyumluluk izleme sisteminin denetimden önce güncellenmesi gerekiyor.

Strategy ON translation:

> Müşteri veri gizliliği uyum izleme sisteminin denetimden önce güncellenmesi gerekmektedir.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### passive_voice_001

Risk type: passive_voice, formal_register

Expected improvement: Strategy ON should choose a natural formal Turkish passive or active structure.

Source:

> The report was reviewed by the committee and was approved after several minor revisions.

Strategy OFF translation:

> Rapor, komite tarafından incelendi ve birkaç küçük düzeltmenin ardından onaylandı.

Strategy ON translation:

> Rapor, komite tarafından incelendikten sonra birkaç küçük düzeltmeyle onaylandı.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### phrasal_verb_001

Risk type: phrasal_verb, business_register

Expected improvement: Strategy ON should avoid literal phrasal-verb transfer and use natural corporate Turkish.

Source:

> The support team will follow up with each regional office after the migration is complete.

Strategy OFF translation:

> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bölge ofisiyle iletişime geçecektir.

Strategy ON translation:

> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bölge ofisiyle iletişime geçecektir.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### corporate_sentence_001

Risk type: corporate_sentence, idiomatic_balance

Expected improvement: Strategy ON should preserve the contrast and avoid stiff corporate wording.

Source:

> Management wants the rollout to be completed quickly, but not at the expense of customer trust.

Strategy OFF translation:

> Yönetim, dağıtımın hızlı bir şekilde tamamlanmasını istiyor, ancak müşteri güveni pahasına değil.

Strategy ON translation:

> Yönetim, kullanıma sunma işleminin hızlı bir şekilde tamamlanmasını istiyor, ancak bu müşteri güveni pahasına olmamalı.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? yes
Preferred: OFF

### academic_abstract_001

Risk type: academic_abstract, terminology, naturalness

Expected improvement: Strategy ON should keep the academic claim precise and readable.

Source:

> This study examines how remote collaboration affects decision quality in distributed engineering teams.

Strategy OFF translation:

> Bu çalışma, uzaktan iş birliğinin dağıtık mühendislik ekiplerinde karar kalitesini nasıl etkilediğini incelemektedir.

Strategy ON translation:

> Bu çalışma, dağıtık mühendislik ekiplerinde uzaktan iş birliğinin karar kalitesini nasıl etkilediğini incelemektedir.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### literary_fragments_001

Risk type: literary_short_sentence, fragment_preservation, rhythm

Expected improvement: Strategy ON should preserve fragments and avoid over-explaining.

Source:

> He stood at the door. Silent. Waiting.

Strategy OFF translation:

> Kapıda durdu. Sessiz. Bekleyerek.

Strategy ON translation:

> Kapıda durdu. Sessiz. Bekleyerek.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### idiom_metaphor_001

Risk type: idiom, metaphor, literalness

Expected improvement: Strategy ON should avoid literal wording and preserve the meaning of the idiom.

Source:

> The announcement threw cold water on the team's optimism.

Strategy OFF translation:

> Bu açıklama, takımın iyimserliğini suya düşürdü.

Strategy ON translation:

> Duyuru, takımın iyimserliğini kursağında bıraktı.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? yes
Did ON improve Turkish naturalness? yes
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: ON

### pronoun_heavy_001

Risk type: pronoun_heavy, ambiguity, naturalness

Expected improvement: Strategy ON should reduce unnecessary pronouns without losing reference clarity.

Source:

> She told him that she would send him the file when she finished reviewing it.

Strategy OFF translation:

> Ona dosyayı inceledikten sonra kendisine göndereceğini söyledi.

Strategy ON translation:

> Dosyayı inceledikten sonra ona göndereceğini söyledi.

Visible difference: Strategy ON is more concise.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### preposition_heavy_001

Risk type: preposition_heavy, noun_stack, sentence_reconstruction

Expected improvement: Strategy ON should unpack prepositional phrases into natural Turkish order.

Source:

> The update from the finance team about the delay in the payment process arrived after the meeting.

Strategy OFF translation:

> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

Strategy ON translation:

> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantının ardından geldi.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

## 4. Translationese Pattern Analysis

| Case | OFF Patterns | ON Patterns |
| ---- | ------------ | ----------- |
| business_relative_clause_001 | bu, eden, neden oldu | bu, eden, neden oldu |
| noun_stack_001 | none | none |
| passive_voice_001 | tarafından | tarafından |
| phrasal_verb_001 | none | none |
| corporate_sentence_001 | none | bu |
| academic_abstract_001 | bu | bu |
| literary_fragments_001 | none | none |
| idiom_metaphor_001 | bu | none |
| pronoun_heavy_001 | none | none |
| preposition_heavy_001 | none | none |

## 5. Where Strategy ON Helped

- idiom_metaphor_001

## 6. Where Strategy ON Did Not Help

- business_relative_clause_001
- noun_stack_001
- passive_voice_001
- phrasal_verb_001
- academic_abstract_001
- literary_fragments_001
- pronoun_heavy_001
- preposition_heavy_001

## 7. Where Strategy ON Harmed Output

- corporate_sentence_001

## 8. Recommendations

Keep Strategy Planner, but treat the default-enabled decision as inconclusive.
