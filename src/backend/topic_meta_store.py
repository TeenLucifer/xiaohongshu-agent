"""Session-scoped topic metadata storage."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.schemas import TopicMetaRecord

logger = logging.getLogger(__name__)


class TopicMetaStore:
    """Persist and load topic metadata inside session directories."""

    def __init__(self, data_root: Path) -> None:
        self._sessions_root = data_root / "sessions"

    def get(self, session_id: str) -> TopicMetaRecord | None:
        path = self.get_record_path(session_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return TopicMetaRecord.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load topic metadata for session %s: %s", session_id, exc)
            return None

    def save(self, session_id: str, record: TopicMetaRecord) -> TopicMetaRecord:
        path = self.get_record_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def delete(self, session_id: str) -> None:
        path = self.get_record_path(session_id)
        if path.exists():
            path.unlink()

    def get_session_root(self, session_id: str) -> Path:
        return self._sessions_root / session_id

    def get_record_path(self, session_id: str) -> Path:
        return self.get_session_root(session_id) / "topic.json"
