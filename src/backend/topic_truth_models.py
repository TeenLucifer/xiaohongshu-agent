"""File-backed topic workspace truth models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TopicMeta(BaseModel):
    """Topic-level metadata for the workspace truth store."""

    topic_id: str
    title: str
    description: str | None = None
    updated_at: datetime


class PostHeat(BaseModel):
    """Post engagement summary for workspace cards."""

    likes: int | None = None
    favorites: int | None = None
    comments: int | None = None


class CandidatePostRecord(BaseModel):
    """Minimal candidate/selected post record for workspace display."""

    post_id: str
    title: str
    excerpt: str
    author: str | None = None
    source_url: str | None = None
    heat: PostHeat | None = None
    cover_image_path: str | None = None
    selected: bool
    manual_order: int | None = None
    updated_at: datetime


class CandidatePostsDocument(BaseModel):
    """Candidate post list for the workspace."""

    items: list[CandidatePostRecord] = Field(default_factory=list)
    updated_at: datetime


class SelectedPostRecord(BaseModel):
    """Minimal selected-post state persisted for one workspace."""

    post_id: str
    manual_order: int


class SelectedPostsDocument(BaseModel):
    """Selected post list for the workspace."""

    items: list[SelectedPostRecord] = Field(default_factory=list)
    updated_at: datetime


class PatternSummaryRecord(BaseModel):
    """Structured pattern summary for the workspace."""

    title_patterns: list[str] = Field(default_factory=list)
    body_patterns: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    image_patterns: list[str] = Field(default_factory=list)
    image_quality_notes: str | None = None
    summary_text: str | None = None
    source_post_ids: list[str] = Field(default_factory=list)
    updated_at: datetime


class CopyDraftRecord(BaseModel):
    """Copy draft payload for the workspace."""

    title: str
    body: str
    source_summary_version: str | None = None
    updated_at: datetime


class EditorImageRecord(BaseModel):
    """Single editor-area image persisted in workspace."""

    id: str
    order: int
    source_type: Literal["material", "generated"]
    source_post_id: str | None = None
    source_image_id: str | None = None
    source_generated_image_id: str | None = None
    alt: str
    image_path: str


class EditorImagesDocument(BaseModel):
    """Persisted editor image list."""

    items: list[EditorImageRecord] = Field(default_factory=list)
    updated_at: datetime


class GeneratedImageResultRecord(BaseModel):
    """Single generated image result."""

    id: str
    image_path: str
    alt: str
    prompt: str
    source_editor_image_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class ImageResultsRecord(BaseModel):
    """Image result index for the workspace."""

    items: list[GeneratedImageResultRecord] = Field(default_factory=list)
    updated_at: datetime


class PostAuthor(BaseModel):
    """Normalized author identity."""

    name: str | None = None
    author_id: str | None = None


class PostContent(BaseModel):
    """Normalized textual content for one post."""

    text: str
    hashtags: list[str] = Field(default_factory=list)


class PostMetrics(BaseModel):
    """Normalized engagement metrics."""

    likes: int | None = None
    favorites: int | None = None
    comments: int | None = None


class PostMediaAsset(BaseModel):
    """One local media file associated with a post."""

    asset_id: str
    kind: Literal["image"]
    path: str
    order: int


class PostSource(BaseModel):
    """Source metadata for one imported post."""

    platform: str
    source_type: str
    captured_at: datetime


class PostDetail(BaseModel):
    """Normalized post detail stored under one topic."""

    post_id: str
    title: str
    post_type: str
    url: str
    published_at: str | None = None
    author: PostAuthor | None = None
    content: PostContent
    metrics: PostMetrics
    media: list[PostMediaAsset] = Field(default_factory=list)
    source: PostSource | None = None
    updated_at: datetime


RawPostRecord = dict[str, Any]
