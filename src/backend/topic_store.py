"""File-backed topic/session index storage."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.schemas import TopicSessionRecord

logger = logging.getLogger(__name__)


class TopicSessionStore:
    """Persist and load the current session for each topic."""

    def __init__(self, data_root: Path) -> None:
        self._index_path = data_root / "topic-index.json"

    def get(self, topic_id: str) -> TopicSessionRecord | None:
        return self._load_index().get(topic_id)

    def save(self, record: TopicSessionRecord) -> TopicSessionRecord:
        index = self._load_index()
        index[record.topic_id] = record
        self._write_index(index)
        return record

    def delete(self, topic_id: str) -> None:
        index = self._load_index()
        if topic_id not in index:
            return
        del index[topic_id]
        self._write_index(index)

    def list(self) -> list[TopicSessionRecord]:
        records = list(self._load_index().values())
        return sorted(records, key=lambda record: record.updated_at, reverse=True)

    def get_index_path(self) -> Path:
        return self._index_path

    def _load_index(self) -> dict[str, TopicSessionRecord]:
        if not self._index_path.exists():
            return {}
        try:
            payload = json.loads(self._index_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                logger.warning(
                    "Failed to load topic index %s: payload is not an object",
                    self._index_path,
                )
                return {}
            records: dict[str, TopicSessionRecord] = {}
            for topic_id, value in payload.items():
                if not isinstance(value, dict):
                    logger.warning(
                        "Failed to load topic index entry %s: entry is not an object",
                        topic_id,
                    )
                    continue
                normalized = {"topic_id": topic_id, **value}
                records[topic_id] = TopicSessionRecord.model_validate(normalized)
            return records
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load topic index %s: %s", self._index_path, exc)
            return {}

    def _write_index(self, index: dict[str, TopicSessionRecord]) -> None:
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            topic_id: {
                "session_id": record.session_id,
                "updated_at": record.updated_at,
            }
            for topic_id, record in sorted(index.items())
        }
        self._index_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
