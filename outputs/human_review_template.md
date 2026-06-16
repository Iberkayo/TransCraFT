# Human Review Template — v0.9.1

Fill this template manually. For each benchmark case, review the three outputs and answer the questions below.

This is not an automatic evaluation. Heuristic metrics are approximate.
Human review is required before quality claims.

## Case 1: business_relative_clause_001

**Genre:** business
**Risk types:** long_relative_clause, business_translationese_risk
**Expected behavior:** Full chain should split naturally and avoid 'neden oldu' style translationese.
**Protected terms:** none

### Source:
> The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

### Baseline Output:
> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor; bu karar, birçok departmanın günlük operasyonlarının bundan nasıl etkileneceğini merak etmesine yol açtı.

### Strategy-Only Output:
> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük operasyonların bundan nasıl etkileneceğine dair soru işaretleri yarattı.

### Full Chain Output:
> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük operasyonların bundan nasıl etkileneceğine dair soru işaretleri yarattı.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 2: noun_stack_001

**Genre:** business
**Risk types:** noun_stack, clarity
**Expected behavior:** Full chain should unpack the noun stack into clear Turkish.
**Protected terms:** none

### Source:
> The customer data privacy compliance monitoring system needs to be updated before the audit.

### Baseline Output:
> Müşteri veri gizliliği uyumluluk izleme sisteminin denetimden önce güncellenmesi gerekiyor.

### Strategy-Only Output:
> Müşteri veri gizliliği uyum izleme sisteminin denetimden önce güncellenmesi gerekiyor.

### Full Chain Output:
> Müşteri veri gizliliği uyum izleme sisteminin denetimden önce güncellenmesi gerekiyor.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 3: passive_double_001

**Genre:** business
**Risk types:** passive_voice, double_passive
**Expected behavior:** Full chain should choose natural formal Turkish passive or active.
**Protected terms:** none

### Source:
> The report was reviewed by the committee and was approved after several minor revisions.

### Baseline Output:
> Rapor, komite tarafından incelendi ve birkaç küçük düzeltmenin ardından onaylandı.

### Strategy-Only Output:
> Rapor, komite tarafından incelendikten sonra birkaç küçük düzeltmeyle onaylandı.

### Full Chain Output:
> Rapor, komite tarafından incelendikten sonra birkaç küçük düzeltmeyle onaylandı.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 4: phrasal_verb_001

**Genre:** business
**Risk types:** phrasal_verb, business_register
**Expected behavior:** Full chain should avoid literal phrasal-verb transfer.
**Protected terms:** none

### Source:
> The support team will follow up with each regional office after the migration is complete.

### Baseline Output:
> Destek ekibi, geçiş tamamlandıktan sonra her bölge ofisiyle iletişime geçecektir.

### Strategy-Only Output:
> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bir bölge ofisiyle iletişime geçecektir.

### Full Chain Output:
> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bir bölge ofisiyle iletişime geçecektir.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 5: corporate_translationese_001

**Genre:** business
**Risk types:** business_translationese_risk, idiomatic_balance
**Expected behavior:** Full chain should preserve the contrast and avoid stiff corporate wording.
**Protected terms:** customer trust

### Source:
> Management wants the rollout to be completed quickly, but not at the expense of customer trust.

### Baseline Output:
> Yönetim, dağıtımın hızlı bir şekilde tamamlanmasını istiyor, ancak müşteri güveni pahasına değil.

### Strategy-Only Output:
> Yönetim, kullanıma sunma işleminin hızlı bir şekilde tamamlanmasını istiyor; ancak bu, müşteri güveninden ödün verilmesi anlamına gelmemeli.

### Full Chain Output:
> Yönetim, kullanıma sunma işleminin hızlı  tamamlanmasını istiyor, ancak bu süreç müşteri güveninden ödün verilmesine yol açmamalı.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 6: academic_abstract_001

**Genre:** academic
**Risk types:** academic_abstract, terminology, naturalness
**Expected behavior:** Full chain should keep academic claim precise and readable.
**Protected terms:** none

### Source:
> This study examines how remote collaboration affects decision quality in distributed engineering teams.

### Baseline Output:
> Bu çalışma, uzaktan iş birliğinin dağıtık mühendislik ekiplerinde karar kalitesini nasıl etkilediğini incelemektedir.

### Strategy-Only Output:
> Bu çalışma, dağıtık mühendislik ekiplerinde uzaktan iş birliğinin karar kalitesini nasıl etkilediğini incelemektedir.

### Full Chain Output:
> Bu çalışma, dağıtık mühendislik ekiplerinde uzaktan iş birliğinin karar kalitesini nasıl etkilediğini incelemektedir.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 7: literary_fragments_001

**Genre:** literary
**Risk types:** literary_fragment, fragment_preservation, rhythm
**Expected behavior:** Full chain should preserve fragments and avoid over-explaining.
**Protected terms:** none

### Source:
> He stood at the door. Silent. Waiting.

### Baseline Output:
> Kapıda durdu. Sessiz. Bekleyerek.

### Strategy-Only Output:
> Kapıda durdu. Sessiz. Bekleyerek.

### Full Chain Output:
> Kapıda durdu. Sessiz. Bekleyerek.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 8: idiom_metaphor_001

**Genre:** general
**Risk types:** idiom_or_metaphor, literalness
**Expected behavior:** Full chain should use natural Turkish idiom, not literal wording.
**Protected terms:** none

### Source:
> The announcement threw cold water on the team's optimism.

### Baseline Output:
> Açıklama, takımın iyimserliğini suya düşürdü.

### Strategy-Only Output:
> Duyuru, ekibin iyimserliğini kursağında bıraktı.

### Full Chain Output:
> Duyuru, ekibin iyimserliğini kursağında bıraktı.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 9: pronoun_heavy_001

**Genre:** general
**Risk types:** pronoun_heavy, ambiguity
**Expected behavior:** Full chain should reduce unnecessary pronouns.
**Protected terms:** none

### Source:
> She told him that she would send him the file when she finished reviewing it.

### Baseline Output:
> Dosyayı inceledikten sonra ona göndereceğini söyledi.

### Strategy-Only Output:
> Dosyayı inceledikten sonra göndereceğini söyledi.

### Full Chain Output:
> Dosyayı inceledikten sonra göndereceğini söyledi.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 10: preposition_heavy_001

**Genre:** business
**Risk types:** preposition_heavy, noun_stack
**Expected behavior:** Full chain should unpack prepositional phrases into natural Turkish.
**Protected terms:** none

### Source:
> The update from the finance team about the delay in the payment process arrived after the meeting.

### Baseline Output:
> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

### Strategy-Only Output:
> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

### Full Chain Output:
> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 11: nested_relative_clause_001

**Genre:** business
**Risk types:** long_relative_clause, nested_relative_clause
**Expected behavior:** Full chain should split or reorder nested relative clauses.
**Protected terms:** none

### Source:
> The vendor that manages the platform which stores regional invoices will be replaced next month.

### Baseline Output:
> Gelecek ay, bölgesel faturaları depolayan platformu yöneten satıcı değiştirilecek.

### Strategy-Only Output:
> Bölgesel faturaların saklandığı platformu yöneten satıcı, önümüzdeki ay değiştirilecek.

### Full Chain Output:
> Bölgesel faturaların saklandığı platformu yöneten satıcı, önümüzdeki ay değiştirilecek.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 12: academic_noun_pile_001

**Genre:** academic
**Risk types:** noun_stack, academic_nominalization
**Expected behavior:** Full chain should unpack the noun pile while preserving academic claim.
**Protected terms:** none

### Source:
> The energy market volatility prediction accuracy evaluation framework is tested across three datasets.

### Baseline Output:
> Enerji piyasası oynaklık tahmini doğruluk değerlendirme çerçevesi, üç veri seti üzerinde test edilmiştir.

### Strategy-Only Output:
> Enerji piyasası oynaklık tahmin doğruluğu değerlendirme çerçevesi, üç veri kümesi üzerinde test edilmiştir.

### Full Chain Output:
> Enerji piyasası oynaklık tahmin doğruluğu değerlendirme çerçevesi, üç veri kümesi üzerinde test edilmiştir.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 13: literary_implied_subject_001

**Genre:** literary
**Risk types:** literary_fragment, implied_subject, rhythm
**Expected behavior:** Full chain should preserve implied subject and fragment rhythm.
**Protected terms:** none

### Source:
> Went back to the window. No answer. Only the rain.

### Baseline Output:
> Pencereye geri döndü. Cevap yok. Sadece yağmur.

### Strategy-Only Output:
> Pencereye geri döndü. Cevap yok. Sadece yağmur.

### Full Chain Output:
> Pencereye geri döndü. Cevap yok. Sadece yağmur.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 14: metaphor_nonliteral_001

**Genre:** general
**Risk types:** idiom_or_metaphor, literalness
**Expected behavior:** Full chain should avoid literal door imagery if it sounds unnatural.
**Protected terms:** none

### Source:
> The failed pilot opened the door to a more careful redesign.

### Baseline Output:
> Başarısız pilot uygulaması, daha dikkatli bir yeniden tasarımın önünü açtı.

### Strategy-Only Output:
> Başarısız pilot uygulaması, daha titiz bir yeniden tasarımın önünü açtı.

### Full Chain Output:
> Başarısız pilot uygulaması, daha titiz bir yeniden tasarımın önünü açtı.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 15: clear_split_required_001

**Genre:** business
**Risk types:** long_relative_clause, business_translationese_risk
**Expected behavior:** Full chain should split the policy scope and required action.
**Protected terms:** none

### Source:
> The new policy applies to all vendors who process customer records, which means the procurement team must update every active contract this month.

### Baseline Output:
> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir; bu da satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerektiği anlamına gelir.

### Strategy-Only Output:
> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.

### Full Chain Output:
> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 16: numbers_dates_001

**Genre:** business
**Risk types:** number_date_preservation
**Expected behavior:** Full chain should preserve numbers and convert date to Turkish format.
**Protected terms:** 150,000 TL, December 25, 2024

### Source:
> On December 25, 2024, the company paid 150,000 TL for the license renewal.

### Baseline Output:
> 25 Aralık 2024 tarihinde şirket, lisans yenileme için 150.000 TL ödedi.

### Strategy-Only Output:
> Şirket, 25 Aralık 2024 tarihinde lisans yenileme için 150.000 TL ödedi.

### Full Chain Output:
> Şirket, 25 Aralık 2024 tarihinde lisans yenileme için 150.000 TL ödedi.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 17: meaning_preservation_trap_001

**Genre:** general
**Risk types:** number_preservation, meaning_preservation
**Expected behavior:** Full chain must NOT swap the percentages or drop one.
**Protected terms:** 40 percent, 20 percent

### Source:
> The treatment reduced symptoms by 40 percent, but caused fatigue in 20 percent of patients.

### Baseline Output:
> Tedavi, semptomları yüzde 40 oranında azalttı ancak hastaların yüzde 20'sinde yorgunluğa neden oldu.

### Strategy-Only Output:
> Tedavi semptomları yüzde 40 oranında azalttı, ancak hastaların yüzde 20'sinde yorgunluğa neden oldu.

### Full Chain Output:
> Tedavi semptomları yüzde 40 oranında azalttı, ancak hastaların yüzde 20'sinde yorgunluğa neden oldu.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 18: no_rewrite_needed_001

**Genre:** literary
**Risk types:** no_risk, leave_unchanged
**Expected behavior:** Full chain should NOT over-edit this simple literary sentence.
**Protected terms:** none

### Source:
> The rain fell softly on the roof.

### Baseline Output:
> Yağmur, çatıya hafifçe yağıyordu.

### Strategy-Only Output:
> Yağmur, çatıya usulca düşüyordu.

### Full Chain Output:
> Yağmur, çatıya usulca düşüyordu.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 19: target_naturalness_opportunity_001

**Genre:** business
**Risk types:** translationese, target_naturalness
**Expected behavior:** Full chain's target naturalness pass should avoid 'merak etmesine neden oldu'.
**Protected terms:** none

### Source:
> The delay has left customers wondering how their orders will be affected.

### Baseline Output:
> Gecikme, müşterilerin siparişlerinin nasıl etkileneceği konusunda kafa karışıklığı yaşamasına neden oldu.

### Strategy-Only Output:
> Gecikme, müşterilerin siparişlerinin nasıl etkileneceği konusunda soru işaretleri yarattı.

### Full Chain Output:
> Gecikme, müşterilerin siparişlerinin nasıl etkileneceği konusunda soru işaretleri yarattı.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---

## Case 20: aggressive_rewrite_danger_001

**Genre:** literary
**Risk types:** literary_fragment, over_editing_risk
**Expected behavior:** Full chain should preserve sparse literary fragments; NOT expand or explain them.
**Protected terms:** none

### Source:
> Blood. Time. The desert stretched before them like a white page.

### Baseline Output:
> Kan. Zaman. Çöl, önlerinde beyaz bir sayfa gibi uzanıyordu.

### Strategy-Only Output:
> Kan. Zaman. Çöl, önlerinde beyaz bir sayfa gibi uzanıyordu.

### Full Chain Output:
> Kan. Zaman. Çöl, önlerinde beyaz bir sayfa gibi uzanıyordu.

### Review Questions:
1. Which output is most natural Turkish? (baseline / strategy_only / full_chain / tie)
2. Which output preserves source meaning best? (baseline / strategy_only / full_chain / tie / cannot_judge)
3. Which output smells least like translation? (baseline / strategy_only / full_chain / tie)
4. Did full_chain over-edit? (yes / no)
5. Did any output lose protected terms, numbers, dates, or terminology? (yes / no)
6. Preferred output: (baseline / strategy_only / full_chain / tie)
7. Error tags: (see allowed list in human_review_schema.json)
8. Severity: (none / minor / major / critical)
9. Notes:

---
