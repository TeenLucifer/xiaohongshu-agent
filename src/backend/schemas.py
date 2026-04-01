"""HTTP schemas for backend APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

from agent.models import ToolCallSummary
from backend.topic_truth_models import (
    CopyDraftRecord,
    EditorImageRecord,
    GeneratedImageResultRecord,
    PatternSummaryRecord,
)


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


class StreamingRunEvent(BaseModel):
    """SSE event envelope for streaming runs."""

    type: Literal[
        "run_started",
        "tool_call_started",
        "tool_call_finished",
        "assistant_delta",
        "run_completed",
        "run_failed",
    ]
    run_id: str
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class ResetRequestBody(BaseModel):
    """Request body for reset endpoint."""

    topic_title: str = Field(min_length=1)


class CreateTopicRequestBody(BaseModel):
    """Request body for topic creation."""

    title: str = Field(min_length=1)
    description: str = ""


class UpdateSelectedPostsRequestBody(BaseModel):
    """Request body for persisting selected post ids and order."""

    topic_title: str = Field(min_length=1)
    post_ids: list[str] = Field(default_factory=list)


class UpdateEditorImageItemRequestBody(BaseModel):
    """One editor image item written back from frontend."""

    id: str
    order: int
    source_type: Literal["material", "generated"] = Field(
        validation_alias=AliasChoices("source_type", "sourceType")
    )
    source_post_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("source_post_id", "sourcePostId"),
    )
    source_image_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("source_image_id", "sourceImageId"),
    )
    source_generated_image_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("source_generated_image_id", "sourceGeneratedImageId"),
    )
    image_path: str = Field(validation_alias=AliasChoices("image_path", "imagePath"))
    alt: str


class UpdateEditorImagesRequestBody(BaseModel):
    """Request body for persisting editor-area images."""

    topic_title: str = Field(
        min_length=1,
        validation_alias=AliasChoices("topic_title", "topicTitle"),
    )
    items: list[UpdateEditorImageItemRequestBody] = Field(default_factory=list)


class UpdateCopyDraftRequestBody(BaseModel):
    """Request body for persisting copy draft edits."""

    topic_title: str = Field(
        min_length=1,
        validation_alias=AliasChoices("topic_title", "topicTitle"),
    )
    title: str = ""
    body: str = ""


class MessageImageAttachmentResponse(BaseModel):
    """Lightweight image attachment rendered below final answer."""

    image_url: str
    alt: str


class MessageResponse(BaseModel):
    """Minimal chat message DTO for the frontend main column."""

    id: str
    role: Literal["user", "agent"]
    text: str
    time: str
    agent_name: str | None = None
    tool_summary: list[ToolCallSummary] = Field(default_factory=list)
    image_attachments: list[MessageImageAttachmentResponse] = Field(default_factory=list)


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
    trace_file: str | None = None


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


class SkillListItemResponse(BaseModel):
    """Read-only skill DTO for the skills page."""

    name: str
    description: str
    source: str
    location: str
    available: bool
    requires: list[str] = Field(default_factory=list)
    content_summary: str = ""


class SkillsListResponse(BaseModel):
    """Response payload for listing all available and unavailable skills."""

    items: list[SkillListItemResponse] = Field(default_factory=list)


class CandidatePostImageResponse(BaseModel):
    """Read-only post image DTO for candidate post detail view."""

    id: str
    imageUrl: str
    imagePath: str
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
    imagePatterns: list[str] = Field(default_factory=list)
    imageQualityNotes: str | None = None
    summaryText: str | None = None

    @classmethod
    def from_record(cls, record: PatternSummaryRecord) -> PatternSummaryContentResponse:
        return cls(
            titlePatterns=record.title_patterns,
            bodyPatterns=record.body_patterns,
            keywords=record.keywords,
            imagePatterns=record.image_patterns,
            imageQualityNotes=record.image_quality_notes,
            summaryText=record.summary_text,
        )


class CopyDraftContentResponse(BaseModel):
    """Read-only copy draft DTO for the right workspace."""

    title: str
    body: str

    @classmethod
    def from_record(cls, record: CopyDraftRecord) -> CopyDraftContentResponse:
        return cls(title=record.title, body=record.body)


class CopyDraftResponse(BaseModel):
    """Persisted copy draft DTO."""

    topic_id: str
    topic_title: str
    copy_draft: CopyDraftContentResponse
    updated_at: datetime


class EditorImageResponse(BaseModel):
    """Read-only editor image DTO."""

    id: str
    order: int
    sourceType: Literal["material", "generated"]
    sourcePostId: str | None = None
    sourceImageId: str | None = None
    sourceGeneratedImageId: str | None = None
    imageUrl: str
    imagePath: str
    alt: str

    @classmethod
    def from_record(
        cls,
        record: EditorImageRecord,
        *,
        image_url: str,
    ) -> EditorImageResponse:
        return cls(
            id=record.id,
            order=record.order,
            sourceType=record.source_type,
            sourcePostId=record.source_post_id,
            sourceImageId=record.source_image_id,
            sourceGeneratedImageId=record.source_generated_image_id,
            imageUrl=image_url,
            imagePath=record.image_path,
            alt=record.alt,
        )


class GeneratedImageResultResponse(BaseModel):
    """Read-only generated image result DTO."""

    id: str
    imageUrl: str
    imagePath: str
    alt: str
    prompt: str
    sourceEditorImageIds: list[str] = Field(default_factory=list)
    createdAt: datetime

    @classmethod
    def from_record(
        cls,
        record: GeneratedImageResultRecord,
        *,
        image_url: str,
    ) -> GeneratedImageResultResponse:
        return cls(
            id=record.id,
            imageUrl=image_url,
            imagePath=record.image_path,
            alt=record.alt,
            prompt=record.prompt,
            sourceEditorImageIds=record.source_editor_image_ids,
            createdAt=record.created_at,
        )


class WorkspaceContextResponse(BaseModel):
    """Read-only right workspace payload for the first 021 integration step."""

    topic_id: str
    topic_title: str
    candidate_posts: list[CandidatePostContextResponse] = Field(default_factory=list)
    pattern_summary: PatternSummaryContentResponse | None = None
    copy_draft: CopyDraftContentResponse | None = None
    editor_images: list[EditorImageResponse] = Field(default_factory=list)
    image_results: list[GeneratedImageResultResponse] = Field(default_factory=list)
    updated_at: datetime


class SelectedPostItemResponse(BaseModel):
    """Minimal persisted selected-post item."""

    post_id: str
    manual_order: int


class SelectedPostsResponse(BaseModel):
    """Response payload for selected-post persistence."""

    topic_id: str
    topic_title: str
    items: list[SelectedPostItemResponse] = Field(default_factory=list)
    updated_at: datetime


class EditorImagesResponse(BaseModel):
    """Response payload for editor image persistence."""

    topic_id: str
    topic_title: str
    items: list[EditorImageResponse] = Field(default_factory=list)
    updated_at: datetime


class DeleteImageResultResponse(BaseModel):
    """Response payload after deleting one generated image result."""

    deleted_image_id: str
    updated_at: datetime
