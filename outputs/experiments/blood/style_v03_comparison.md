# TIE v0.3 MVP Style Intelligence Benchmark - Blood Meridian

This experiment compares the literary quality of Cormac McCarthy's opening paragraph in *Blood Meridian* (Chunk 2 of the PDF) under TIE v0.2 (Terminology only) vs TIE v0.3 MVP (Style Intelligence Layer).

## 1. Style Contract Used (TIE v0.3)
```json
{
  "tone": "bleak, severe, epic, emotionally detached",
  "sentence_rhythm": "biblical, paratactic, coordinate clauses mixed with stark fragmentary pulses",
  "rules": [
    "Preserve sentence fragments and coordinate clauses as separate sentence pulses in Turkish. Do not combine them using relative clauses or run-on sentences.",
    "Avoid adding explanatory Turkish conjunctions (e.g. 'çünkü', 'fakat', 'ise') to bridge coordinate structures linked by 'and'. Keep the conjunctions literal or use simple semicolons.",
    "Prefer scenic presentation and direct theatrical/scenic verbs (e.g. translating 'See the child.' as 'Çocuğa bakın.', 'Karşınızda çocuk.', or 'Bakın çocuk.') over plain literal cognitive statements ('Çocuğu görün.').",
    "Maintain a bleak, stark, and sparse atmospheric narration rhythm. Use solemn and archaic Turkish lexical equivalents where appropriate."
  ]
}
```

---

## 2. Text Comparison (Opening Paragraph / Chunk 2)

### Source English Text
> See the child. He is pale and thin, he wears a thin and ragged linen shirt. He stokes the scullery fire. Outside lie dark turned fields with rags of snow and darker woods beyond that harbor yet a few last wolves. His folk are known for hewers of wood and drawers of water but in truth his father has been a schoolmaster. He lies in drink, he quotes from poets whose names are now lost. The boy crouches by the fire and watches him.

### TIE v0.2 Translation (Terminology only)
```text
Çocuğa bakın. Solgun ve sıskadır, ince ve yırtık pırtık bir keten gömlek giyer. Bulaşık ocağını körükler. Dışarıda kara sürülmüş tarlalar uzanır, üzerlerinde paçavralar halinde kar ve ötesinde birkaç son kurda daha yuva olan daha koyu ormanlar. Onun halkı odun kesenler ve su taşıyanlar olarak bilinir ama gerçekte babası bir okul öğretmeni olmuştur. İçkiye yatmış, adları artık kayıp şairlerden alıntı yapar. Çocuk ateşin yanına çömelir ve onu izler.
```

### TIE v0.3 MVP Translation (Style Intelligence Layer)
```text
Çocuğa bakın. Solgun ve sıska, ince ve yırtık bir keten gömlek giyer. Bulaşık ocağını besler. Dışarıda karanlık sürülmüş tarlalar, üzerlerinde paçavra kar kalıntıları ve ötesinde birkaç son kurda daha yuva olan daha koyu ormanlar uzanır. Onun halkı odun kesenler ve su taşıyanlar olarak bilinir ama gerçekte babası bir okul hocası olmuştur. İçkide yatar, adları artık kayıp şairlerden alıntı yapar. Oğlan ateşin yanına çömelir ve onu izler.
```

---

## 3. Key Sentences Focus

| English Source | TIE v0.2 Translation | TIE v0.3 MVP Translation | Improvement Observations |
| --- | --- | --- | --- |
| **"See the child."** | `"Çocuğa bakın."` | `"Çocuğa bakın."` | Both correctly avoided `"Çocuğu görün"`, but TIE v0.3 achieves this systematically via the contract directive. |
| **"He is pale and thin..."** | `"Solgun ve sıskadır..."` | `"Solgun ve sıska..."` | **TIE v0.3** successfully stripped the declarative `-dir` suffix, preserving the raw fragment/adjectival pulse style of McCarthy. |
| **"Outside lie dark turned fields..."** | `"Dışarıda kara sürülmüş tarlalar uzanır..."` | `"Dışarıda karanlık sürülmüş tarlalar..."` | **TIE v0.3** uses `"karanlık sürülmüş"` instead of `"kara sürülmüş"`, yielding a bleaker, more gothic word choice. |
| **"...but in truth his father has been a schoolmaster."** | `"...babası bir okul öğretmeni olmuştur."` | `"...babası bir okul hocası olmuştur."` | **TIE v0.3** opts for `"hoca"` (archaic register) rather than `"öğretmen"`, matching the solemn/archaic register constraint. |
| **Chapter Headers Formatting** | Combined on a single line with dashes: `... Toadvine – Otel Yangını – Kaçış.` | Preserved McCarthy's line breaks: `... Toadvine - \n Otel Yangını - Kaçış.` | **TIE v0.3** correctly preserved the paratextual line breaks. |

---

## 4. Discussion & Recommendation

### Did style intelligence improve literary quality?
**Yes.** TIE v0.2 outputs a grammatically correct translation but introduces standard narrative suffixes (like `-dir` in `sıskadır`) and modern, plain register terminology (like `öğretmen`). 

TIE v0.3 strictly adheres to the Style Contract:
1.  **Syntactic Purity:** Omission of `-dir` keeps sentences as stark, adjectival fragments.
2.  **Lexical Register:** Using `hoca` and `besler` evokes a more solemn, archaic frontier register.
3.  **Layout Preservation:** Line breaks in headers are preserved instead of being collapsed into a run-on line.

### Recommendation
Deploy the TIE v0.3 Style Intelligence Layer. The minimal style contract successfully guides both translation and styling to replicate author voice.
