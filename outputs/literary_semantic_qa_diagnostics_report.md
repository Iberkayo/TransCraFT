# Literary Semantic QA Diagnostics

## Summary

Deterministic diagnostics for literary semantic risk, Turkish fluency anomalies, and chunk boundary risks.

## Cases

### flatboat_mistranslation

**Source**

```text
He was taken on for a flatboat.
```

**Target**

```text
Bir düzenbaz için alındı.
```

- Semantic flags: `[{'type': 'semantic_mistranslation_risk', 'source_term': 'flatboat', 'target_evidence': 'düzenbaz', 'severity': 'critical', 'suggested_senses': ['sal', 'düz tabanlı tekne', 'nehir teknesi', 'düz tekne'], 'recommendation': 'review flatboat translation'}]`
- Fluency flags: `[]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### schoolmaster_risk

**Source**

```text
His father has been a schoolmaster.
```

**Target**

```text
Babası okul müdürü olmuştu.
```

- Semantic flags: `[{'type': 'literary_term_risk', 'source_term': 'schoolmaster', 'target_evidence': 'okul müdürü', 'severity': 'major', 'suggested_senses': ['okul hocası', 'öğretmen'], 'recommendation': 'review schoolmaster translation'}]`
- Fluency flags: `[]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### scullery_fire_risk

**Source**

```text
He stokes the scullery fire.
```

**Target**

```text
Bulaşık ocağını besler.
```

- Semantic flags: `[{'type': 'literary_term_risk', 'source_term': 'scullery fire', 'target_evidence': 'bulaşık ocağı', 'severity': 'major', 'suggested_senses': ['mutfak ocağı', 'arka mutfak ocağı'], 'recommendation': 'review scullery fire translation'}]`
- Fluency flags: `[]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### dipper_context

**Source**

```text
The Dipper stove.
```

**Target**

```text
Kepçe devrildi.
```

- Semantic flags: `[{'type': 'literary_term_risk', 'source_term': 'Dipper', 'target_evidence': 'kepçe', 'severity': 'major', 'suggested_senses': ['Büyük Kepçe', 'takımyıldızı bağlamı'], 'recommendation': 'review Dipper translation'}]`
- Fluency flags: `[]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### full_house_risk

**Source**

```text
The Reverend Green preached to a full house.
```

**Target**

```text
Rahip Green dolu salonda oynuyordu.
```

- Semantic flags: `[{'type': 'literary_term_risk', 'source_term': 'full house', 'target_evidence': 'dolu salonda oynuyordu', 'severity': 'major', 'suggested_senses': ['kalabalık cemaate vaaz veriyordu', 'çadırı dolduran kalabalığa konuşuyordu'], 'recommendation': 'review full house translation'}]`
- Fluency flags: `[{'type': 'register_semantic_oddity', 'evidence': 'dolu salonda oynuyordu', 'severity': 'major', 'recommendation': 'review preaching/full-house rendering'}]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### lowercase_chunk_continuation

**Source**

```text
he feels mankind itself vindicated.
```

**Target**

```text
kendini haklı çıkarmıştı.
```

- Semantic flags: `[]`
- Fluency flags: `[]`
- Chunk boundary flags: `[{'type': 'lowercase_chunk_start', 'evidence': 'itself vindicated', 'severity': 'major', 'recommendation': 'merge with previous chunk or adjust boundary'}, {'type': 'continuation_chunk_start', 'evidence': 'itself vindicated', 'severity': 'major', 'recommendation': 'merge with previous chunk or adjust boundary'}]`
- Recommendation: `review`

### broken_turkish_ne_ne_de

**Source**

```text
He can neither read nor write.
```

**Target**

```text
Ne okuyup yazma bilir ne de.
```

- Semantic flags: `[]`
- Fluency flags: `[{'type': 'broken_turkish_grammar', 'evidence': 'Ne okuyup yazma bilir ne de', 'severity': 'critical', 'recommendation': 'review malformed Turkish phrase'}]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### typo_fittik

**Source**

```text
He was seven foot tall.
```

**Target**

```text
Neredeyse yedi fittik boyundaydı.
```

- Semantic flags: `[{'type': 'unit_or_typo_risk', 'evidence': 'fittik', 'severity': 'major', 'recommendation': 'review unit rendering'}]`
- Fluency flags: `[{'type': 'unit_or_typo_risk', 'evidence': 'fittik', 'severity': 'major', 'recommendation': 'review unit rendering typo'}]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### double_spaces

**Source**

```text
His face remained oddly innocent.
```

**Target**

```text
Yüzü tuhaf  masumdur.
```

- Semantic flags: `[]`
- Fluency flags: `[{'type': 'double_space', 'evidence': 'Yüzü tuhaf  masumdur.', 'severity': 'minor', 'recommendation': 'remove accidental double space'}]`
- Chunk boundary flags: `[]`
- Recommendation: `review`

### clean_literary_sentence

**Source**

```text
The boy crouches by the fire and watches him.
```

**Target**

```text
Çocuk ateşin yanında çömelir ve onu izler.
```

- Semantic flags: `[]`
- Fluency flags: `[]`
- Chunk boundary flags: `[]`
- Recommendation: `accept`

## Limitations

This is deterministic QA, not proof of semantic correctness.
Human literary review is still required.
