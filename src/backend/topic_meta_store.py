"""File-backed topic metadata storage."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from backend.schemas import TopicMetaRecord

logger = logging.getLogger(__name__)


class TopicMetaStore:
    """Persist and load per-topic metadata records."""

    def __init__(self, data_root: Path) -> None:
        self._topics_root = data_root / "topics"

    def get(self, topic_id: str) -> TopicMetaRecord | None:
        path = self.get_record_path(topic_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return TopicMetaRecord.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load topic metadata %s: %s", topic_id, exc)
            return None

    def save(self, record: TopicMetaRecord) -> TopicMetaRecord:
        path = self.get_record_path(record.topic_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def list(self) -> list[TopicMetaRecord]:
        records: list[TopicMetaRecord] = []
        for path in sorted(self._topics_root.glob("*/topic.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                records.append(TopicMetaRecord.model_validate(payload))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to read topic metadata %s: %s", path, exc)
        return sorted(records, key=lambda record: record.updated_at, reverse=True)

    def delete(self, topic_id: str) -> None:
        topic_root = self.get_topic_root(topic_id)
        if topic_root.exists():
            shutil.rmtree(topic_root, ignore_errors=True)

    def get_topic_root(self, topic_id: str) -> Path:
        return self._topics_root / topic_id

    def get_record_path(self, topic_id: str) -> Path:
        return self.get_topic_root(topic_id) / "topic.json"
