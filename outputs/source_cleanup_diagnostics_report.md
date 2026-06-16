# Source Cleanup Diagnostics

## Summary

Synthetic diagnostics for PDF extraction cleanup. The cleaner performs conservative repairs and flags uncertain merged tokens for review.

## Cases

### merged_pdf_tokens

**Input**

```text
He stokesthe scullery fire. Outside lie dark fields with darker woodsbeyond.
```

- Expected: `n/a`

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

- Expected: `n/a`

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

- Expected: `n/a`

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

- Expected: `n/a`

**Cleaned**

```text
The rider crossed the mountain road and kept going.
```

- Repairs: `[{'type': 'hyphenation_repair', 'before': 'line-break hyphenation', 'after': 'joined token', 'confidence': 'medium', 'count': 1}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

### split_initial_letter

**Input**

```text
S ee the child.
```

- Expected: `See the child.`

**Cleaned**

```text
See the child.
```

- Repairs: `[{'type': 'split_initial_letter_repair', 'before': 'S ee', 'after': 'See', 'confidence': 'high'}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

### split_initial_now

**Input**

```text
N ow come days of begging.
```

- Expected: `Now come days of begging.`

**Cleaned**

```text
Now come days of begging.
```

- Repairs: `[{'type': 'split_initial_letter_repair', 'before': 'N ow', 'after': 'Now', 'confidence': 'high'}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

### invisible_word_split

**Input**

```text
Neigh​bor, you caint get shed of him.
```

- Expected: `Neighbor, you caint get shed of him.`

**Cleaned**

```text
Neighbor, you caint get shed of him.
```

- Repairs: `[{'type': 'invisible_word_split_repair', 'before': 'Neigh\u200bbor', 'after': 'Neighbor', 'confidence': 'medium'}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

### word_internal_split

**Input**

```text
from his cloth​ing
```

- Expected: `from his clothing`

**Cleaned**

```text
from his clothing
```

- Repairs: `[{'type': 'invisible_word_split_repair', 'before': 'cloth\u200bing', 'after': 'clothing', 'confidence': 'medium'}]`
- Cleanup recommendation: `accept`
- Quality score: `1.0`
- Quality flags: `[]`
- Quality recommendation: `accept`

## Limitations

- The repair map is intentionally small.
- Split initial-letter repair is limited to explicit high-confidence forms such as `S ee` and `N ow`.
- Invisible separators inside alphabetic tokens are joined, but semantic word-boundary questions still require review.
- Uncertain merged words are flagged instead of guessed.
- Diagnostics use synthetic examples; chapter extraction still requires boundary review.
