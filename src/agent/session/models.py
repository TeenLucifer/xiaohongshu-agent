"""Session models and history behavior."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agent.models import PromptMessage, SessionMessageRole, ToolCallPayload
from agent.time_utils import now_local

TOOL_CONTENT_MAX_LENGTH = 4_000
TOOL_CONTENT_TRUNCATION_SUFFIX = "\n...[truncated]"
RUNTIME_CONTEXT_PREFIX = "[Runtime Context"


class SessionSnapshot(BaseModel):
    """External view of a session."""

    session_id: str
    topic: str | None = None
    workspace_path: Path
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionMessage(BaseModel):
    """Serializable session history entry."""

    role: SessionMessageRole
    content: str
    timestamp: datetime = Field(default_factory=now_local)
    tool_calls: list[ToolCallPayload] = Field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None

    def to_prompt_message(self) -> PromptMessage:
        """Convert the session entry to a prompt message."""

        return PromptMessage(
            role=self.role,
            content=self.content,
            tool_calls=self.tool_calls,
            tool_call_id=self.tool_call_id,
            name=self.name,
        )


class Session(BaseModel):
    """Session working state and short-term history behavior."""

    session_id: str
    topic: str | None = None
    messages: list[SessionMessage] = Field(default_factory=list)
    last_consolidated: int = 0
    workspace_path: Path
    created_at: datetime = Field(default_factory=now_local)
    updated_at: datetime = Field(default_factory=now_local)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def snapshot(self) -> SessionSnapshot:
        """Create a lightweight external snapshot."""

        return SessionSnapshot(
            session_id=self.session_id,
            topic=self.topic,
            workspace_path=self.workspace_path,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata.copy(),
        )

    def add_message(self, message: SessionMessage) -> None:
        """Append a validated message into the session."""

        normalized = message.model_copy(deep=True)
        if normalized.role == "tool":
            normalized.content = _truncate_tool_content(normalized.content)
        elif normalized.role == "user":
            normalized.content = _strip_runtime_context(normalized.content)
        self.messages.append(normalized)
        self.updated_at = now_local()

    def get_history(self, max_messages: int = 500) -> list[PromptMessage]:
        """Return the legal unconsolidated history slice for model input."""

        unconsolidated = self.messages[self.last_consolidated :]
        sliced = unconsolidated[-max_messages:] if max_messages > 0 else unconsolidated
        sliced = _drop_leading_non_user_messages(sliced)
        start = self._find_legal_start(sliced)
        if start:
            sliced = sliced[start:]
        return [message.to_prompt_message() for message in sliced]

    def clear(self) -> None:
        """Clear messages and reset consolidation state."""

        self.messages = []
        self.last_consolidated = 0
        self.updated_at = now_local()

    def mark_consolidated(self, boundary: int) -> None:
        """Advance the consolidation cursor after successful persistence."""

        self.last_consolidated = max(self.last_consolidated, boundary)
        self.updated_at = now_local()

    @staticmethod
    def _find_legal_start(messages: list[SessionMessage]) -> int:
        """Find the first safe index that avoids orphaned tool results."""

        declared: set[str] = set()
        start = 0
        for index, message in enumerate(messages):
            if message.role == "assistant":
                for tool_call in message.tool_calls:
                    if tool_call.id:
                        declared.add(tool_call.id)
            elif message.role == "tool":
                if message.tool_call_id and message.tool_call_id not in declared:
                    start = index + 1
                    declared = set()
                    for previous in messages[start : index + 1]:
                        if previous.role != "assistant":
                            continue
                        for tool_call in previous.tool_calls:
                            if tool_call.id:
                                declared.add(tool_call.id)
        return start


def _strip_runtime_context(content: str) -> str:
    """Remove runtime metadata prefix from persisted user history."""

    if not content.startswith(RUNTIME_CONTEXT_PREFIX):
        return content
    _, separator, remainder = content.partition("\n\n")
    if not separator:
        return content
    return remainder.strip()


def _truncate_tool_content(content: str) -> str:
    """Truncate oversized tool results before persisting them."""

    if len(content) <= TOOL_CONTENT_MAX_LENGTH:
        return content
    allowed_length = TOOL_CONTENT_MAX_LENGTH - len(TOOL_CONTENT_TRUNCATION_SUFFIX)
    return content[:allowed_length] + TOOL_CONTENT_TRUNCATION_SUFFIX


def _drop_leading_non_user_messages(messages: list[SessionMessage]) -> list[SessionMessage]:
    """Prefer to start history from the nearest user turn."""

    for index, message in enumerate(messages):
        if message.role == "user":
            return messages[index:]
    return messages
