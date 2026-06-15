import json
import logging
import datetime
import shutil
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MemoryManager:
    _backup_done = False  # Class variable to ensure we only backup once per process

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            # Resolve relative to project root
            self.base_dir = Path(__file__).resolve().parent.parent.parent / "memory"
        else:
            self.base_dir = Path(base_dir)
            
        self.global_dir = self.base_dir / "global"
        self.genres_dir = self.base_dir / "genres"
        self.works_dir = self.base_dir / "works"
        self.users_dir = self.base_dir / "users"
        self.pending_dir = self.base_dir / "pending"
        self.pending_file = self.pending_dir / "pending_memory.jsonl"
        
        # 1. Run backup of existing memory if any
        self._backup_existing_memory()
        
        # 2. Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required memory directory structure exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.global_dir.mkdir(parents=True, exist_ok=True)
        self.genres_dir.mkdir(parents=True, exist_ok=True)
        self.works_dir.mkdir(parents=True, exist_ok=True)
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def _backup_existing_memory(self):
        """Backup the current memory directory if it exists and has content, before any modifications."""
        if self.base_dir.exists() and any(self.base_dir.iterdir()):
            if not MemoryManager._backup_done:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # Do not backup if the base_dir is inside a temp path (e.g. during pytest)
                if "pytest" in str(self.base_dir) or "tmp" in str(self.base_dir).lower():
                    MemoryManager._backup_done = True
                    return
                backup_dir = self.base_dir.parent / f"memory_backup_{timestamp}"
                try:
                    shutil.copytree(self.base_dir, backup_dir)
                    logger.info(f"Created memory backup at {backup_dir}")
                    print(f"Created memory backup at {backup_dir}")
                    MemoryManager._backup_done = True
                except Exception as e:
                    logger.error(f"Failed to create memory backup: {e}")

    def _normalize_key(self, key: str) -> str:
        """Normalize key by removing all non-alphanumeric characters and lowercasing."""
        return re.sub(r'[^a-zA-Z0-9]', '', str(key).lower().strip())

    def _migrate_record(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Migrate a record to include all TIE v0.2 metadata. Returns (migrated_record, was_changed)."""
        changed = False
        now_str = datetime.datetime.now().isoformat() + "Z"
        
        # Map of required fields and default values
        defaults = {
            "importance_score": 0.5,
            "usage_count": 1,
            "status": "active",
            "confidence": 0.7,
            "created_at": now_str,
            "updated_at": now_str,
            "source_work": None,
            "source_genre": None,
            "source_user": None
        }
        
        for k, v in defaults.items():
            if k not in record:
                # Special fallback for confidence if it exists under another key or just missing
                if k == "confidence" and "confidence" in record:
                    pass
                else:
                    record[k] = v
                    changed = True
                    
        return record, changed

    def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSON file safely and perform schema migration on items."""
        if not file_path.exists():
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            
            # Run schema migration
            migrated_items = []
            file_changed = False
            for item in items:
                migrated, changed = self._migrate_record(item)
                migrated_items.append(migrated)
                if changed:
                    file_changed = True
                    
            if file_changed:
                self._save_json(file_path, migrated_items)
                
            return migrated_items
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

    def add_memory_item(self, 
                        scope: str, 
                        item: Dict[str, Any], 
                        scope_id: Optional[str] = None,
                        work_id: Optional[str] = None,
                        genre: Optional[str] = None,
                        user_id: Optional[str] = None):
        """
        Add a single memory item to the specified scope.
        Applies TIE v0.2 schema and advanced deduplication/merge logic.
        """
        # Validate required fields
        for field in ["key", "type", "value"]:
            if field not in item:
                raise ValueError(f"Memory item must contain '{field}' field.")

        status = item.get("status", "active")
        now_str = datetime.datetime.now().isoformat() + "Z"
        
        # Build complete record conforming to TIE v0.2 schema
        record = {
            "key": item["key"],
            "value": item["value"],
            "type": item["type"],
            "scope": scope,
            "confidence": min(1.0, max(0.0, item.get("confidence", 0.7))),
            "importance_score": min(1.0, max(0.0, item.get("importance_score", 0.5))),
            "usage_count": item.get("usage_count", 1),
            "created_at": item.get("created_at", now_str),
            "updated_at": now_str,
            "source_work": work_id or item.get("source_work"),
            "source_genre": genre or item.get("source_genre"),
            "source_user": user_id or item.get("source_user"),
            "status": status
        }
        if "notes" in item:
            record["notes"] = item["notes"]
        if "reviewer_notes" in item:
            record["reviewer_notes"] = item["reviewer_notes"]
        if scope_id:
            record["scope_id"] = scope_id

        # If status is pending, store in the pending memory JSONL file
        if status == "pending":
            self._save_pending_item(record)
            return

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
            item_type = item["type"]
            work_folder = self.works_dir / scope_id
            work_folder.mkdir(parents=True, exist_ok=True)
            
            if item_type == "character_info":
                dest_file = work_folder / "characters.json"
            else:
                dest_file = work_folder / "glossary.json"
        else:
            raise ValueError(f"Unknown scope: {scope}")

        # Load existing items
        items = self._load_json(dest_file)
        
        # Advanced Deduplication: check normalized_key, type, scope, source_genre, source_work
        norm_key = self._normalize_key(record["key"])
        duplicate_index = -1
        
        for idx, existing in enumerate(items):
            if (existing.get("type") == record["type"] and 
                existing.get("scope") == record["scope"] and
                existing.get("source_work") == record["source_work"] and
                existing.get("source_genre") == record["source_genre"] and
                self._normalize_key(existing.get("key", "")) == norm_key):
                duplicate_index = idx
                break

        if duplicate_index >= 0:
            # Merge duplicate record
            existing = items[duplicate_index]
            existing["usage_count"] += 1
            existing["updated_at"] = now_str
            existing["confidence"] = max(existing["confidence"], record["confidence"])
            existing["importance_score"] = max(existing["importance_score"], record["importance_score"])
            
            # Value merge: if dictionary, update keys, else overwrite
            if isinstance(existing["value"], dict) and isinstance(record["value"], dict):
                existing["value"].update(record["value"])
            else:
                existing["value"] = record["value"]
                
            if "notes" in record:
                existing["notes"] = record["notes"]
            if "reviewer_notes" in record:
                existing["reviewer_notes"] = record["reviewer_notes"]
                
            logger.info(f"Merged duplicate memory item in {scope}/{scope_id}: {record['key']}")
        else:
            items.append(record)
            logger.info(f"Added new memory item to {scope}/{scope_id}: {record['key']}")
            
        self._save_json(dest_file, items)

    def _save_pending_item(self, record: Dict[str, Any]):
        """Save a pending candidate to memory/pending/pending_memory.jsonl with dedup."""
        self.pending_file.parent.mkdir(parents=True, exist_ok=True)
        existing_lines = []
        
        if self.pending_file.exists():
            try:
                with open(self.pending_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            existing_lines.append(json.loads(line.strip()))
            except Exception as e:
                logger.warning(f"Error loading pending JSONL file: {e}")
                
        # Check for duplicate in pending items
        norm_key = self._normalize_key(record["key"])
        duplicate_idx = -1
        for idx, item in enumerate(existing_lines):
            if (item.get("type") == record["type"] and 
                item.get("scope") == record["scope"] and
                item.get("source_work") == record["source_work"] and
                item.get("source_genre") == record["source_genre"] and
                self._normalize_key(item.get("key", "")) == norm_key):
                duplicate_idx = idx
                break

        if duplicate_idx >= 0:
            existing = existing_lines[duplicate_idx]
            existing["usage_count"] += 1
            existing["updated_at"] = record["updated_at"]
            existing["confidence"] = max(existing["confidence"], record["confidence"])
            existing["importance_score"] = max(existing["importance_score"], record["importance_score"])
            if isinstance(existing["value"], dict) and isinstance(record["value"], dict):
                existing["value"].update(record["value"])
            else:
                existing["value"] = record["value"]
        else:
            existing_lines.append(record)
            
        try:
            with open(self.pending_file, "w", encoding="utf-8") as f:
                for item in existing_lines:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            logger.info(f"Saved pending memory item: {record['key']}")
        except Exception as e:
            logger.error(f"Error writing to pending JSONL file: {e}")

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
