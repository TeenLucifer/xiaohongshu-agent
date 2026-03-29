"""HTTP schemas for backend APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from agent.models import ToolCallSummary
from backend.topic_truth_models import PatternSummaryRecord


class TopicSessionRecord(BaseModel):
    """File-backed topic/session mapping record."""

    topic_id: str
    session_id: str
    updated_at: datetime


class TopicMetaRecord(BaseModel):
    """File-backed topic metadata record."""

    topic_id: str
    title: str
    description: str = ""
    created_at: datetime
    updated_at: datetime


class RunRequestBody(BaseModel):
    """Request body for synchronous runs."""

    topic_title: str = Field(min_length=1)
    user_input: str = Field(min_length=1)
    attachments: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResetRequestBody(BaseModel):
    """Request body for reset endpoint."""

    topic_title: str = Field(min_length=1)


class CreateTopicRequestBody(BaseModel):
    """Request body for topic creation."""

    title: str = Field(min_length=1)
    description: str = ""


class MessageResponse(BaseModel):
    """Minimal chat message DTO for the frontend main column."""

    id: str
    role: Literal["user", "agent"]
    text: str
    time: str
    agent_name: str | None = None


class LastRunResponse(BaseModel):
    """Latest run summary returned by the backend."""

    final_text: str
    tool_calls: list[ToolCallSummary] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)


class WorkspaceResponse(BaseModel):
    """Minimal topic workspace payload."""

    topic_id: str
    topic_title: str
    session_id: str
    messages: list[MessageResponse] = Field(default_factory=list)
    updated_at: datetime
    last_run: LastRunResponse | None = None


class RunResponse(BaseModel):
    """Synchronous run payload."""

    topic_id: str
    topic_title: str
    session_id: str
    messages: list[MessageResponse] = Field(default_factory=list)
    last_run: LastRunResponse
    updated_at: datetime


class MessagesResponse(BaseModel):
    """Current session message payload."""

    topic_id: str
    topic_title: str
    session_id: str
    messages: list[MessageResponse] = Field(default_factory=list)
    updated_at: datetime


class ResetResponse(BaseModel):
    """Workspace payload after reset."""

    topic_id: str
    topic_title: str
    session_id: str
    messages: list[MessageResponse] = Field(default_factory=list)
    updated_at: datetime


class ErrorResponse(BaseModel):
    """Minimal API error payload."""

    error_code: str
    message: str
    details: dict[str, Any] | None = None


class TopicListItemResponse(BaseModel):
    """Minimal topic card DTO for topic list and sidebar."""

    topic_id: str
    title: str
    description: str = ""
    session_id: str
    updated_at: datetime


class TopicListResponse(BaseModel):
    """Response payload for listing topics."""

    items: list[TopicListItemResponse] = Field(default_factory=list)


class CreateTopicResponse(BaseModel):
    """Response payload for topic creation."""

    topic_id: str
    title: str
    description: str = ""
    session_id: str
    updated_at: datetime


class DeleteTopicResponse(BaseModel):
    """Response payload for topic deletion."""

    deleted_topic_id: str


class CandidatePostImageResponse(BaseModel):
    """Read-only post image DTO for candidate post detail view."""

    id: str
    imageUrl: str
    alt: str


class CandidatePostContextResponse(BaseModel):
    """Read-only candidate post DTO for the right workspace."""

    id: str
    title: str
    excerpt: str
    bodyText: str
    author: str
    heat: str
    sourceUrl: str
    imageUrl: str
    images: list[CandidatePostImageResponse] = Field(default_factory=list)
    selected: bool
    manualOrder: int | None = None


class PatternSummaryContentResponse(BaseModel):
    """Read-only pattern summary DTO for the right workspace."""

    titlePatterns: list[str] = Field(default_factory=list)
    bodyPatterns: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    @classmethod
    def from_record(cls, record: PatternSummaryRecord) -> PatternSummaryContentResponse:
        return cls(
            titlePatterns=record.title_patterns,
            bodyPatterns=record.body_patterns,
            keywords=record.keywords,
        )


class WorkspaceContextResponse(BaseModel):
    """Read-only right workspace payload for the first 021 integration step."""

    topic_id: str
    topic_title: str
    candidate_posts: list[CandidatePostContextResponse] = Field(default_factory=list)
    pattern_summary: PatternSummaryContentResponse | None = None
    updated_at: datetime
