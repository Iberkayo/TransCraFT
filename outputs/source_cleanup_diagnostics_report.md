# Source Cleanup Diagnostics

## Summary

Synthetic diagnostics for PDF extraction cleanup. The cleaner performs conservative repairs and flags uncertain merged tokens for review.

## Cases

### merged_pdf_tokens

**Input**

```text
He stokesthe scullery fire. Outside lie dark fields with darker woodsbeyond.
```

**Cleaned**

```text
He stokes the scullery fire. Outside lie dark fields with darker woods beyond.
```

- Repairs: `[{'type': 'merged_word_repair', 'before': 'stokesthe', 'after': 'stokes the', 'confidence': 'high'}, {'type': 'merged_word_repair', 'before': 'woodsbeyond', 'after': 'woods beyond', 'confidence': 'high'}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

### punctuation_spacing

**Input**

```text
The boy watches him.He waits,he listens.
```

**Cleaned**

```text
The boy watches him. He waits, he listens.
```

- Repairs: `[{'type': 'punctuation_spacing_repair', 'before': 'missing space after punctuation', 'after': 'space after punctuation', 'confidence': 'high', 'count': 2}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

### uncertain_merged_token

**Input**

```text
This unknownmergedtoken should be flagged rather than guessed.
```

**Cleaned**

```text
This unknownmergedtoken should be flagged rather than guessed.
```

- Repairs: `[]`
- Cleanup recommendation: `review`
- Quality score: `0.94`
- Quality flags: `[{'type': 'suspicious_long_lowercase_tokens', 'count': 1, 'evidence': ['unknownmergedtoken'], 'recommendation': 'review source extraction'}]`
- Quality recommendation: `review`

### hyphenation

**Input**

```text
The rider crossed the moun-
tain road and kept going.
```

**Cleaned**

```text
The rider crossed the mountain road and kept going.
```

- Repairs: `[{'type': 'hyphenation_repair', 'before': 'line-break hyphenation', 'after': 'joined token', 'confidence': 'medium', 'count': 1}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

## Limitations

- The repair map is intentionally small.
- Uncertain merged words are flagged instead of guessed.
- Diagnostics use synthetic examples; chapter extraction still requires boundary review.
