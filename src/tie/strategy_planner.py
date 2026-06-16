import re
from typing import Any, Dict, List, Optional

from src.core.config import Config
from src.tie.language_profile import LanguageProfileLoader
from src.tie.structural_risk_detector import StructuralRiskDetector


REQUIRED_STRATEGY_FIELDS = [
    "source_language",
    "target_language",
    "text_type",
    "tone",
    "register",
    "audience",
    "literalness_level",
    "sentence_reconstruction_strategy",
    "localization_strategy",
    "meaning_units",
    "structural_risks",
    "target_language_rules",
    "translator_instructions",
    "critic_checklist",
    "turkish_reconstruction_notes",
    "fallback_used",
]


class TranslationStrategyPlanner:
    """Create a structured translation strategy without exposing hidden reasoning."""

    def __init__(
        self,
        profile_loader: Optional[LanguageProfileLoader] = None,
        enable_llm: bool = False,
    ):
        self.profile_loader = profile_loader or LanguageProfileLoader()
        self.enable_llm = enable_llm
        self.risk_detector = StructuralRiskDetector()

    def plan(
        self,
        source_text: str,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        genre: Optional[str] = None,
        style: Optional[str] = None,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
        style_contract: Optional[Dict[str, Any]] = None,
        memory_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        del user_id  # Reserved for future user-specific planning.

        pair = self.profile_loader.load_pair(source_language, target_language)
        source_profile = pair["source_profile"]
        target_profile = pair["target_profile"]
        strategy = self._fallback_strategy(
            source_text=source_text,
            source_profile=source_profile,
            target_profile=target_profile,
            genre=genre or "general",
            style=style,
            work_id=work_id,
            style_contract=style_contract,
            memory_context=memory_context,
        )
        return self._ensure_required_fields(strategy)

    def language_profile_context(
        self,
        source_language: Optional[str],
        target_language: Optional[str],
    ) -> Dict[str, Any]:
        pair = self.profile_loader.load_pair(source_language, target_language)
        return {
            "source_language_profile": pair["source_profile"],
            "target_language_profile": pair["target_profile"],
        }

    def _fallback_strategy(
        self,
        source_text: str,
        source_profile: Dict[str, Any],
        target_profile: Dict[str, Any],
        genre: str,
        style: Optional[str],
        work_id: Optional[str],
        style_contract: Optional[Dict[str, Any]],
        memory_context: Optional[str],
    ) -> Dict[str, Any]:
        text_type = self._text_type(genre)
        tone = self._tone(genre, style_contract)
        register = self._register(genre)
        literalness = self._literalness(genre)
        detected_risks = self.risk_detector.detect(source_text, genre=genre)
        meaning_units = self._meaning_units(source_text, detected_risks)
        structural_risks = self._structural_risks(source_text, target_profile, detected_risks)
        target_rules = self._target_rules(target_profile, genre)
        reconstruction_notes = self._reconstruction_notes(genre, target_profile, style_contract, detected_risks)
        translator_instructions = self._translator_instructions(genre, memory_context, work_id, detected_risks)
        critic_checklist = self._critic_checklist(genre, target_profile, detected_risks)

        return {
            "source_language": source_profile.get("language_code", "en_US"),
            "target_language": target_profile.get("language_code", "tr_TR"),
            "text_type": text_type,
            "tone": tone,
            "register": register,
            "audience": self._audience(target_profile, text_type),
            "literalness_level": literalness,
            "sentence_reconstruction_strategy": self._sentence_strategy(genre),
            "localization_strategy": self._localization_strategy(genre),
            "meaning_units": meaning_units,
            "structural_risks": structural_risks,
            "target_language_rules": target_rules,
            "translator_instructions": translator_instructions,
            "critic_checklist": critic_checklist,
            "turkish_reconstruction_notes": reconstruction_notes,
            "fallback_used": True,
        }

    def _text_type(self, genre: str) -> str:
        genre_norm = (genre or "general").casefold()
        if genre_norm in {"literary", "fiction", "novel"}:
            return "literary_fiction"
        if genre_norm in {"tech", "technical"}:
            return "technical"
        if genre_norm in {"academic", "paper"}:
            return "academic"
        if genre_norm in {"business", "legal"}:
            return "business"
        return "general"

    def _tone(self, genre: str, style_contract: Optional[Dict[str, Any]]) -> str:
        if style_contract and style_contract.get("tone"):
            return str(style_contract["tone"])
        if self._text_type(genre) == "literary_fiction":
            return "literary, attentive to rhythm and atmosphere"
        if self._text_type(genre) in {"technical", "academic"}:
            return "clear, precise, controlled"
        return "natural and fluent"

    def _register(self, genre: str) -> str:
        text_type = self._text_type(genre)
        if text_type == "literary_fiction":
            return "literary"
        if text_type in {"technical", "academic"}:
            return "formal technical"
        if text_type == "business":
            return "formal business"
        return "natural"

    def _literalness(self, genre: str) -> str:
        text_type = self._text_type(genre)
        if text_type == "literary_fiction":
            return "medium_low"
        if text_type in {"technical", "academic"}:
            return "medium"
        return "medium_low"

    def _meaning_units(self, source_text: str, detected_risks: Optional[List[Dict[str, str]]] = None) -> List[str]:
        detected_risks = detected_risks or []
        if any(r["risk_type"] == "long_relative_clause" for r in detected_risks):
            parts = [p.strip(" ,;") for p in re.split(r",\s*(?=a decision|which|that|who|whose|where)", source_text, maxsplit=1, flags=re.IGNORECASE)]
            if len(parts) > 1:
                return [self._compact(part) for part in parts if part][:6]
        chunks = [s.strip() for s in re.split(r"(?<=[.!?;:])\s+", source_text or "") if s.strip()]
        if not chunks and source_text:
            chunks = [source_text.strip()]
        return [self._compact(unit) for unit in chunks[:6]]

    def _structural_risks(
        self,
        source_text: str,
        target_profile: Dict[str, Any],
        detected_risks: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        risks = list(detected_risks)
        if not risks and "translationese_patterns_to_avoid" in target_profile:
            risks.append(
                {
                    "risk_type": "translationese_risk",
                    "evidence": self._compact(source_text[:120]),
                    "translation_risk": "Target profile lists translationese patterns that should be avoided.",
                    "recommended_strategy": "Check target-profile anti-translationese rules before final wording.",
                }
            )
        return risks[:8]

    def _target_rules(self, target_profile: Dict[str, Any], genre: str) -> List[str]:
        rules = list(target_profile.get("core_rules", []))[:8]
        genre_rules = target_profile.get("genre_preferences", {}).get((genre or "general"), [])
        return (rules + genre_rules)[:10]

    def _audience(self, target_profile: Dict[str, Any], text_type: str) -> str:
        name = target_profile.get("name") or target_profile.get("language_code") or "target-language"
        if text_type == "technical":
            return f"technical {name} readers"
        return f"general {name} readers"

    def _reconstruction_notes(
        self,
        genre: str,
        target_profile: Dict[str, Any],
        style_contract: Optional[Dict[str, Any]],
        detected_risks: List[Dict[str, str]],
    ) -> List[str]:
        notes = list(target_profile.get("reconstruction_notes", []))
        if not notes:
            notes = [
                "avoid literal source-language word order",
                "reconstruct meaning naturally in the target language before final wording",
            ]
        if self._text_type(genre) == "literary_fiction":
            notes.append("preserve sparse rhythm and intentional fragments when style requires it")
        if self._text_type(genre) in {"technical", "academic"}:
            notes.append("prioritize terminology consistency and clear claims")
        if style_contract:
            notes.append("follow style contract tone and sentence rhythm")
        notes.extend(self._risk_reconstruction_notes(detected_risks))
        notes.extend(target_profile.get("translation_notes", [])[:3])
        return self._unique(notes)[:14]

    def _translator_instructions(
        self,
        genre: str,
        memory_context: Optional[str],
        work_id: Optional[str],
        detected_risks: List[Dict[str, str]],
    ) -> List[str]:
        instructions = [
            "treat strategy notes as constraints unless they harm source meaning",
            "preserve full meaning before polishing style",
            "translate by meaning units, not word by word",
            "avoid translationese and unnecessary repetition",
            "produce only the target-language translation",
        ]
        if memory_context:
            instructions.append("apply only relevant memory context already routed into the prompt")
        if work_id:
            instructions.append("respect work-specific names, terminology, and style decisions")
        if self._text_type(genre) == "literary_fiction":
            instructions.append("preserve narrative tone, imagery, and rhythm")
        if self._text_type(genre) in {"technical", "academic"}:
            instructions.append("prioritize terminology consistency and technical accuracy")
        instructions.extend(self._risk_translator_instructions(detected_risks))
        return self._unique(instructions)[:14]

    def _critic_checklist(
        self,
        genre: str,
        target_profile: Dict[str, Any],
        detected_risks: List[Dict[str, str]],
    ) -> List[str]:
        checklist = list(target_profile.get("critic_checklist", []))
        if not checklist:
            checklist = [
                "meaning preserved",
                "target-language naturalness",
                "unnecessary repetition avoided",
                "translationese patterns avoided",
                "long relative clause chains avoided",
            ]
        checklist.extend(["register consistency", "terminology consistency"])
        if self._text_type(genre) == "literary_fiction":
            checklist.append("style and rhythm preservation")
        checklist.extend(self._risk_critic_checks(detected_risks))
        return self._unique(checklist)[:16]

    def _risk_reconstruction_notes(self, risks: List[Dict[str, str]]) -> List[str]:
        notes = []
        for risk in risks:
            risk_type = risk["risk_type"]
            if risk_type == "long_relative_clause":
                notes.extend([
                    "Use two Turkish sentences when the relative clause becomes heavy.",
                    "Translate the first unit as a clear plan or factual statement.",
                    "Translate the second unit as a natural consequence in Turkish.",
                    "Avoid literal English relative-clause order.",
                ])
            elif risk_type == "business_translationese_risk":
                notes.append(
                    "Avoid literal phrases like 'merak etmesine neden oldu'; prefer natural corporate Turkish such as 'soru isaretleri yaratti' or 'endise yaratti' when meaning fits."
                )
            elif risk_type == "noun_stack":
                notes.append("Unpack the English noun stack into a clear Turkish possessive or explanatory phrase.")
            elif risk_type in {"passive_voice", "double_passive"}:
                notes.append("Keep passive voice only if it sounds natural; otherwise use a clear active Turkish structure.")
            elif risk_type == "phrasal_verb":
                notes.append("Translate the phrasal verb by function, not by its particles.")
            elif risk_type == "idiom_or_metaphor":
                notes.append("Avoid literal metaphor transfer; preserve the intended effect in natural Turkish.")
            elif risk_type == "pronoun_heavy":
                notes.append("Reduce unnecessary pronouns while keeping references clear.")
            elif risk_type == "preposition_heavy":
                notes.append("Reorder prepositional chains into natural Turkish case and verb structure.")
            elif risk_type == "literary_fragment":
                notes.append("Preserve short fragments and implied subjects where Turkish rhythm allows.")
            elif risk_type == "academic_nominalization":
                notes.append("Turn dense nominalizations into readable Turkish academic clauses when needed.")
            elif risk_type == "long_sentence":
                notes.append("Split long sentences when Turkish readability improves.")
        return notes

    def _risk_translator_instructions(self, risks: List[Dict[str, str]]) -> List[str]:
        return [
            f"For {risk['risk_type']}: {risk['recommended_strategy']}"
            for risk in risks[:6]
            if risk.get("recommended_strategy")
        ]

    def _risk_critic_checks(self, risks: List[Dict[str, str]]) -> List[str]:
        checks = []
        for risk in risks:
            risk_type = risk["risk_type"]
            if risk_type == "long_relative_clause":
                checks.append("Did the output avoid preserving a heavy English relative-clause structure?")
            elif risk_type == "business_translationese_risk":
                checks.append("Did the output avoid 'neden oldu' or similarly stiff business translationese?")
            elif risk_type == "noun_stack":
                checks.append("Did the output unpack the noun stack into readable Turkish?")
            elif risk_type in {"passive_voice", "double_passive"}:
                checks.append("Did the output avoid unnecessary passive stacking?")
            elif risk_type == "phrasal_verb":
                checks.append("Did the output translate the phrasal verb by meaning rather than particles?")
            elif risk_type == "idiom_or_metaphor":
                checks.append("Did the output avoid a literal metaphor that loses the intended effect?")
            elif risk_type == "pronoun_heavy":
                checks.append("Did the output avoid unnecessary pronoun repetition?")
            elif risk_type == "preposition_heavy":
                checks.append("Did the output avoid literal prepositional-chain order?")
            elif risk_type == "literary_fragment":
                checks.append("Did the output preserve intentional fragments and rhythm?")
            elif risk_type == "academic_nominalization":
                checks.append("Did the output keep academic meaning clear without heavy nominal piles?")
        return checks

    def _sentence_strategy(self, genre: str) -> str:
        if self._text_type(genre) == "literary_fiction":
            return "Reconstruct sentences for natural target-language flow while preserving intentional fragments and rhythm."
        if self._text_type(genre) in {"technical", "academic"}:
            return "Prefer clear target-language sentence boundaries; split long source sentences when helpful."
        return "Prefer natural target-language rhythm over literal source syntax."

    def _localization_strategy(self, genre: str) -> str:
        if self._text_type(genre) in {"technical", "academic"}:
            return "Keep technical names stable; localize explanatory phrasing without changing terms."
        return "Localize idioms and phrasing naturally while preserving source meaning."

    def _ensure_required_fields(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            "source_language": "en_US",
            "target_language": "tr_TR",
            "text_type": "general",
            "tone": "natural",
            "register": "natural",
            "audience": "general target-language readers",
            "literalness_level": "medium_low",
            "sentence_reconstruction_strategy": "Prefer natural target-language reconstruction.",
            "localization_strategy": "Localize naturally while preserving meaning.",
            "meaning_units": [],
            "structural_risks": [],
            "target_language_rules": [],
            "translator_instructions": [],
            "critic_checklist": [],
            "turkish_reconstruction_notes": [],
            "fallback_used": True,
        }
        for field, default in defaults.items():
            strategy.setdefault(field, default)
        return strategy

    def _compact(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _unique(self, items: List[str]) -> List[str]:
        seen = set()
        unique_items = []
        for item in items:
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique_items.append(item)
        return unique_items


def build_strategy_prompt_context(strategy: Optional[Dict[str, Any]], language_profile: Optional[Dict[str, Any]]) -> str:
    if not strategy:
        return ""

    def bullets(items: List[Any]) -> str:
        formatted = []
        for item in items:
            if not item:
                continue
            if isinstance(item, dict):
                formatted.append(
                    "- {risk_type}: {evidence} | risk: {translation_risk} | strategy: {recommended_strategy}".format(
                        risk_type=item.get("risk_type", "risk"),
                        evidence=item.get("evidence", ""),
                        translation_risk=item.get("translation_risk", ""),
                        recommended_strategy=item.get("recommended_strategy", ""),
                    )
                )
            else:
                formatted.append(f"- {item}")
        return "\n".join(formatted)

    target_rules = strategy.get("target_language_rules") or []
    if language_profile:
        profile_rules = language_profile.get("core_rules", [])
        target_rules = target_rules or profile_rules[:8]

    return f"""
### Translation Strategy Plan
- Source language: {strategy.get('source_language')}
- Target language: {strategy.get('target_language')}
- Text type: {strategy.get('text_type')}
- Tone: {strategy.get('tone')}
- Register: {strategy.get('register')}
- Literalness level: {strategy.get('literalness_level')}
- Sentence reconstruction: {strategy.get('sentence_reconstruction_strategy')}
- Localization: {strategy.get('localization_strategy')}

Meaning units:
{bullets(strategy.get('meaning_units', []))}

Structural risks:
{bullets(strategy.get('structural_risks', []))}

Target-language reconstruction notes:
{bullets(strategy.get('turkish_reconstruction_notes', []))}

Target language profile rules:
{bullets(target_rules)}

Translator instructions:
{bullets(strategy.get('translator_instructions', []))}
""".strip()
