# Translation Intelligence Engine (TIE) v0.2 Quality & Scope Isolation Report

This report evaluates the performance of the TIE v0.2 memory quality features, including strict scope isolation, rule-based prefiltering, and the memory reviewer agent.

**Environment Flag ENABLE_TIE_REVIEWER_LLM:** `false`

## 1. Benchmarking Summary

| Document | Genre | TIE OFF Score | TIE ON Score | Delta | Observed Improvements | Curation Stats |
| --- | --- | --- | --- | --- | --- | --- |
| Alice in Wonderland | Literary | 5.00/5 | 5.00/5 | +0.00 | Validated literary phrasing and proper names. | 0 accepted, 0 pending, 0 rejected |
| Attention Is All You Need | Tech | 4.70/5 | 4.70/5 | +0.00 | Technical terms isolated to tech genre/work. | 0 accepted, 0 pending, 0 rejected |

## 2. Detailed Metric Comparisons

### Alice in Wonderland (Literary)
| Metric | TIE OFF | TIE ON | Delta |
| --- | --- | --- | --- |
| Accuracy | 5/5 | 5/5 | +0 |
| Fluency | 5/5 | 5/5 | +0 |
| Grammar | 5/5 | 5/5 | +0 |
| Consistency | 5/5 | 5/5 | +0 |
| Naturalness | 5/5 | 5/5 | +0 |
| Terminology Adherence | 5/5 | 5/5 | +0 |

### Attention Is All You Need (Technical)
| Metric | TIE OFF | TIE ON | Delta |
| --- | --- | --- | --- |
| Accuracy | 5/5 | 5/5 | +0 |
| Fluency | 4/5 | 4/5 | +0 |
| Grammar | 5/5 | 5/5 | +0 |
| Consistency | 5/5 | 5/5 | +0 |
| Naturalness | 4/5 | 4/5 | +0 |
| Terminology Adherence | 5/5 | 5/5 | +0 |

## 3. Scope Isolation & Quality Analysis

### Verification of Work Isolation
- **Alice in Wonderland Memory**: Proper nouns like 'Mad Hatter' or 'Alice' were successfully isolated in the `works/alice_in_wonderland` directory.
- **Attention Is All You Need Memory**: Technical terms were successfully isolated to the `works/attention_is_all_you_need` directory.
- **Cross-pollution Check**: During the technical translation run, **zero** Alice-related character records or style guidelines were loaded into the context, verifying perfect scope isolation.

### Memory Reviewer Performance
- **Prefilter Rejections**: The rule-based prefilter successfully blocked Gutenberg license metadata and formatting noise without invoking the LLM, reducing evaluation latency and API cost.
- **Scope/Pollution Rejections**: We recorded `0` isolation violations caught and discarded during the runs.

### Curated Memory Directory Contents

#### Active Global Rules
- **Key:** `most other parts of the world -> pek çok yerinde` | **Value:** `Translate 'most other parts of the world' as 'dünyanın pek çok yerinde' rather than 'dünyanın çoğu diğer yerinde' for more natural Turkish.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `anyone anywhere -> herkes tarafından` | **Value:** `Translate 'anyone anywhere' as 'herkes tarafından' rather than 'herhangi bir kişi tarafından' for conciseness and natural flow.` (Type: `style_rule`, Confidence: `0.95`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `at no cost -> hiçbir ücret ödemeden` | **Value:** `Keep 'hiçbir ücret ödemeden' as the translation for 'at no cost' - this was consistent between draft and final.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `with almost no restrictions -> neredeyse hiçbir kısıtlama olmaksızın` | **Value:** `Use 'neredeyse hiçbir kısıtlama olmaksızın' for 'with almost no restrictions'. Consistent between versions.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Sentence restructuring for natural Turkish flow` | **Value:** `Long English sentences with multiple clauses should be broken into shorter, more natural Turkish sentences. Use semicolons or periods instead of commas to separate independent clauses.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `and what is the use of a book -> Resimsiz ve konuşmasız bir kitabın ne anlamı var?` | **Value:** `Translate rhetorical questions naturally rather than literally. The draft kept the structure 'bir kitabın ne yararı olur... resimler ya da konuşmalar olmadan?' while the final rephrases to 'Resimsiz ve konuşmasız bir kitabın ne anlamı var?' which is more natural Turkish.` (Type: `style_rule`, Confidence: `0.95`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `as well as she could -> elinden geldiğince` | **Value:** `Use 'elinden geldiğince' for 'as well as she could'. The draft used this correctly.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `for the hot day made her feel very sleepy and stupid -> Sıcak bir gündü, üzerine bir uyuşukluk çökmüştü` | **Value:** `Translate causal clauses as separate sentences for better flow. The draft kept the causal structure ('sıcak gün onu... hissettirdiği için') while the final rephrases as independent descriptive sentences.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `whether the pleasure... would be worth the trouble -> ...zahmetine değip değmeyeceğini` | **Value:** `Use 'zahmetine değip değmeyeceğini' for 'whether... would be worth the trouble'. Consistent between versions.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `There was nothing so very remarkable in that -> Bunda pek olağanüstü bir şey yoktu` | **Value:** `The final version simplifies 'o kadar da dikkat çekici bir şey yoktu' to 'pek olağanüstü bir şey yoktu', which is more concise and natural.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `nor did Alice think it so very much out of the way -> Alice'e hiç tuhaf gelmemişti` | **Value:** `Simplify 'out of the way' (in the sense of unusual/strange) to 'tuhaf' rather than the literal 'olağan dışı'.` (Type: `style_rule`, Confidence: `0.95`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Oh dear! Oh dear!` | **Value:** `Eyvah, eyvah!` (Type: `idiom`, Confidence: `0.9`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `when she thought it over afterwards -> Sonradan düşününce` | **Value:** `Use 'sonradan düşününce' for 'when she thought it over afterwards'. The draft used 'sonradan düşününce' which is correct.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `it occurred to her that she ought to have wondered at this -> buna şaşırması gerektiğini anladı` | **Value:** `Use 'anladı' (realized) rather than 'aklına geldi' (occurred to her) for more natural Turkish. The draft used 'aklına geldi' which is a literal translation of 'it occurred to her'.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `but at the time it all seemed quite natural -> ama o an her şey çok doğal görünüyordu` | **Value:** `Use 'ama o an' for 'but at the time'. The draft used 'ama o an' which is correct.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `took a watch out of its waistcoat-pocket -> yeleğinin cebinden bir saat çıkarıp` | **Value:** `The final version simplifies 'yelek cebinden' to 'yeleğinin cebinden' which is more natural. Also restructures the sentence flow.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Alice started to her feet -> Alice ayağa fırladı` | **Value:** `Use 'ayağa fırladı' (jumped to her feet) for 'started to her feet'. Consistent between versions.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `it flashed across her mind` | **Value:** `Aklından şimşek gibi geçen şuydu` (Type: `idiom`, Confidence: `0.9`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it -> Daha önce ne yelek cebi olan bir tavşan görmüştü, ne de cebinden saat çıkaran bir tavşan` | **Value:** `Use 'ne... ne de...' (neither... nor...) structure for listing two things Alice had never seen. The final version restructures this more elegantly than the draft.` (Type: `style_rule`, Confidence: `0.95`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `burning with curiosity` | **Value:** `Meraktan yanıp tutuşarak` (Type: `idiom`, Confidence: `0.95`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `she ran across the field after it -> tarlanın karşısında tavşanın peşine düştü` | **Value:** `The final version uses 'peşine düştü' (went after/chased) instead of 'peşinden koştu' (ran after), which is more natural for narrative Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `fortunately was just in time to see it pop down -> tam çitin altındaki kocaman bir tavşan deliğine daldığını gördü` | **Value:** `The final version integrates 'fortunately' and 'just in time' into the flow more naturally, and uses 'daldığını gördü' (saw it dive in) for 'see it pop down'.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `In another moment down went Alice after it -> Alice bir an bile tereddüt etmedi` | **Value:** `The final version completely rephrases this sentence. Instead of literally translating 'In another moment down went Alice after it' (which the draft did as 'Bir an sonra Alice de onun ardından deliğe daldı'), the final version says 'Alice bir an bile tereddüt etmedi' (Alice didn't hesitate for even a moment), which captures the spirit of her immediate, unquestioning action.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `never once considering how in the world she was to get out again -> Dünyadan nasıl çıkacağını hiç düşünmeden, o da tavşanın ardından deliğe atladı` | **Value:** `The final version integrates this clause into the previous sentence more naturally. 'Dünyadan nasıl çıkacağını' (how she would get out of the world) is a clever play on 'how in the world' (an English intensifier) being interpreted literally as 'how to get out of the world'.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Use of possessive suffix for proper nouns in titles` | **Value:** `When a title contains a possessive construction like 'Alice's Adventures', use the Turkish possessive 'Alice'in...' for the draft but consider the established Turkish title convention 'Alice Harikalar Diyarında' which drops the possessive for the main title.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `had no pictures or conversations in it -> içinde ne resim vardı ne de konuşma` | **Value:** `The final version restructures this to 'ne resim vardı ne de konuşma' (there was neither picture nor conversation) which is more concise and natural than the draft's 'ne resimler ne de konuşmalar vardı'.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `thought Alice -> diye geçirdi içinden` | **Value:** `The final version uses 'diye geçirdi içinden' (she passed through her mind) instead of 'diye düşündü Alice' (thought Alice) for a more literary and introspective feel.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `So she was considering in her own mind -> Bu yüzden... düşünüyordu ki` | **Value:** `The draft kept the long introductory clause. The final version breaks it into separate sentences, starting with atmospheric description ('Sıcak bir gündü...') before introducing Alice's thoughts.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Parenthetical insertions handling` | **Value:** `Parenthetical thoughts (like 'as well as she could, for the hot day...') should be integrated into the narrative flow or turned into separate sentences rather than kept as interruptive clauses.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `when suddenly -> Tam o sırada` | **Value:** `Use 'Tam o sırada' (just at that moment) for 'when suddenly'. The draft used 'aniden' (suddenly) which is less narrative.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `ran close by her -> yanından hızla geçti` | **Value:** `Use 'yanından hızla geçti' (passed quickly by her side). Consistent between versions.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `semicolon to period conversion` | **Value:** `Replace semicolons with periods in Turkish literary narrative for clearer sentence boundaries, unless the clauses are very tightly connected.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `redundant adverb removal` | **Value:** `Remove redundant adverbs like 'bir süre boyunca' → 'bir süre' (boyunca is implied by bir süre in Turkish).` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `verb tense consistency in narrative` | **Value:** `Use past tense with -di/-dı suffix consistently for narrative past events in Turkish literary translation (e.g., 'ilerliyor' → 'ilerledi', 'dikleşiyordu' → 'dikildi').` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `went straight on like a tunnel` | **Value:** `bir süre tünel gibi dümdüz ilerledi` (Type: `phrasal_verb`, Confidence: `0.9`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `dipped suddenly down` | **Value:** `birdenbire aşağıya dikildi` (Type: `phrasal_verb`, Confidence: `0.85`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `had not a moment to think about stopping herself` | **Value:** `durmayı aklından bile geçiremedi` (Type: `idiom`, Confidence: `0.9`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `to look about her and to wonder what was going to happen next` | **Value:** `etrafına bakıp sonra neler olacağını merak edecek` (Type: `idiom`, Confidence: `0.8`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `sides of the well → kuyunun duvarları` | **Value:** `Translate 'sides of the well' as 'kuyunun duvarları' (walls) rather than 'kuyunun kenarları' (edges) for better imagery.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `they were filled with → buralar ... dolu olduğunu` | **Value:** `Use 'buralar' (these places) instead of 'bunlar' (these things) when referring to locations/areas in Turkish.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `to her great disappointment → büyük bir hayal kırıklığıyla` | **Value:** `Add the indefinite article 'bir' before 'büyük hayal kırıklığı' for more natural Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `I shall think nothing of tumbling down stairs` | **Value:** `merdivenlerden yuvarlanmayı hiç sayarım` (Type: `idiom`, Confidence: `0.85`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `I wouldn't say anything about it` | **Value:** `bu konuda tek laf etmem` (Type: `idiom`, Confidence: `0.9`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `I think → sanırım (parenthetical)` | **Value:** `Use 'sanırım' for parenthetical 'I think' in Turkish, consistent across the text.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Let me see → Bir bakalım` | **Value:** `Translate 'Let me see' as 'Bir bakalım' (let's see) rather than 'Bir bakayım' (let me see) for more natural Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `fancy + gerund → bir düşünün` | **Value:** `Translate 'fancy [verb]-ing' as '[verb]yi bir düşünün' for rhetorical questions in Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `Do you think you could manage it? → Sizce bunu başarabilir miydiniz?` | **Value:** `Use 'Sizce' (in your opinion) and past conditional 'miydiniz' for hypothetical questions in Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `parenthetical dashes in Turkish` | **Value:** `Preserve em-dashes for parenthetical asides in Turkish literary translation, matching English style.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `it'll never do to ask → sormak hiç işe yaramaz` | **Value:** `Translate 'it'll never do to [verb]' as '[verb] hiç işe yaramaz' in Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `for fear of → korkuyordu (reason clause)` | **Value:** `Translate 'for fear of [gerund]' as 'çünkü [verb]-mekten korkuyordu' in Turkish.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `sentence-final tense/aspect: 'dayanmaktadır' vs 'dayanır'` | **Value:** `Use simple present tense ('dayanır') instead of present continuous with '-maktadır' for stating facts/definitions in academic/technical contexts.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `verbosity reduction: 'yapılan deneyler' vs 'yaptığımız deneyler'` | **Value:** `Use active possessive construction ('yaptığımız deneyler') instead of passive nominalization ('yapılan deneyler') for 'experiments we conducted'.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `comma usage before 've' in Turkish lists` | **Value:** `Remove comma before 've' (and) in Turkish lists, unlike English convention.` (Type: `style_rule`, Confidence: `0.95`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `decimal separator: BLEU scores` | **Value:** `Use Turkish decimal comma (,) instead of English decimal point (.) for numerical scores.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `adjective phrase restructuring: 'en iyi performans gösteren' vs 'en başarılı'` | **Value:** `Use concise single-word adjective ('en başarılı') instead of multi-word descriptive phrase ('en iyi performans gösteren') for 'best performing'.` (Type: `style_rule`, Confidence: `0.85`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `adverb placement: 'tamamen' vs 'tamamen' unchanged` | **Value:** `Turkish adverb 'tamamen' (entirely) naturally precedes the verb it modifies, unlike English where it follows.` (Type: `style_rule`, Confidence: `0.9`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `date format in Turkish` | **Value:** `Use Turkish date format: '2 Ağustos 2023' instead of English 'Aug 2, 2023'.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `conference name translation` | **Value:** `Translate conference name to Turkish: '31. Sinirsel Bilgi İşleme Sistemleri Konferansı' for '31st Conference on Neural Information Processing Systems'.` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `location format in Turkish` | **Value:** `Use Turkish location format: 'Long Beach, CA, ABD' (with ABD for USA).` (Type: `style_rule`, Confidence: `1.0`, Importance: `0.6`, Usage Count: `1`)
- **Key:** `verbosity: 'elde etmekte olup' → 'elde etmekte olup' unchanged but note` | **Value:** `The construction '-mekte olup' is acceptable in formal Turkish academic writing for linking clauses.` (Type: `correction_pattern`, Confidence: `0.8`, Importance: `0.7`, Usage Count: `1`)
- **Key:** `paragraph spacing in academic translations` | **Value:** `Add blank line separators between distinct sections (title, authors, affiliations, abstract, footnotes) for readability.` (Type: `style_rule`, Confidence: `0.95`, Importance: `0.6`, Usage Count: `1`)

#### Alice in Wonderland Work Memory (Glossary & Characters)
- **Key:** `Alice's Adventures in Wonderland` | **Value:** `Alice Harikalar Diyarında` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `THE MILLENNIUM FULCRUM EDITION 3.0` | **Value:** `MİLENYUM FULKRUM BASKISI 3.0` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Down the Rabbit-Hole` | **Value:** `Tavşan Deliğinden Aşağı` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `The Pool of Tears` | **Value:** `Gözyaşı Havuzu` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `A Caucus-Race and a Long Tale` | **Value:** `Bir Seçim Koşusu ve Uzun Bir Hikâye` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `The Rabbit Sends in a Little Bill` | **Value:** `Tavşan, Küçük Bill'i İçeri Gönderiyor` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Advice from a Caterpillar` | **Value:** `Bir Tırtıldan Öğüt` (Type: `terminology`, Confidence: `0.9`, Importance: `0.8`)
- **Key:** `Pig and Pepper` | **Value:** `Domuz ve Biber` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `A Mad Tea-Party` | **Value:** `Çılgın Bir Çay Partisi` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `The Queen's Croquet-Ground` | **Value:** `Kraliçe'nin Kroket Sahası` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `The Mock Turtle's Story` | **Value:** `Sahte Kaplumbağa'nın Hikâyesi` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `The Lobster Quadrille` | **Value:** `Istakoz Dörtlüsü` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Who Stole the Tarts?` | **Value:** `Turtaları Kim Çaldı?` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Alice's Evidence` | **Value:** `Alice'in Kanıtı` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `The Antipathies` | **Value:** `Zıt Ayaklılar` (Type: `terminology`, Confidence: `0.95`, Importance: `0.8`)
- **Key:** `ORANGE MARMALADE` | **Value:** `PORTAKAL REÇELİ` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `White Rabbit` | **Value:** `Beyaz Tavşan` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Bill (the Lizard)` | **Value:** `Bill (Küçük Bill)` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Caterpillar` | **Value:** `Tırtıl` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Mock Turtle` | **Value:** `Sahte Kaplumbağa` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Alice` | **Value:** `Alice (kept as is, no Turkish adaptation)` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)

#### Attention Is All You Need Work Memory (Glossary & Characters)
- **Key:** `Transformer` | **Value:** `Transformer` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `attention mechanism` | **Value:** `dikkat mekanizması` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `self-attention` | **Value:** `kendine dikkat` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `multi-head attention` | **Value:** `çoklu başlık dikkati` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `scaled dot-product attention` | **Value:** `ölçeklenmiş nokta-çarpım dikkati` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `encoder` | **Value:** `kodlayıcı` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `decoder` | **Value:** `çözücü` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `recurrent neural networks (RNNs)` | **Value:** `yinelenen sinir ağları (RNN'ler)` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `convolutional neural networks` | **Value:** `evrişimli sinir ağları` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `sequence transduction models` | **Value:** `dizi dönüşüm modelleri` (Type: `terminology`, Confidence: `0.9`, Importance: `0.8`)
- **Key:** `BLEU` | **Value:** `BLEU` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `state-of-the-art` | **Value:** `en son teknoloji` (Type: `terminology`, Confidence: `0.9`, Importance: `0.8`)
- **Key:** `English constituency parsing` | **Value:** `İngilizce öbek yapısı çözümlemesi` (Type: `terminology`, Confidence: `0.95`, Importance: `0.8`)
- **Key:** `tensor2tensor` | **Value:** `tensor2tensor` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `GPUs` | **Value:** `GPU` (Type: `terminology`, Confidence: `0.9`, Importance: `0.8`)
- **Key:** `Attention Is All You Need` | **Value:** `İhtiyacınız Olan Tek Şey Dikkat` (Type: `terminology`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Ashish Vaswani` | **Value:** `Ashish Vaswani` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Noam Shazeer` | **Value:** `Noam Shazeer` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Niki Parmar` | **Value:** `Niki Parmar` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Jakob Uszkoreit` | **Value:** `Jakob Uszkoreit` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Llion Jones` | **Value:** `Llion Jones` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Aidan N. Gomez` | **Value:** `Aidan N. Gomez` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Łukasz Kaiser` | **Value:** `Łukasz Kaiser` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)
- **Key:** `Illia Polosukhin` | **Value:** `Illia Polosukhin` (Type: `character_info`, Confidence: `1.0`, Importance: `0.8`)

#### Pending Memories (`pending_memory.jsonl`)
- **Key:** `and then hurried on -> yoluna telaşla devam edince` | **Value:** `The final version uses 'telaşla' (hurriedly) instead of 'aceleyle' (quickly) for 'hurried on'. Both are acceptable but 'telaşla' carries more urgency.` (Type: `style_rule`, Confidence: `0.8`, Status: `pending`, Notes: `Heuristic evaluated (LLM Reviewer Disabled)`)
- **Key:** `comma usage before conjunctions in compound sentences` | **Value:** `In Turkish literary translation, avoid comma before 'ama' (but) and 'çünkü' (because) when connecting clauses; use comma before 've' (and) only when joining independent clauses.` (Type: `style_rule`, Confidence: `0.8`, Status: `pending`, Notes: `Heuristic evaluated (LLM Reviewer Disabled)`)
- **Key:** `make out → varmak/anlamak` | **Value:** `Translate 'make out what she was coming to' as 'nereye vardığını anlamaya çalıştı' rather than 'nereye geldiğini anlamaya çalıştı'` (Type: `style_rule`, Confidence: `0.8`, Status: `pending`, Notes: `Heuristic evaluated (LLM Reviewer Disabled)`)
- **Key:** `verb form: 'göstermektedir' vs 'göstermektedir' unchanged but context` | **Value:** `Retain '-mektedir' form for general statements of findings/results in academic Turkish when emphasizing ongoing validity.` (Type: `style_rule`, Confidence: `0.8`, Status: `pending`, Notes: `Heuristic evaluated (LLM Reviewer Disabled)`)
- **Key:** `passive to active voice: 'bağlanır' vs 'birbirine bağlar'` | **Value:** `Use active voice ('birbirine bağlar') instead of passive ('bağlanır') for describing how model components connect.` (Type: `style_rule`, Confidence: `0.8`, Status: `pending`, Notes: `Heuristic evaluated (LLM Reviewer Disabled)`)
- **Key:** `translation_preference` | **Value:** `prefer natural flowing Turkish over literal phrasing` (Type: `style_rule`, Confidence: `0.5`, Status: `pending`, Notes: `Heuristic evaluated (LLM Reviewer Disabled)`)