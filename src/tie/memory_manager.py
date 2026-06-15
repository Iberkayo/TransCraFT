import json
import logging
import datetime
import shutil
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MemoryManager:
    _backup_done = False  # Class variable to ensure we only backup once per process

    def __init__(self, base_dir: Optional[Path] = None, enable_backups: bool = True):
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
        self._enable_backups = enable_backups
         
        # 1. Run backup of existing memory if any (only when backups enabled)
        if self._enable_backups:
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

    def _build_memory_id(self, record: Dict[str, Any]) -> str:
        raw = "|".join([
            str(record.get("scope", "")),
            str(record.get("scope_id", "")),
            str(record.get("type", "")),
            self._normalize_key(record.get("key", "")),
            str(record.get("source_work", "")),
            str(record.get("source_genre", "")),
            str(record.get("source_user", "")),
        ])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _build_provenance(self, record: Dict[str, Any], item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "created_by": item.get("created_by", "memory_curator"),
            "source_work": record.get("source_work"),
            "source_genre": record.get("source_genre"),
            "source_user": record.get("source_user"),
            "source_chunk": item.get("source_chunk"),
            "trace_id": item.get("trace_id"),
        }

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
            "source_user": None,
            "times_loaded": 0,
            "times_injected": 0,
            "times_detected_in_output": 0,
            "estimated_quality_impact_avg": 0.0,
            "harm_score_avg": 0.0,
            "last_effectiveness_decision": None,
            "last_effectiveness_evidence": None,
            "effectiveness_updated_at": None,
            "effectiveness_sample_count": 0,
        }
        
        for k, v in defaults.items():
            if k not in record:
                # Special fallback for confidence if it exists under another key or just missing
                if k == "confidence" and "confidence" in record:
                    pass
                else:
                    record[k] = v
                    changed = True

        if "memory_id" not in record:
            record["memory_id"] = self._build_memory_id(record)
            changed = True

        if "provenance" not in record:
            record["provenance"] = {
                "created_by": record.get("created_by", "unknown"),
                "source_work": record.get("source_work"),
                "source_genre": record.get("source_genre"),
                "source_user": record.get("source_user"),
                "source_chunk": record.get("source_chunk"),
                "trace_id": record.get("trace_id"),
            }
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
        if scope_id:
            record["scope_id"] = scope_id
        record["memory_id"] = item.get("memory_id") or self._build_memory_id(record)
        record["provenance"] = item.get("provenance") or self._build_provenance(record, item)
        if "notes" in item:
            record["notes"] = item["notes"]
        if "reviewer_notes" in item:
            record["reviewer_notes"] = item["reviewer_notes"]

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
        def with_source_path(items: List[Dict[str, Any]], file_path: Path) -> List[Dict[str, Any]]:
            for item in items:
                item.setdefault("_source_path", str(file_path))
            return items

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
                combined.extend(with_source_path(self._load_json(file_path), file_path))
            return combined
        else:
            return []

        return with_source_path(self._load_json(dest_file), dest_file)

    def _memory_data_files(self) -> List[Path]:
        """Return JSON files that contain mutable memory records."""
        files = []
        global_rules = self.global_dir / "rules.json"
        if global_rules.exists():
            files.append(global_rules)
        files.extend(sorted(self.genres_dir.glob("*.json")))
        files.extend(sorted(self.users_dir.glob("*.json")))
        if self.works_dir.exists():
            for work_dir in sorted(p for p in self.works_dir.iterdir() if p.is_dir()):
                files.extend(sorted(work_dir.glob("*.json")))
        return files

    def _update_memory_records(self, memory_ids: List[str], updater) -> int:
        target_ids = {memory_id for memory_id in memory_ids if memory_id}
        if not target_ids:
            return 0

        updated_count = 0
        for file_path in self._memory_data_files():
            items = self._load_json(file_path)
            changed = False
            for item in items:
                if item.get("memory_id") in target_ids:
                    updater(item)
                    item["updated_at"] = datetime.datetime.now().isoformat() + "Z"
                    changed = True
                    updated_count += 1
            if changed:
                self._save_json(file_path, items)
        return updated_count

    def record_memory_loaded(self, memory_ids: List[str]) -> int:
        """Increment load counters for memory records by id."""
        def updater(item: Dict[str, Any]):
            item["times_loaded"] = int(item.get("times_loaded", 0) or 0) + 1

        return self._update_memory_records(memory_ids, updater)

    def record_memory_injected(self, memory_ids: List[str]) -> int:
        """Increment prompt-injection counters for memory records by id."""
        def updater(item: Dict[str, Any]):
            item["times_injected"] = int(item.get("times_injected", 0) or 0) + 1

        return self._update_memory_records(memory_ids, updater)

    def update_memory_effectiveness(self, effectiveness_records: List[Dict[str, Any]]) -> int:
        """Persist item-level memory effectiveness metrics back into memory metadata."""
        records_by_id = {
            record.get("memory_id"): record
            for record in effectiveness_records
            if record.get("memory_id")
        }

        def updater(item: Dict[str, Any]):
            record = records_by_id.get(item.get("memory_id"), {})
            sample_count = int(item.get("effectiveness_sample_count", 0) or 0)
            new_count = sample_count + 1
            impact = float(record.get("estimated_quality_impact", 0.0) or 0.0)
            harm = float(record.get("harm_score", 0.0) or 0.0)
            old_impact = float(item.get("estimated_quality_impact_avg", 0.0) or 0.0)
            old_harm = float(item.get("harm_score_avg", 0.0) or 0.0)

            if record.get("detected_in_output"):
                item["times_detected_in_output"] = int(item.get("times_detected_in_output", 0) or 0) + 1
            item["estimated_quality_impact_avg"] = ((old_impact * sample_count) + impact) / new_count
            item["harm_score_avg"] = ((old_harm * sample_count) + harm) / new_count
            item["last_effectiveness_decision"] = record.get("decision")
            item["last_effectiveness_evidence"] = record.get("evidence")
            item["effectiveness_updated_at"] = datetime.datetime.now().isoformat() + "Z"
            item["effectiveness_sample_count"] = new_count

        return self._update_memory_records(list(records_by_id.keys()), updater)

    def all_memory_items(self) -> List[Dict[str, Any]]:
        """Return all mutable memory records across global, genre, user, and work scopes."""
        items: List[Dict[str, Any]] = []
        for file_path in self._memory_data_files():
            for item in self._load_json(file_path):
                item.setdefault("_source_path", str(file_path))
                items.append(item)
        return items

    def get_low_value_memories(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return memories with low detected usage and low estimated impact."""
        items = self.all_memory_items()
        return sorted(
            items,
            key=lambda item: (
                float(item.get("estimated_quality_impact_avg", 0.0) or 0.0),
                int(item.get("times_detected_in_output", 0) or 0),
                -float(item.get("harm_score_avg", 0.0) or 0.0),
            ),
        )[:limit]

    def get_high_value_memories(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return memories with high estimated impact and repeated detected usage."""
        items = self.all_memory_items()
        return sorted(
            items,
            key=lambda item: (
                float(item.get("estimated_quality_impact_avg", 0.0) or 0.0),
                int(item.get("times_detected_in_output", 0) or 0),
                -float(item.get("harm_score_avg", 0.0) or 0.0),
            ),
            reverse=True,
        )[:limit]

    def build_effectiveness_records(self) -> List[Dict[str, Any]]:
        """Convert persisted memory metadata into report-compatible effectiveness records."""
        records = []
        for item in self.all_memory_items():
            detected = int(item.get("times_detected_in_output", 0) or 0) > 0
            records.append(
                {
                    "memory_id": item.get("memory_id"),
                    "key": item.get("key"),
                    "type": item.get("type"),
                    "scope": item.get("scope"),
                    "loaded": int(item.get("times_loaded", 0) or 0) > 0,
                    "injected": int(item.get("times_injected", 0) or 0) > 0,
                    "detected_in_output": detected,
                    "relevance_score": 0.0,
                    "usage_score": (
                        int(item.get("times_detected_in_output", 0) or 0)
                        / max(1, int(item.get("effectiveness_sample_count", 0) or 0))
                    ),
                    "estimated_quality_impact": float(item.get("estimated_quality_impact_avg", 0.0) or 0.0),
                    "harm_score": float(item.get("harm_score_avg", 0.0) or 0.0),
                    "decision": item.get("last_effectiveness_decision") or "review",
                    "evidence": item.get("last_effectiveness_evidence") or "",
                    "source_work": item.get("source_work"),
                    "source_genre": item.get("source_genre"),
                }
            )
        return records

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
