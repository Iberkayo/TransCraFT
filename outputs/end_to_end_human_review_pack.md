# End-to-End Human Review Pack

This pack is designed for human review by Berkay or a qualified reviewer.
Heuristic metrics cannot replace human judgment.
For each case, review the outputs and answer the questions.

## business_relative_clause_001

**Genre:** business
**Risk types:** long_relative_clause, business_translationese_risk
**Expected behavior:** Full chain should split naturally and avoid 'neden oldu' style translationese.

### Source:

> The legacy software is expected to be phased out by the end of Q3, a decision which has left many departments wondering how their daily operations will be affected.

### Baseline (translator only):

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması bekleniyor; bu karar, birçok departmanın günlük operasyonlarının bundan nasıl etkileneceğini merak etmesine yol açtı.

### Strategy Only (planner + translator):

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük operasyonların bundan nasıl etkileneceğine dair soru işaretleri yarattı.

### Full Chain (planner + translator + revision + naturalness):

> Eski yazılımın üçüncü çeyreğin sonuna kadar aşamalı olarak kullanımdan kaldırılması planlanıyor. Bu karar, birçok departmanda günlük operasyonların bundan nasıl etkileneceğine dair soru işaretleri yarattı.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## noun_stack_001

**Genre:** business
**Risk types:** noun_stack, clarity
**Expected behavior:** Full chain should unpack the noun stack into clear Turkish.

### Source:

> The customer data privacy compliance monitoring system needs to be updated before the audit.

### Baseline (translator only):

> Müşteri veri gizliliği uyumluluk izleme sisteminin denetimden önce güncellenmesi gerekiyor.

### Strategy Only (planner + translator):

> Müşteri veri gizliliği uyum izleme sisteminin denetimden önce güncellenmesi gerekiyor.

### Full Chain (planner + translator + revision + naturalness):

> Müşteri veri gizliliği uyum izleme sisteminin denetimden önce güncellenmesi gerekiyor.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## passive_double_001

**Genre:** business
**Risk types:** passive_voice, double_passive
**Expected behavior:** Full chain should choose natural formal Turkish passive or active.

### Source:

> The report was reviewed by the committee and was approved after several minor revisions.

### Baseline (translator only):

> Rapor, komite tarafından incelendi ve birkaç küçük düzeltmenin ardından onaylandı.

### Strategy Only (planner + translator):

> Rapor, komite tarafından incelendikten sonra birkaç küçük düzeltmeyle onaylandı.

### Full Chain (planner + translator + revision + naturalness):

> Rapor, komite tarafından incelendikten sonra birkaç küçük düzeltmeyle onaylandı.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## phrasal_verb_001

**Genre:** business
**Risk types:** phrasal_verb, business_register
**Expected behavior:** Full chain should avoid literal phrasal-verb transfer.

### Source:

> The support team will follow up with each regional office after the migration is complete.

### Baseline (translator only):

> Destek ekibi, geçiş tamamlandıktan sonra her bölge ofisiyle iletişime geçecektir.

### Strategy Only (planner + translator):

> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bir bölge ofisiyle iletişime geçecektir.

### Full Chain (planner + translator + revision + naturalness):

> Destek ekibi, geçiş işlemi tamamlandıktan sonra her bir bölge ofisiyle iletişime geçecektir.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## corporate_translationese_001

**Genre:** business
**Risk types:** business_translationese_risk, idiomatic_balance
**Expected behavior:** Full chain should preserve the contrast and avoid stiff corporate wording.

### Source:

> Management wants the rollout to be completed quickly, but not at the expense of customer trust.

### Baseline (translator only):

> Yönetim, dağıtımın hızlı bir şekilde tamamlanmasını istiyor, ancak müşteri güveni pahasına değil.

### Strategy Only (planner + translator):

> Yönetim, kullanıma sunma işleminin hızlı bir şekilde tamamlanmasını istiyor; ancak bu, müşteri güveninden ödün verilmesi anlamına gelmemeli.

### Full Chain (planner + translator + revision + naturalness):

> Yönetim, kullanıma sunma işleminin hızlı  tamamlanmasını istiyor, ancak bu süreç müşteri güveninden ödün verilmesine yol açmamalı.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## academic_abstract_001

**Genre:** academic
**Risk types:** academic_abstract, terminology, naturalness
**Expected behavior:** Full chain should keep academic claim precise and readable.

### Source:

> This study examines how remote collaboration affects decision quality in distributed engineering teams.

### Baseline (translator only):

> Bu çalışma, uzaktan iş birliğinin dağıtık mühendislik ekiplerinde karar kalitesini nasıl etkilediğini incelemektedir.

### Strategy Only (planner + translator):

> Bu çalışma, dağıtık mühendislik ekiplerinde uzaktan iş birliğinin karar kalitesini nasıl etkilediğini incelemektedir.

### Full Chain (planner + translator + revision + naturalness):

> Bu çalışma, dağıtık mühendislik ekiplerinde uzaktan iş birliğinin karar kalitesini nasıl etkilediğini incelemektedir.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## literary_fragments_001

**Genre:** literary
**Risk types:** literary_fragment, fragment_preservation, rhythm
**Expected behavior:** Full chain should preserve fragments and avoid over-explaining.

### Source:

> He stood at the door. Silent. Waiting.

### Baseline (translator only):

> Kapıda durdu. Sessiz. Bekleyerek.

### Strategy Only (planner + translator):

> Kapıda durdu. Sessiz. Bekleyerek.

### Full Chain (planner + translator + revision + naturalness):

> Kapıda durdu. Sessiz. Bekleyerek.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## idiom_metaphor_001

**Genre:** general
**Risk types:** idiom_or_metaphor, literalness
**Expected behavior:** Full chain should use natural Turkish idiom, not literal wording.

### Source:

> The announcement threw cold water on the team's optimism.

### Baseline (translator only):

> Açıklama, takımın iyimserliğini suya düşürdü.

### Strategy Only (planner + translator):

> Duyuru, ekibin iyimserliğini kursağında bıraktı.

### Full Chain (planner + translator + revision + naturalness):

> Duyuru, ekibin iyimserliğini kursağında bıraktı.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## pronoun_heavy_001

**Genre:** general
**Risk types:** pronoun_heavy, ambiguity
**Expected behavior:** Full chain should reduce unnecessary pronouns.

### Source:

> She told him that she would send him the file when she finished reviewing it.

### Baseline (translator only):

> Dosyayı inceledikten sonra ona göndereceğini söyledi.

### Strategy Only (planner + translator):

> Dosyayı inceledikten sonra göndereceğini söyledi.

### Full Chain (planner + translator + revision + naturalness):

> Dosyayı inceledikten sonra göndereceğini söyledi.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## preposition_heavy_001

**Genre:** business
**Risk types:** preposition_heavy, noun_stack
**Expected behavior:** Full chain should unpack prepositional phrases into natural Turkish.

### Source:

> The update from the finance team about the delay in the payment process arrived after the meeting.

### Baseline (translator only):

> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

### Strategy Only (planner + translator):

> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

### Full Chain (planner + translator + revision + naturalness):

> Finans ekibinden ödeme sürecindeki gecikmeyle ilgili güncelleme, toplantıdan sonra geldi.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## nested_relative_clause_001

**Genre:** business
**Risk types:** long_relative_clause, nested_relative_clause
**Expected behavior:** Full chain should split or reorder nested relative clauses.

### Source:

> The vendor that manages the platform which stores regional invoices will be replaced next month.

### Baseline (translator only):

> Gelecek ay, bölgesel faturaları depolayan platformu yöneten satıcı değiştirilecek.

### Strategy Only (planner + translator):

> Bölgesel faturaların saklandığı platformu yöneten satıcı, önümüzdeki ay değiştirilecek.

### Full Chain (planner + translator + revision + naturalness):

> Bölgesel faturaların saklandığı platformu yöneten satıcı, önümüzdeki ay değiştirilecek.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## academic_noun_pile_001

**Genre:** academic
**Risk types:** noun_stack, academic_nominalization
**Expected behavior:** Full chain should unpack the noun pile while preserving academic claim.

### Source:

> The energy market volatility prediction accuracy evaluation framework is tested across three datasets.

### Baseline (translator only):

> Enerji piyasası oynaklık tahmini doğruluk değerlendirme çerçevesi, üç veri seti üzerinde test edilmiştir.

### Strategy Only (planner + translator):

> Enerji piyasası oynaklık tahmin doğruluğu değerlendirme çerçevesi, üç veri kümesi üzerinde test edilmiştir.

### Full Chain (planner + translator + revision + naturalness):

> Enerji piyasası oynaklık tahmin doğruluğu değerlendirme çerçevesi, üç veri kümesi üzerinde test edilmiştir.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## literary_implied_subject_001

**Genre:** literary
**Risk types:** literary_fragment, implied_subject, rhythm
**Expected behavior:** Full chain should preserve implied subject and fragment rhythm.

### Source:

> Went back to the window. No answer. Only the rain.

### Baseline (translator only):

> Pencereye geri döndü. Cevap yok. Sadece yağmur.

### Strategy Only (planner + translator):

> Pencereye geri döndü. Cevap yok. Sadece yağmur.

### Full Chain (planner + translator + revision + naturalness):

> Pencereye geri döndü. Cevap yok. Sadece yağmur.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## metaphor_nonliteral_001

**Genre:** general
**Risk types:** idiom_or_metaphor, literalness
**Expected behavior:** Full chain should avoid literal door imagery if it sounds unnatural.

### Source:

> The failed pilot opened the door to a more careful redesign.

### Baseline (translator only):

> Başarısız pilot uygulaması, daha dikkatli bir yeniden tasarımın önünü açtı.

### Strategy Only (planner + translator):

> Başarısız pilot uygulaması, daha titiz bir yeniden tasarımın önünü açtı.

### Full Chain (planner + translator + revision + naturalness):

> Başarısız pilot uygulaması, daha titiz bir yeniden tasarımın önünü açtı.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## clear_split_required_001

**Genre:** business
**Risk types:** long_relative_clause, business_translationese_risk
**Expected behavior:** Full chain should split the policy scope and required action.

### Source:

> The new policy applies to all vendors who process customer records, which means the procurement team must update every active contract this month.

### Baseline (translator only):

> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir; bu da satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerektiği anlamına gelir.

### Strategy Only (planner + translator):

> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.

### Full Chain (planner + translator + revision + naturalness):

> Yeni politika, müşteri kayıtlarını işleyen tüm tedarikçiler için geçerlidir. Bu nedenle satın alma ekibinin bu ay içinde mevcut tüm aktif sözleşmeleri güncellemesi gerekiyor.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## numbers_dates_001

**Genre:** business
**Risk types:** number_date_preservation
**Expected behavior:** Full chain should preserve numbers and convert date to Turkish format.

### Source:

> On December 25, 2024, the company paid 150,000 TL for the license renewal.

### Baseline (translator only):

> 25 Aralık 2024 tarihinde şirket, lisans yenileme için 150.000 TL ödedi.

### Strategy Only (planner + translator):

> Şirket, 25 Aralık 2024 tarihinde lisans yenileme için 150.000 TL ödedi.

### Full Chain (planner + translator + revision + naturalness):

> Şirket, 25 Aralık 2024 tarihinde lisans yenileme için 150.000 TL ödedi.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## meaning_preservation_trap_001

**Genre:** general
**Risk types:** number_preservation, meaning_preservation
**Expected behavior:** Full chain must NOT swap the percentages or drop one.

### Source:

> The treatment reduced symptoms by 40 percent, but caused fatigue in 20 percent of patients.

### Baseline (translator only):

> Tedavi, semptomları yüzde 40 oranında azalttı ancak hastaların yüzde 20'sinde yorgunluğa neden oldu.

### Strategy Only (planner + translator):

> Tedavi semptomları yüzde 40 oranında azalttı, ancak hastaların yüzde 20'sinde yorgunluğa neden oldu.

### Full Chain (planner + translator + revision + naturalness):

> Tedavi semptomları yüzde 40 oranında azalttı, ancak hastaların yüzde 20'sinde yorgunluğa neden oldu.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## no_rewrite_needed_001

**Genre:** literary
**Risk types:** no_risk, leave_unchanged
**Expected behavior:** Full chain should NOT over-edit this simple literary sentence.

### Source:

> The rain fell softly on the roof.

### Baseline (translator only):

> Yağmur, çatıya hafifçe yağıyordu.

### Strategy Only (planner + translator):

> Yağmur, çatıya usulca düşüyordu.

### Full Chain (planner + translator + revision + naturalness):

> Yağmur, çatıya usulca düşüyordu.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## target_naturalness_opportunity_001

**Genre:** business
**Risk types:** translationese, target_naturalness
**Expected behavior:** Full chain's target naturalness pass should avoid 'merak etmesine neden oldu'.

### Source:

> The delay has left customers wondering how their orders will be affected.

### Baseline (translator only):

> Gecikme, müşterilerin siparişlerinin nasıl etkileneceği konusunda kafa karışıklığı yaşamasına neden oldu.

### Strategy Only (planner + translator):

> Gecikme, müşterilerin siparişlerinin nasıl etkileneceği konusunda soru işaretleri yarattı.

### Full Chain (planner + translator + revision + naturalness):

> Gecikme, müşterilerin siparişlerinin nasıl etkileneceği konusunda soru işaretleri yarattı.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---

## aggressive_rewrite_danger_001

**Genre:** literary
**Risk types:** literary_fragment, over_editing_risk
**Expected behavior:** Full chain should preserve sparse literary fragments; NOT expand or explain them.

### Source:

> Blood. Time. The desert stretched before them like a white page.

### Baseline (translator only):

> Kan. Zaman. Çöl, önlerinde beyaz bir sayfa gibi uzanıyordu.

### Strategy Only (planner + translator):

> Kan. Zaman. Çöl, önlerinde beyaz bir sayfa gibi uzanıyordu.

### Full Chain (planner + translator + revision + naturalness):

> Kan. Zaman. Çöl, önlerinde beyaz bir sayfa gibi uzanıyordu.

### Questions:

1. Which output is most natural Turkish?
2. Which output preserves source meaning best?
3. Which output smells least like translation?
4. Did Full Chain over-edit anything?
5. Preferred: baseline | strategy_only | full_chain | tie
6. Notes:

---
