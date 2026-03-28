"""Session manager for short-term history."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from agent.errors import SessionNotFoundError
from agent.session.models import Session, SessionSnapshot
from agent.session.storage import SessionStorage

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage session lifecycle, caching, and persistence."""

    def __init__(self, data_root: Path, storage: SessionStorage | None = None) -> None:
        self._storage = storage or SessionStorage(data_root)
        self._cache: dict[str, Session] = {}

    def create(
        self,
        topic: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        session_id = str(uuid4())
        workspace_path = self._storage.ensure_workspace_exists(session_id)
        session = Session(
            session_id=session_id,
            topic=topic,
            workspace_path=workspace_path,
            metadata=(metadata or {}).copy(),
        )
        self._cache[session_id] = session
        logger.debug("Created session %s", session_id)
        return session

    def get(self, session_id: str) -> Session | None:
        return self._cache.get(session_id)

    def require(self, session_id: str) -> Session:
        session = self.get(session_id) or self.load(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return session

    def get_or_create(
        self,
        session_id: str,
        *,
        topic: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        cached = self.get(session_id)
        if cached is not None:
            return cached

        loaded = self.load(session_id)
        if loaded is not None:
            return loaded

        session = Session(
            session_id=session_id,
            topic=topic,
            workspace_path=self._storage.ensure_workspace_exists(session_id),
            metadata=(metadata or {}).copy(),
        )
        self._cache[session_id] = session
        return session

    def load(self, session_id: str) -> Session | None:
        session = self._storage.load(session_id)
        if session is None:
            return None
        self._cache[session_id] = session
        return session

    def save(self, session: Session) -> None:
        self._storage.save(session)
        self._cache[session.session_id] = session

    def invalidate(self, session_id: str) -> None:
        self._cache.pop(session_id, None)

    def list_sessions(self) -> list[SessionSnapshot]:
        snapshots: dict[str, SessionSnapshot] = {
            session_id: session.snapshot() for session_id, session in self._cache.items()
        }
        for path in self._storage.list_session_paths():
            session_id = path.parent.name
            if session_id in snapshots:
                continue
            session = self.load(session_id)
            if session is None:
                continue
            snapshots[session_id] = session.snapshot()
        return sorted(snapshots.values(), key=lambda snapshot: snapshot.updated_at, reverse=True)

    def snapshot(self, session_id: str) -> SessionSnapshot:
        session = self.get(session_id) or self.load(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return session.snapshot()
