# Revision Checklist Benchmark

## 1. Executive Summary

- Cases tested: 10
- Improved after revision: 3
- Worsened after revision: 0
- Unchanged: 7
- Base translationese total: 4
- Revised translationese total: 0
- Base pronoun count: 6
- Revised pronoun count: 4
- Base average naturalness: 4.69
- Revised average naturalness: 4.94
- Base average checklist score: 4.88
- Revised average checklist score: 4.97

This is a small synthetic benchmark. Checklist heuristics are not perfect.
Naturalness scoring is approximate. Human review is still needed.

## 2. Case-by-Case Results

| Case | Base T | Rev T | Base P | Rev P | Base Nat | Rev Nat | Base Score | Rev Score | Improved? |
| ---- | -----: | ----: | -----: | ----: | -------: | ------: | ---------: | --------: | --------- |
| business_translationese_001 | 2 | 0 | 1 | 1 | 4.1 | 4.9 | 4.7 | 5.0 | yes |
| noun_stack_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | no |
| passive_voice_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | no |
| pronoun_heavy_001 | 0 | 0 | 3 | 0 | 4.0 | 5.0 | 4.7 | 5.0 | yes |
| idiom_metaphor_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | no |
| literary_fragment_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | no |
| phrasal_verb_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | no |
| business_translationese_002 | 0 | 0 | 0 | 1 | 5.0 | 4.9 | 5.0 | 5.0 | no |
| preposition_heavy_001 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | no |
| clear_split_001 | 2 | 0 | 2 | 2 | 3.8 | 4.6 | 4.4 | 4.7 | yes |

## 3. Case Details

### business_translationese_001

Source: The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

Base: Eski yazılımın 3. çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor, bu karar birçok departmanın günlük operasyonlarının nasıl etkileneceğini merak etmesine neden oldu.

Revised: Eski yazılımın üçüncü çeyrek sonunda aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük işleyişin nasıl etkileneceğine dair soru işaretleri yarattı.

Translationese: 2 -> 0
Pronouns: 1 -> 1
Naturalness: 4.1 -> 4.9
Checklist score: 4.7 -> 5.0
Improved: yes

### noun_stack_001

Source: The customer data privacy compliance monitoring system needs to be updated before the audit.

Base: Müşteri veri gizliliği uyumluluk izleme sisteminin denetimden önce güncellenmesi gerekiyor.

Revised: Müşteri verilerinin gizliliğini denetleyen uyum sisteminin denetimden önce güncellenmesi gerekiyor.

Translationese: 0 -> 0
Pronouns: 0 -> 0
Naturalness: 5.0 -> 5.0
Checklist score: 5.0 -> 5.0
Improved: no

### passive_voice_001

Source: The report was reviewed by the committee and was approved after several minor revisions.

Base: Rapor, komite tarafından incelenmiş ve birkaç küçük düzeltmeden sonra onaylanmıştır.

Revised: Komite raporu inceledi ve birkaç küçük düzeltmenin ardından onayladı.

Translationese: 0 -> 0
Pronouns: 0 -> 0
Naturalness: 5.0 -> 5.0
Checklist score: 5.0 -> 5.0
Improved: no

### pronoun_heavy_001

Source: She told him that she would send him the file when she finished reviewing it.

Base: O, ona dosyayı incelemeyi bitirdiğinde onu ona göndereceğini söyledi.

Revised: Dosyayı inceledikten sonra göndereceğini söyledi.

Translationese: 0 -> 0
Pronouns: 3 -> 0
Naturalness: 4.0 -> 5.0
Checklist score: 4.7 -> 5.0
Improved: yes

### idiom_metaphor_001

Source: The announcement threw cold water on the team's optimism.

Base: Duyuru takımın iyimserliğine soğuk su attı.

Revised: Duyuru, ekibin iyimserliğini kursağında bıraktı.

Translationese: 0 -> 0
Pronouns: 0 -> 0
Naturalness: 5.0 -> 5.0
Checklist score: 5.0 -> 5.0
Improved: no

### literary_fragment_001

Source: Went back to the window. No answer. Only the rain.

Base: Pencereye geri döndü. Cevap yok. Sadece yağmur.

Revised: Pencereye geri döndü. Cevap yok. Sadece yağmur.

Translationese: 0 -> 0
Pronouns: 0 -> 0
Naturalness: 5.0 -> 5.0
Checklist score: 5.0 -> 5.0
Improved: no

### phrasal_verb_001

Source: The support team will follow up with each regional office after the migration is complete.

Base: Destek takımı geçiş tamamlandıktan sonra her bölgesel ofisi takip edecek.

Revised: Destek ekibi, geçiş tamamlandıktan sonra her bölge ofisiyle iletişime geçecek.

Translationese: 0 -> 0
Pronouns: 0 -> 0
Naturalness: 5.0 -> 5.0
Checklist score: 5.0 -> 5.0
Improved: no

### business_translationese_002

Source: Management wants the rollout to be completed quickly, but not at the expense of customer trust.

Base: Yönetim dağıtımın hızlı tamamlanmasını istiyor, ama müşteri güveni pahasına değil.

Revised: Yönetim, kullanıma sunma işleminin hızlı tamamlanmasını istiyor ancak bu süreç müşteri güveninden ödün verilmesine yol açmamalı.

Translationese: 0 -> 0
Pronouns: 0 -> 1
Naturalness: 5.0 -> 4.9
Checklist score: 5.0 -> 5.0
Improved: no

### preposition_heavy_001

Source: The update from the finance team about the delay in the payment process arrived after the meeting.

Base: Finans takımından ödeme sürecindeki gecikme hakkındaki güncelleme toplantıdan sonra geldi.

Revised: Finans ekibinden, ödeme sürecindeki gecikmeyle ilgili güncelleme toplantıdan sonra geldi.

Translationese: 0 -> 0
Pronouns: 0 -> 0
Naturalness: 5.0 -> 5.0
Checklist score: 5.0 -> 5.0
Improved: no

### clear_split_001

Source: The new policy applies to all vendors who process customer records, which means the procurement team must update every active contract this month.

Base: Yeni politika müşteri kayıtlarını işleyen tüm satıcılar için geçerlidir, bu da satın alma ekibinin bu ay tüm aktif sözleşmeleri güncellemesi gerektiği anlamına gelir.

Revised: Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.

Translationese: 2 -> 0
Pronouns: 2 -> 2
Naturalness: 3.8 -> 4.6
Checklist score: 4.4 -> 4.7
Improved: yes

## 4. Notes on Limitations

- All cases are synthetic; no copyrighted text is used.
- Heuristic evaluation cannot verify meaning preservation or register consistency.
- Translationese detection uses a fixed pattern list; it may miss novel patterns.
- Pronoun counting is approximate; context-dependent pronoun necessity is not modeled.
- Human review remains essential before accepting any checklist-driven revision.