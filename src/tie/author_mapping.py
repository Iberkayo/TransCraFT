import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.config import Config

logger = logging.getLogger(__name__)


def _normalize_work_id(work_id: str) -> str:
    return work_id.lower().strip().replace(" ", "_")


def load_author_mapping(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    mapping_path = path or Config.AUTHOR_MAPPING_PATH
    if not mapping_path.exists():
        logger.warning(f"Author mapping config not found: {mapping_path}")
        return {}

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"Could not load author mapping config {mapping_path}: {e}")
        return {}

    if not isinstance(data, dict):
        logger.warning(f"Author mapping config must be a JSON object: {mapping_path}")
        return {}

    return {_normalize_work_id(key): value for key, value in data.items() if isinstance(value, dict)}


def resolve_author_for_work(work_id: Optional[str]) -> Optional[Dict[str, str]]:
    if not work_id:
        return None

    work_key = _normalize_work_id(work_id)
    author_info = load_author_mapping().get(work_key)
    if not author_info:
        return None

    author_id = str(author_info.get("author_id") or "").strip()
    if not author_id:
        return None

    return {
        "work_key": work_key,
        "author_id": author_id,
        "author_name": str(author_info.get("author_name") or author_id.replace("_", " ").title()),
    }
