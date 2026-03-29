"""File-backed topic/session mapping storage."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.schemas import TopicSessionRecord

logger = logging.getLogger(__name__)


class TopicSessionStore:
    """Persist and load the active session for each topic."""

    def __init__(self, data_root: Path) -> None:
        self._topics_root = data_root / "topics"

    def get(self, topic_id: str) -> TopicSessionRecord | None:
        path = self.get_record_path(topic_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return TopicSessionRecord.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load topic mapping %s: %s", topic_id, exc)
            return None

    def save(self, record: TopicSessionRecord) -> TopicSessionRecord:
        path = self.get_record_path(record.topic_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def delete(self, topic_id: str) -> None:
        path = self.get_record_path(topic_id)
        if path.exists():
            path.unlink()
        topic_root = self.get_topic_root(topic_id)
        if topic_root.exists() and not any(topic_root.iterdir()):
            topic_root.rmdir()

    def list(self) -> list[TopicSessionRecord]:
        records: list[TopicSessionRecord] = []
        for path in sorted(self._topics_root.glob("*/session.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                records.append(TopicSessionRecord.model_validate(payload))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load topic mapping from %s: %s", path, exc)
        return sorted(records, key=lambda record: record.updated_at, reverse=True)

    def get_topic_root(self, topic_id: str) -> Path:
        return self._topics_root / topic_id

    def get_record_path(self, topic_id: str) -> Path:
        return self.get_topic_root(topic_id) / "session.json"
