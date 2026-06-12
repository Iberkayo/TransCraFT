import json
import hashlib
from pathlib import Path
from typing import Optional

class TranslationMemory:
    def __init__(self, db_path: str = "data/reference/translation_memory.json"):
        self.db_path = Path(db_path)
        self.memory = {}
        self._load()

    def _load(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception:
                self.memory = {}
        else:
            self.memory = {}

    def _save(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()

    def get_translation(self, source_text: str) -> Optional[str]:
        """Get cached translation if exists."""
        text_hash = self._get_hash(source_text)
        return self.memory.get(text_hash, {}).get("translation")

    def save_translation(self, source_text: str, translated_text: str):
        """Save a new translation to memory."""
        text_hash = self._get_hash(source_text)
        self.memory[text_hash] = {
            "source": source_text.strip(),
            "translation": translated_text.strip()
        }
        self._save()
