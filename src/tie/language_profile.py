import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.config import Config


class LanguageProfileLoader:
    """Load data-driven source and target language profiles."""

    LANGUAGE_ALIASES = {
        "english": "en_US",
        "en": "en_US",
        "en-us": "en_US",
        "en_us": "en_US",
        "turkish": "tr_TR",
        "tr": "tr_TR",
        "tr-tr": "tr_TR",
        "tr_tr": "tr_TR",
    }

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = Path(profiles_dir or Config.LANGUAGE_PROFILES_DIR)

    def normalize_code(self, language: Optional[str], default: str) -> str:
        if not language:
            return default
        raw = str(language).strip()
        return self.LANGUAGE_ALIASES.get(raw.casefold(), raw)

    def load_profile(self, language: Optional[str], default: str = "tr_TR") -> Dict[str, Any]:
        code = self.normalize_code(language, default=default)
        profile_path = self.profiles_dir / f"{code}.json"
        if not profile_path.exists():
            return self.safe_default_profile(code)
        try:
            return json.loads(profile_path.read_text(encoding="utf-8"))
        except Exception:
            return self.safe_default_profile(code)

    def load_pair(self, source_language: Optional[str], target_language: Optional[str]) -> Dict[str, Dict[str, Any]]:
        source_code = self.normalize_code(source_language, default="en_US")
        target_code = self.normalize_code(target_language, default="tr_TR")
        return {
            "source_profile": self.load_profile(source_code, default="en_US"),
            "target_profile": self.load_profile(target_code, default="tr_TR"),
        }

    def safe_default_profile(self, code: str) -> Dict[str, Any]:
        return {
            "language_code": code,
            "name": code,
            "default_register": "neutral",
            "core_rules": [],
            "translation_notes": [],
            "translationese_patterns_to_avoid": [],
            "genre_preferences": {},
            "fallback_used": True,
        }
