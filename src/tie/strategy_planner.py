import re
from typing import Any, Dict, List, Optional

from src.core.config import Config
from src.tie.language_profile import LanguageProfileLoader


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
        meaning_units = self._meaning_units(source_text)
        structural_risks = self._structural_risks(source_text, target_profile)
        target_rules = self._target_rules(target_profile, genre)
        reconstruction_notes = self._reconstruction_notes(genre, target_profile, style_contract)
        translator_instructions = self._translator_instructions(genre, memory_context, work_id)
        critic_checklist = self._critic_checklist(genre)

        return {
            "source_language": source_profile.get("language_code", "en_US"),
            "target_language": target_profile.get("language_code", "tr_TR"),
            "text_type": text_type,
            "tone": tone,
            "register": register,
            "audience": "general Turkish readers" if text_type != "technical" else "technical Turkish readers",
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

    def _meaning_units(self, source_text: str) -> List[str]:
        chunks = [s.strip() for s in re.split(r"(?<=[.!?;:])\s+", source_text or "") if s.strip()]
        if not chunks and source_text:
            chunks = [source_text.strip()]
        return [self._compact(unit) for unit in chunks[:6]]

    def _structural_risks(self, source_text: str, target_profile: Dict[str, Any]) -> List[str]:
        risks = []
        if len(source_text.split()) > 35:
            risks.append("Long English sentence may need splitting for Turkish readability.")
        if re.search(r"\b(which|that|who|whose|where)\b", source_text or "", re.IGNORECASE):
            risks.append("English relative clause may create heavy Turkish participle structures.")
        if re.search(r"\bof\b.+\bof\b", source_text or "", re.IGNORECASE):
            risks.append("English noun/preposition stack may need unpacking.")
        if "translationese_patterns_to_avoid" in target_profile:
            risks.append("Check for Turkish translationese patterns listed in the target profile.")
        return risks[:6]

    def _target_rules(self, target_profile: Dict[str, Any], genre: str) -> List[str]:
        rules = list(target_profile.get("core_rules", []))[:8]
        genre_rules = target_profile.get("genre_preferences", {}).get((genre or "general"), [])
        return (rules + genre_rules)[:10]

    def _reconstruction_notes(
        self,
        genre: str,
        target_profile: Dict[str, Any],
        style_contract: Optional[Dict[str, Any]],
    ) -> List[str]:
        notes = [
            "avoid literal English word order",
            "drop unnecessary pronouns when Turkish morphology or context is enough",
            "reconstruct meaning naturally in Turkish before final wording",
        ]
        if self._text_type(genre) == "literary_fiction":
            notes.append("preserve sparse rhythm and intentional fragments when style requires it")
        if self._text_type(genre) in {"technical", "academic"}:
            notes.append("prioritize terminology consistency and clear claims")
        if style_contract:
            notes.append("follow style contract tone and sentence rhythm")
        notes.extend(target_profile.get("translation_notes", [])[:3])
        return notes[:10]

    def _translator_instructions(self, genre: str, memory_context: Optional[str], work_id: Optional[str]) -> List[str]:
        instructions = [
            "preserve full meaning before polishing style",
            "translate by meaning units, not word by word",
            "avoid translationese and unnecessary pronoun repetition",
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
        return instructions

    def _critic_checklist(self, genre: str) -> List[str]:
        checklist = [
            "meaning preserved",
            "Turkish naturalness",
            "unnecessary pronouns avoided",
            "translationese patterns avoided",
            "long relative clause chains avoided",
            "register consistency",
            "terminology consistency",
        ]
        if self._text_type(genre) == "literary_fiction":
            checklist.append("style and rhythm preservation")
        return checklist

    def _sentence_strategy(self, genre: str) -> str:
        if self._text_type(genre) == "literary_fiction":
            return "Reconstruct sentences for natural Turkish while preserving intentional fragments and rhythm."
        if self._text_type(genre) in {"technical", "academic"}:
            return "Prefer clear Turkish academic sentence boundaries; split long English sentences when helpful."
        return "Prefer natural Turkish sentence rhythm over literal English syntax."

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
            "audience": "general Turkish readers",
            "literalness_level": "medium_low",
            "sentence_reconstruction_strategy": "Prefer natural Turkish reconstruction.",
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


def build_strategy_prompt_context(strategy: Optional[Dict[str, Any]], language_profile: Optional[Dict[str, Any]]) -> str:
    if not strategy:
        return ""

    def bullets(items: List[Any]) -> str:
        return "\n".join(f"- {item}" for item in items if item)

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

Turkish reconstruction notes:
{bullets(strategy.get('turkish_reconstruction_notes', []))}

Target language profile rules:
{bullets(target_rules)}

Translator instructions:
{bullets(strategy.get('translator_instructions', []))}
""".strip()
