"""JSONL persistence for sessions."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from agent.session.models import Session, SessionMessage

logger = logging.getLogger(__name__)


class SessionStorage:
    """Persist sessions as jsonl files under each session workspace."""

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._sessions_root = data_root / "sessions"

    def get_workspace_path(self, session_id: str) -> Path:
        """Return the session workspace directory."""

        return self._sessions_root / session_id

    def get_session_path(self, session_id: str) -> Path:
        """Return the jsonl file path for a session."""

        return self.get_workspace_path(session_id) / "session.jsonl"

    def ensure_workspace_exists(self, session_id: str) -> Path:
        """Ensure the session workspace directory exists."""

        workspace_path = self.get_workspace_path(session_id)
        workspace_path.mkdir(parents=True, exist_ok=True)
        return workspace_path

    def load(self, session_id: str) -> Session | None:
        """Load a session from disk, returning None on failure."""

        path = self.get_session_path(session_id)
        if not path.exists():
            return None

        try:
            with path.open(encoding="utf-8") as handle:
                metadata_line = handle.readline().strip()
                if not metadata_line:
                    return None
                metadata_payload = json.loads(metadata_line)
                if metadata_payload.get("_type") != "metadata":
                    raise ValueError("Invalid metadata line")
                messages = [
                    SessionMessage.model_validate(json.loads(line))
                    for line in handle
                    if line.strip()
                ]
            session = Session(
                session_id=metadata_payload["session_id"],
                topic=metadata_payload.get("topic"),
                messages=messages,
                last_consolidated=metadata_payload.get("last_consolidated", 0),
                workspace_path=self.get_workspace_path(session_id),
                created_at=metadata_payload["created_at"],
                updated_at=metadata_payload["updated_at"],
                metadata=metadata_payload.get("metadata", {}),
            )
            self.ensure_workspace_exists(session_id)
            return session
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load session %s: %s", session_id, exc)
            return None

    def save(self, session: Session) -> None:
        """Rewrite the full session jsonl file."""

        path = self.get_session_path(session.session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata_line = {
            "_type": "metadata",
            "session_id": session.session_id,
            "topic": session.topic,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "last_consolidated": session.last_consolidated,
            "metadata": session.metadata,
        }
        with path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(metadata_line, ensure_ascii=False) + "\n")
            for message in session.messages:
                handle.write(json.dumps(message.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def list_session_paths(self) -> list[Path]:
        """Return all persisted session files."""

        return sorted(self._sessions_root.glob("*/session.jsonl"))
