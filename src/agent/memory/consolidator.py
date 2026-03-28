"""Memory consolidation policy and orchestration."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel, ValidationError, field_validator

from agent.memory.store import MemoryStore
from agent.session.models import Session, SessionMessage

logger = logging.getLogger(__name__)


class MemoryConsolidationResult(BaseModel):
    """Structured output from the memory consolidation agent."""

    history_entry: str
    memory_update: str

    @field_validator("history_entry")
    @classmethod
    def validate_history_entry(cls, value: str) -> str:
        """Require the nanobot-style timestamp prefix."""

        if not value.startswith("[") or "]" not in value:
            raise ValueError("history_entry must start with [YYYY-MM-DD HH:MM]")
        return value


class MemoryConsolidationAgent(Protocol):
    """Protocol for the independent memory consolidation agent."""

    def consolidate(
        self,
        *,
        current_memory: str,
        messages_text: str,
    ) -> MemoryConsolidationResult | dict[str, object] | None:
        """Return a structured memory consolidation result."""


def estimate_message_tokens(message: SessionMessage) -> int:
    """Heuristic token estimate for one message."""

    return max(1, len(message.content) // 4 + 8)


def estimate_session_tokens(session: Session) -> int:
    """Heuristic token estimate for the current session history view."""

    return sum(estimate_message_tokens(message) for message in session.messages)


class MemoryConsolidator:
    """Owns token-budget memory consolidation policy."""

    _MAX_CONSOLIDATION_ROUNDS = 5
    _SAFETY_BUFFER = 1024

    def __init__(
        self,
        *,
        store: MemoryStore,
        agent: MemoryConsolidationAgent,
        context_window_tokens: int,
        max_completion_tokens: int = 4096,
    ) -> None:
        self.store = store
        self.agent = agent
        self.context_window_tokens = context_window_tokens
        self.max_completion_tokens = max_completion_tokens

    @property
    def budget(self) -> int:
        """Effective budget for prompt-side tokens."""

        return self.context_window_tokens - self.max_completion_tokens - self._SAFETY_BUFFER

    @property
    def target(self) -> int:
        """Compression target after consolidation."""

        return self.budget // 2

    def pick_consolidation_boundary(
        self,
        session: Session,
        tokens_to_remove: int,
    ) -> tuple[int, int] | None:
        """Pick a user-turn boundary that removes enough old prompt tokens."""

        start = session.last_consolidated
        if start >= len(session.messages) or tokens_to_remove <= 0:
            return None

        removed_tokens = 0
        last_boundary: tuple[int, int] | None = None
        for index in range(start, len(session.messages)):
            message = session.messages[index]
            if index > start and message.role == "user":
                last_boundary = (index, removed_tokens)
                if removed_tokens >= tokens_to_remove:
                    return last_boundary
            removed_tokens += estimate_message_tokens(message)
        return last_boundary

    def maybe_consolidate_by_tokens(self, session: Session) -> bool:
        """Consolidate older unconsolidated messages until the budget is safe."""

        if not session.messages or self.context_window_tokens <= 0:
            return False

        estimated = estimate_session_tokens(session)
        if estimated < self.budget:
            return False

        changed = False
        for _ in range(self._MAX_CONSOLIDATION_ROUNDS):
            if estimated <= self.target:
                return changed

            boundary = self.pick_consolidation_boundary(
                session=session,
                tokens_to_remove=max(1, estimated - self.target),
            )
            if boundary is None:
                return changed

            end_index = boundary[0]
            chunk = session.messages[session.last_consolidated : end_index]
            if not chunk:
                return changed

            if not self._consolidate_chunk(session=session, chunk=chunk, end_index=end_index):
                return changed

            changed = True
            estimated = estimate_session_tokens(session)
        return changed

    def run_pre_check(self, session: Session) -> bool:
        """Run the pre-run consolidation check."""

        return self.maybe_consolidate_by_tokens(session)

    def schedule_post_check(
        self,
        session: Session,
        on_complete: Callable[[bool], None] | None = None,
    ) -> threading.Thread:
        """Run a post-run consolidation check in a background thread."""

        def runner() -> None:
            changed = self.maybe_consolidate_by_tokens(session)
            if on_complete is not None:
                on_complete(changed)

        thread = threading.Thread(
            target=runner,
            name=f"memory-post-{session.session_id}",
            daemon=True,
        )
        thread.start()
        return thread

    def _consolidate_chunk(
        self,
        *,
        session: Session,
        chunk: list[SessionMessage],
        end_index: int,
    ) -> bool:
        """Consolidate one selected chunk and advance the cursor on success."""

        messages_text = self.store.format_messages(chunk)
        current_memory = self.store.read_long_term()
        try:
            raw_result = self.agent.consolidate(
                current_memory=current_memory,
                messages_text=messages_text,
            )
            if raw_result is None:
                logger.warning("Memory consolidation returned no result")
                self.store.mark_failure_or_raw_archive(chunk)
                return False

            result = (
                raw_result
                if isinstance(raw_result, MemoryConsolidationResult)
                else MemoryConsolidationResult.model_validate(raw_result)
            )
        except (ValidationError, ValueError) as exc:
            logger.warning("Memory consolidation returned invalid payload: %s", exc)
            self.store.mark_failure_or_raw_archive(chunk)
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("Memory consolidation failed: %s", exc)
            self.store.mark_failure_or_raw_archive(chunk)
            return False

        entry = self.store.normalize_text(result.history_entry).strip()
        update = self.store.normalize_text(result.memory_update)
        if not entry:
            logger.warning("Memory consolidation returned empty history entry")
            self.store.mark_failure_or_raw_archive(chunk)
            return False

        self.store.append_history(entry)
        if update != current_memory:
            self.store.write_long_term(update)
        self.store.mark_success()
        session.mark_consolidated(end_index)
        return True
