import json
import re
from pathlib import Path
from typing import Dict, Optional


def _slug(value: Optional[str], default: str) -> str:
    if not value:
        return default
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower()).strip("_")
    return slug or default


class ScopedGlossaryStore:
    """Stores runtime glossary candidates under an explicit genre/work/user scope."""

    FILE_NAME = "auto_glossary_candidate.json"

    def __init__(self, runtime_dir: Path):
        self.runtime_dir = Path(runtime_dir)

    def scope_key(
        self,
        genre: Optional[str] = None,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        return "__".join(
            [
                f"genre-{_slug(genre, 'general')}",
                f"work-{_slug(work_id, 'none')}",
                f"user-{_slug(user_id, 'shared')}",
            ]
        )

    def path_for(
        self,
        genre: Optional[str] = None,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Path:
        return self.runtime_dir / "glossaries" / self.scope_key(genre, work_id, user_id) / self.FILE_NAME

    def load(
        self,
        genre: Optional[str] = None,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, str]:
        path = self.path_for(genre, work_id, user_id)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def merge(
        self,
        candidates: Dict[str, str],
        genre: Optional[str] = None,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, str]:
        path = self.path_for(genre, work_id, user_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        merged = self.load(genre, work_id, user_id)
        merged.update(candidates or {})

        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        return merged
