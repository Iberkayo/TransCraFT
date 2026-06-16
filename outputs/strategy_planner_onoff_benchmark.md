# Strategy Planner ON/OFF Benchmark

## 1. Executive Summary

This benchmark compares the real draft translator prompt with Strategy Planner OFF and ON. Scores are lightweight heuristics plus human-readable comparisons; they are not a full human evaluation platform.

- Cases tested: 20
- Strategy ON wins: 2
- Strategy OFF wins: 0
- Ties: 18
- ON harm cases: 0
- Translationese patterns OFF: 7
- Translationese patterns ON: 5
- Average naturalness OFF: 4.65
- Average naturalness ON: 4.80
- Average literalness score OFF: 4.65
- Average literalness score ON: 4.80
- Average meaning preservation OFF: 4.00
- Average meaning preservation ON: 4.00
- Strategy Planner Impact: Inconclusive
- Translation errors: 0

This remains a small synthetic benchmark. Human review is still needed; ON wins do not automatically prove production quality. Ties mean the planner may still be insufficiently influential, and harm cases must be inspected manually.

## 2. Overall Result

Keep Strategy Planner, but treat the default-enabled decision as inconclusive.

| Case | Risk Type | Preferred | OFF Naturalness | ON Naturalness | ON Reduced Literalness? | Notes |
| ---- | --------- | --------- | --------------: | -------------: | ----------------------- | ----- |
| business_relative_clause_001 | long_relative_clause, business_translationese_risk, sentence_splitting | ON | 4 | 5 | yes | Strategy ON uses more sentence splitting. |
| noun_stack_001 | noun_stack, terminology, clarity | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| passive_voice_001 | passive_voice, double_passive, formal_register | Tie | 4 | 4 | no | Strategy ON changes wording or structure. |
| phrasal_verb_001 | phrasal_verb, business_register | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| corporate_sentence_001 | corporate_sentence, idiomatic_balance, business_translationese_risk | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| academic_abstract_001 | academic_abstract, terminology, naturalness | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| literary_fragments_001 | literary_fragment, fragment_preservation, rhythm | Tie | 5 | 5 | no | No visible wording difference. |
| idiom_metaphor_001 | idiom_or_metaphor, literalness | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| pronoun_heavy_001 | pronoun_heavy, ambiguity, naturalness | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| preposition_heavy_001 | preposition_heavy, noun_stack, sentence_reconstruction | Tie | 5 | 5 | no | No visible wording difference. |
| nested_relative_clause_001 | long_relative_clause, nested_relative_clause, sentence_splitting | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| double_passive_001 | passive_voice, double_passive | Tie | 4 | 4 | no | Strategy ON changes wording or structure. |
| legal_nominalization_001 | academic_nominalization, legal_business_nominalization, noun_stack | Tie | 5 | 5 | no | No visible wording difference. |
| academic_noun_pile_001 | noun_stack, academic_nominalization, technical_clarity | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| literary_implied_subject_001 | literary_fragment, implied_subject, rhythm | Tie | 5 | 5 | no | No visible wording difference. |
| metaphor_nonliteral_001 | idiom_or_metaphor, literalness | Tie | 5 | 5 | no | Strategy ON changes wording or structure. |
| phrasal_nonliteral_001 | phrasal_verb, nonliteral_meaning, business_register | Tie | 5 | 5 | no | No visible wording difference. |
| long_multiclause_001 | long_sentence, multiple_clauses, sentence_splitting | Tie | 4 | 4 | no | No visible wording difference. |
| pronoun_ambiguity_001 | pronoun_heavy, pronoun_ambiguity | Tie | 4 | 4 | no | Strategy ON changes wording or structure. |
| clear_split_required_001 | long_relative_clause, sentence_splitting, business_translationese_risk | ON | 3 | 5 | yes | Strategy ON uses more sentence splitting. |

## 3. Case-by-Case Comparisons

### business_relative_clause_001

Risk type: long_relative_clause, business_translationese_risk, sentence_splitting

Expected improvement: Strategy ON should split the sentence and avoid literal English clause order.

Source:

> The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

Strategy OFF translation:

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor; bu karar, birçok departmanın günlük operasyonlarının bundan nasıl etkileneceğini merak etmesine yol açtı.

Strategy ON translation:

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük operasyonların bundan nasıl etkileneceğine dair soru işaretleri yarattı.

Visible difference: Strategy ON uses more sentence splitting.
Did ON reduce translationese? yes
Did ON improve Turkish naturalness? yes
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: ON

### noun_stack_001

Risk type: noun_stack, terminology, clarity

Expected improvement: Strategy ON should unpack the noun stack into clear Turkish.

Source:

> The customer data privacy compliance monitoring system needs to be updated before the audit.

Strategy OFF translation:

> Müşteri veri gizliliği uyumluluk izleme sisteminin denetimden önce güncellenmesi gerekiyor.

Strategy ON translation:

> Müşteri veri gizliliği uyum izleme sisteminin denetimden önce güncellenmesi gerekiyor.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### passive_voice_001

Risk type: passive_voice, double_passive, formal_register

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

> Destek ekibi, geçiş tamamlandıktan sonra her bölge ofisiyle iletişime geçecektir.

Strategy ON translation:

> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bir bölge ofisiyle iletişime geçecektir.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### corporate_sentence_001

Risk type: corporate_sentence, idiomatic_balance, business_translationese_risk

Expected improvement: Strategy ON should preserve the contrast and avoid stiff corporate wording.

Source:

> Management wants the rollout to be completed quickly, but not at the expense of customer trust.

Strategy OFF translation:

> Yönetim, dağıtımın hızlı bir şekilde tamamlanmasını istiyor, ancak müşteri güveni pahasına değil.

Strategy ON translation:

> Yönetim, kullanıma sunma işleminin hızlı bir şekilde tamamlanmasını istiyor, ancak bu süreç müşteri güveninden ödün verilmesine yol açmamalı.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

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

Risk type: literary_fragment, fragment_preservation, rhythm

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

Risk type: idiom_or_metaphor, literalness

Expected improvement: Strategy ON should avoid literal wording and preserve the meaning of the idiom.

Source:

> The announcement threw cold water on the team's optimism.

Strategy OFF translation:

> Açıklama, takımın iyimserliğini suya düşürdü.

Strategy ON translation:

> Duyuru, ekibin iyimserliğini kursağında bıraktı.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### pronoun_heavy_001

Risk type: pronoun_heavy, ambiguity, naturalness

Expected improvement: Strategy ON should reduce unnecessary pronouns without losing reference clarity.

Source:

> She told him that she would send him the file when she finished reviewing it.

Strategy OFF translation:

> Dosyayı inceledikten sonra ona göndereceğini söyledi.

Strategy ON translation:

> Dosyayı inceledikten sonra göndereceğini söyledi.

Visible difference: Strategy ON changes wording or structure.
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

> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### nested_relative_clause_001

Risk type: long_relative_clause, nested_relative_clause, sentence_splitting

Expected improvement: Strategy ON should split or reorder nested relative clauses into readable Turkish.

Source:

> The vendor that manages the platform which stores regional invoices will be replaced next month.

Strategy OFF translation:

> Gelecek ay, bölgesel faturaları depolayan platformu yöneten satıcı değiştirilecek.

Strategy ON translation:

> Bölgesel faturaların saklandığı platformu yöneten satıcı, önümüzdeki ay değiştirilecek.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### double_passive_001

Risk type: passive_voice, double_passive

Expected improvement: Strategy ON should avoid unnecessary passive stacking.

Source:

> The request was submitted by the branch office and was later rejected by the compliance unit.

Strategy OFF translation:

> Talep, şube ofisi tarafından iletilmiş ve daha sonra uyum birimi tarafından reddedilmiştir.

Strategy ON translation:

> Talep, şube tarafından iletilmiş ancak daha sonra uyum birimi tarafından reddedilmiştir.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### legal_nominalization_001

Risk type: academic_nominalization, legal_business_nominalization, noun_stack

Expected improvement: Strategy ON should convert dense nominalizations into clear Turkish legal-business prose.

Source:

> The implementation of the termination provision requires notification of all affected contractors.

Strategy OFF translation:

> Fesih hükmünün uygulanması, etkilenen tüm yüklenicilere bildirim yapılmasını gerektirir.

Strategy ON translation:

> Fesih hükmünün uygulanması, etkilenen tüm yüklenicilere bildirim yapılmasını gerektirir.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### academic_noun_pile_001

Risk type: noun_stack, academic_nominalization, technical_clarity

Expected improvement: Strategy ON should unpack the noun pile and preserve the academic claim.

Source:

> The energy market volatility prediction accuracy evaluation framework is tested across three datasets.

Strategy OFF translation:

> Enerji piyasası oynaklık tahmini doğruluk değerlendirme çerçevesi, üç veri seti üzerinde test edilmiştir.

Strategy ON translation:

> Enerji piyasası oynaklık tahmin doğruluğu değerlendirme çerçevesi, üç veri kümesi üzerinde test edilmiştir.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### literary_implied_subject_001

Risk type: literary_fragment, implied_subject, rhythm

Expected improvement: Strategy ON should preserve implied subject and fragment rhythm.

Source:

> Went back to the window. No answer. Only the rain.

Strategy OFF translation:

> Pencereye geri döndü. Cevap yok. Sadece yağmur.

Strategy ON translation:

> Pencereye geri döndü. Cevap yok. Sadece yağmur.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### metaphor_nonliteral_001

Risk type: idiom_or_metaphor, literalness

Expected improvement: Strategy ON should avoid literal door imagery if it sounds unnatural.

Source:

> The failed pilot opened the door to a more careful redesign.

Strategy OFF translation:

> Başarısız pilot uygulaması, daha dikkatli bir yeniden tasarımın yolunu açtı.

Strategy ON translation:

> Başarısız pilot uygulaması, daha titiz bir yeniden tasarımın önünü açtı.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### phrasal_nonliteral_001

Risk type: phrasal_verb, nonliteral_meaning, business_register

Expected improvement: Strategy ON should translate phrasal verbs by meaning, not particles.

Source:

> The board turned down the proposal because the cost assumptions did not hold up.

Strategy OFF translation:

> Yönetim kurulu, maliyet varsayımları geçerliliğini korumadığı için teklifi reddetti.

Strategy ON translation:

> Yönetim kurulu, maliyet varsayımları geçerliliğini korumadığı için teklifi reddetti.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### long_multiclause_001

Risk type: long_sentence, multiple_clauses, sentence_splitting

Expected improvement: Strategy ON should split the sentence where Turkish readability improves.

Source:

> The team delayed the release because the billing service failed during testing, but the client still expects the launch to happen before Friday.

Strategy OFF translation:

> Ekip, test sırasında faturalandırma hizmetinin başarısız olması nedeniyle sürümü erteledi, ancak müşteri hâlâ lansmanın Cuma gününden önce gerçekleşmesini bekliyor.

Strategy ON translation:

> Ekip, test sırasında faturalandırma hizmetinin başarısız olması nedeniyle sürümü erteledi, ancak müşteri hâlâ lansmanın Cuma gününden önce gerçekleşmesini bekliyor.

Visible difference: No visible wording difference.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### pronoun_ambiguity_001

Risk type: pronoun_heavy, pronoun_ambiguity

Expected improvement: Strategy ON should avoid unnecessary pronouns while preserving who did what.

Source:

> When Mira called Deniz, she said her manager wanted her to revise the plan before she sent it.

Strategy OFF translation:

> Mira, Deniz'i aradığında, yöneticisinin planı göndermeden önce revize etmesini istediğini söyledi.

Strategy ON translation:

> Mira, Deniz'i aradığında, müdürünün planı göndermeden önce revize etmesini istediğini söyledi.

Visible difference: Strategy ON changes wording or structure.
Did ON reduce translationese? no
Did ON improve Turkish naturalness? no
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: Tie

### clear_split_required_001

Risk type: long_relative_clause, sentence_splitting, business_translationese_risk

Expected improvement: Strategy ON should clearly split the policy scope and the required action.

Source:

> The new policy applies to all vendors who process customer records, which means the procurement team must update every active contract this month.

Strategy OFF translation:

> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir; bu da satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerektiği anlamına gelir.

Strategy ON translation:

> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.

Visible difference: Strategy ON uses more sentence splitting.
Did ON reduce translationese? yes
Did ON improve Turkish naturalness? yes
Did ON preserve meaning? heuristic score 4/5
Did ON over-edit or harm anything? no
Preferred: ON

## 4. Translationese Pattern Analysis

| Case | OFF Patterns | ON Patterns |
| ---- | ------------ | ----------- |
| business_relative_clause_001 | merak etmesine yol açtı | none |
| noun_stack_001 | none | none |
| passive_voice_001 | tarafından | tarafından |
| phrasal_verb_001 | none | none |
| corporate_sentence_001 | none | none |
| academic_abstract_001 | none | none |
| literary_fragments_001 | none | none |
| idiom_metaphor_001 | none | none |
| pronoun_heavy_001 | none | none |
| preposition_heavy_001 | none | none |
| nested_relative_clause_001 | none | none |
| double_passive_001 | tarafından | tarafından |
| legal_nominalization_001 | none | none |
| academic_noun_pile_001 | none | none |
| literary_implied_subject_001 | none | none |
| metaphor_nonliteral_001 | none | none |
| phrasal_nonliteral_001 | none | none |
| long_multiclause_001 | eden | eden |
| pronoun_ambiguity_001 | eden | eden |
| clear_split_required_001 | anlamına gelir, bu da | eden |

Summary:

- OFF pattern count: 7
- ON pattern count: 5

## 5. Where Strategy ON Helped

- business_relative_clause_001
- clear_split_required_001

## 6. Where Strategy ON Did Not Help

- noun_stack_001
- passive_voice_001
- phrasal_verb_001
- corporate_sentence_001
- academic_abstract_001
- literary_fragments_001
- idiom_metaphor_001
- pronoun_heavy_001
- preposition_heavy_001
- nested_relative_clause_001
- double_passive_001
- legal_nominalization_001
- academic_noun_pile_001
- literary_implied_subject_001
- metaphor_nonliteral_001
- phrasal_nonliteral_001
- long_multiclause_001
- pronoun_ambiguity_001

## 7. Where Strategy ON Harmed Output

_None._

## 8. Recommendations

Keep Strategy Planner, but treat the default-enabled decision as inconclusive.
