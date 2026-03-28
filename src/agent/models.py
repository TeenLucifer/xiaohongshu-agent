"""Runtime-level schemas for the agent foundation feature."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

MessageRole = Literal["system", "user", "assistant", "tool"]
SessionMessageRole = Literal["user", "assistant", "tool"]


class ToolCallPayload(BaseModel):
    """Serializable tool-call payload used in session history."""

    id: str | None = None
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class PromptMessage(BaseModel):
    """Minimal prompt/message model used by the runtime foundation."""

    role: MessageRole
    content: str
    tool_calls: list[ToolCallPayload] = Field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


class ToolCallSummary(BaseModel):
    """Lightweight tool-call summary returned to callers."""

    name: str
    arguments_summary: str
    result_summary: str


class RunRequest(BaseModel):
    """Minimal runtime request model."""

    session_id: str
    user_input: str
    attachments: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunResult(BaseModel):
    """Minimal runtime result model."""

    session_id: str
    final_text: str
    tool_calls: list[ToolCallSummary] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
