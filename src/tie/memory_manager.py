import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            # Try to resolve relative to this file
            self.base_dir = Path(__file__).resolve().parent.parent.parent / "memory"
        else:
            self.base_dir = Path(base_dir)
            
        self.global_dir = self.base_dir / "global"
        self.genres_dir = self.base_dir / "genres"
        self.works_dir = self.base_dir / "works"
        self.users_dir = self.base_dir / "users"
        
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required memory directory structure exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.global_dir.mkdir(parents=True, exist_ok=True)
        self.genres_dir.mkdir(parents=True, exist_ok=True)
        self.works_dir.mkdir(parents=True, exist_ok=True)
        self.users_dir.mkdir(parents=True, exist_ok=True)

    def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSON file safely, return empty list if not found or invalid."""
        if not file_path.exists():
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        except Exception as e:
            logger.warning(f"Error loading memory file {file_path}: {e}")
            return []

    def _save_json(self, file_path: Path, data: Any):
        """Save data to JSON file safely."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory file {file_path}: {e}")

    def add_memory_item(self, scope: str, item: Dict[str, Any], scope_id: Optional[str] = None):
        """
        Add a single memory item to the specified scope.
        Prevents duplicate entries by matching on 'key' and 'type'.
        
        item structure:
        {
            "key": "...",
            "value": "..." or {...},
            "type": "...",
            "confidence": 0.0 - 1.0,
            "notes": "..."
        }
        """
        # Validate required fields
        for field in ["key", "type", "value"]:
            if field not in item:
                raise ValueError(f"Memory item must contain '{field}' field.")

        confidence = item.get("confidence", 1.0)
        
        # Determine destination path based on scope
        if scope == "global":
            dest_file = self.global_dir / "rules.json"
        elif scope == "genre":
            if not scope_id:
                raise ValueError("genre name/id must be provided as scope_id for genre scope")
            dest_file = self.genres_dir / f"{scope_id}.json"
        elif scope == "user":
            if not scope_id:
                raise ValueError("user_id must be provided as scope_id for user scope")
            dest_file = self.users_dir / f"{scope_id}.json"
        elif scope == "work":
            if not scope_id:
                raise ValueError("work_id must be provided as scope_id for work scope")
            # Decide file based on item type
            item_type = item["type"]
            work_folder = self.works_dir / scope_id
            work_folder.mkdir(parents=True, exist_ok=True)
            
            if item_type == "character_info":
                dest_file = work_folder / "characters.json"
            elif item_type == "terminology" or item_type == "glossary":
                dest_file = work_folder / "glossary.json"
            elif item_type == "style_rule":
                # Style rule in work memory can go to glossary/rules, but let's put it in glossary or a separate rules file
                dest_file = work_folder / "glossary.json"
            else:
                dest_file = work_folder / "glossary.json"
        else:
            raise ValueError(f"Unknown scope: {scope}")

        # Load existing items
        items = self._load_json(dest_file)
        
        # Check for duplicate: match by 'key' and 'type' (case-insensitive key comparison)
        duplicate_index = -1
        for idx, existing in enumerate(items):
            if existing.get("type") == item["type"] and str(existing.get("key")).strip().lower() == str(item["key"]).strip().lower():
                duplicate_index = idx
                break
                
        # Format item record
        record = {
            "key": item["key"],
            "value": item["value"],
            "type": item["type"],
            "confidence": confidence,
            "scope": scope
        }
        if "notes" in item:
            record["notes"] = item["notes"]
        if scope_id:
            record["scope_id"] = scope_id

        if duplicate_index >= 0:
            # Overwrite/update if new confidence is higher or equal, or just update to keep fresh
            items[duplicate_index] = record
            logger.info(f"Updated existing memory item in {scope}/{scope_id}: {item['key']}")
        else:
            items.append(record)
            logger.info(f"Added new memory item to {scope}/{scope_id}: {item['key']}")
            
        self._save_json(dest_file, items)

    def get_memory_items(self, scope: str, scope_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve memory items for a specific scope."""
        if scope == "global":
            dest_file = self.global_dir / "rules.json"
        elif scope == "genre":
            if not scope_id:
                return []
            dest_file = self.genres_dir / f"{scope_id}.json"
        elif scope == "user":
            if not scope_id:
                return []
            dest_file = self.users_dir / f"{scope_id}.json"
        elif scope == "work":
            if not scope_id:
                return []
            work_folder = self.works_dir / scope_id
            if not work_folder.exists():
                return []
            # Gather all JSON files in work folder
            combined = []
            for file_path in work_folder.glob("*.json"):
                combined.extend(self._load_json(file_path))
            return combined
        else:
            return []

        return self._load_json(dest_file)

    def write_style_profile(self, work_id: str, markdown_content: str):
        """Write custom markdown style profile for a work."""
        work_folder = self.works_dir / work_id
        work_folder.mkdir(parents=True, exist_ok=True)
        profile_path = work_folder / "style_profile.md"
        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        except Exception as e:
            logger.error(f"Error saving style profile for {work_id}: {e}")

    def read_style_profile(self, work_id: str) -> Optional[str]:
        """Read custom markdown style profile for a work."""
        profile_path = self.works_dir / work_id / "style_profile.md"
        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error reading style profile for {work_id}: {e}")
        return None
