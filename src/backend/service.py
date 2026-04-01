"""Application service for topic-oriented backend access."""

from __future__ import annotations

import asyncio
import json
import queue
import re
import secrets
import shutil
import threading
import time
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

from agent.models import RunRequest as AgentRunRequest
from agent.models import ToolCallSummary
from agent.run_events import RunEventSink
from agent.runtime import AgentRuntime
from agent.session.models import Session, SessionImageAttachment, SessionMessage
from agent.skills.loader import SkillRecord
from agent.time_utils import now_local
from agent.trace import SessionTraceCollector, TraceMode
from backend.schemas import (
    CandidatePostContextResponse,
    CandidatePostImageResponse,
    CopyDraftContentResponse,
    CreateTopicResponse,
    DeleteImageResultResponse,
    DeleteTopicResponse,
    EditorImageResponse,
    EditorImagesResponse,
    GeneratedImageResultResponse,
    LastRunResponse,
    MessageImageAttachmentResponse,
    MessageResponse,
    MessagesResponse,
    PatternSummaryContentResponse,
    ResetResponse,
    RunResponse,
    SelectedPostItemResponse,
    SelectedPostsResponse,
    SkillListItemResponse,
    SkillsListResponse,
    StreamingRunEvent,
    TopicListItemResponse,
    TopicListResponse,
    TopicMetaRecord,
    TopicSessionRecord,
    UpdateEditorImageItemRequestBody,
    WorkspaceContextResponse,
    WorkspaceResponse,
)
from backend.topic_meta_store import TopicMetaStore
from backend.topic_store import TopicSessionStore
from backend.topic_truth_models import (
    EditorImageRecord,
    EditorImagesDocument,
    GeneratedImageResultRecord,
    PostDetail,
    PostMetrics,
    SelectedPostRecord,
    SelectedPostsDocument,
)
from backend.topic_truth_store import SessionWorkspaceStore

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
_TOOL_SUMMARY_MAX_LENGTH = 200

_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


class BackendApiError(Exception):
    """Backend-facing error with stable code and optional details."""

    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code


class BackendAppService:
    """Translate topic-oriented API requests into runtime operations."""

    def __init__(
        self,
        *,
        runtime: AgentRuntime,
        topic_store: TopicSessionStore,
        topic_meta_store: TopicMetaStore | None = None,
        workspace_store: SessionWorkspaceStore | None = None,
        trace_mode: TraceMode | None = None,
    ) -> None:
        self._runtime = runtime
        self._topic_store = topic_store
        self._topic_meta_store = topic_meta_store or TopicMetaStore(runtime.data_root)
        self._workspace_store = workspace_store or SessionWorkspaceStore(runtime.data_root)
        self._trace_mode: TraceMode | None = trace_mode

    def list_topics(self) -> TopicListResponse:
        items: list[TopicListItemResponse] = []
        for mapping in self._topic_store.list():
            meta = self._topic_meta_store.get(mapping.session_id)
            if meta is None:
                meta = TopicMetaRecord(
                    topic_id=mapping.topic_id,
                    title=mapping.topic_id,
                    description="",
                    created_at=mapping.updated_at,
                    updated_at=mapping.updated_at,
                )
            items.append(
                TopicListItemResponse(
                    topic_id=meta.topic_id,
                    title=meta.title,
                    description=meta.description,
                    session_id=mapping.session_id,
                    updated_at=max(meta.updated_at, mapping.updated_at),
                )
            )
        items.sort(key=lambda item: item.updated_at, reverse=True)
        return TopicListResponse(items=items)

    def list_skills(self) -> SkillsListResponse:
        skills_by_path: dict[Path, SkillRecord] = {}

        for skill in self._runtime.skills_loader.list_skills(filter_unavailable=False):
            skills_by_path[skill.path.resolve()] = skill

        sessions_root = self._runtime.data_root / "sessions"
        if sessions_root.exists():
            for session_dir in sorted(path for path in sessions_root.iterdir() if path.is_dir()):
                for skill in self._runtime.skills_loader.list_skills(
                    workspace_path=session_dir,
                    filter_unavailable=False,
                ):
                    if skill.source != "workspace":
                        continue
                    skills_by_path.setdefault(skill.path.resolve(), skill)

        items = [
            SkillListItemResponse(
                name=skill.name,
                description=skill.description,
                source=skill.source,
                location=str(skill.path),
                available=skill.available,
                requires=_split_requirements(skill.missing_requirements),
                content_summary=_build_skill_content_summary(skill.path),
            )
            for skill in sorted(
                skills_by_path.values(),
                key=lambda item: (item.source != "builtin", item.name.lower(), str(item.path)),
            )
        ]
        return SkillsListResponse(items=items)

    def create_topic(self, *, title: str, description: str = "") -> CreateTopicResponse:
        topic_id = _generate_topic_id()
        snapshot = self._runtime.create_session(
            topic=title,
            metadata={"topic_id": topic_id},
        )
        mapping = TopicSessionRecord(
            topic_id=topic_id,
            session_id=snapshot.session_id,
            updated_at=snapshot.updated_at,
        )
        self._topic_store.save(mapping)
        self._topic_meta_store.save(
            snapshot.session_id,
            TopicMetaRecord(
                topic_id=topic_id,
                title=title,
                description=description,
                created_at=snapshot.updated_at,
                updated_at=snapshot.updated_at,
            )
        )
        return CreateTopicResponse(
            topic_id=topic_id,
            title=title,
            description=description,
            session_id=snapshot.session_id,
            updated_at=snapshot.updated_at,
        )

    def delete_topic(self, *, topic_id: str) -> DeleteTopicResponse:
        mapping = self._topic_store.get(topic_id)
        if mapping is None:
            raise BackendApiError(
                error_code="topic_not_found",
                message="未找到对应话题。",
                status_code=404,
            )

        self._runtime.session_manager.invalidate(mapping.session_id)
        shutil.rmtree(
            self._runtime.data_root / "sessions" / mapping.session_id,
            ignore_errors=True,
        )

        self._topic_store.delete(topic_id)
        return DeleteTopicResponse(deleted_topic_id=topic_id)

    def get_workspace(self, *, topic_id: str, topic_title: str) -> WorkspaceResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        return WorkspaceResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(session, fallback=topic_title),
            session_id=record.session_id,
            messages=self._build_messages(session),
            updated_at=record.updated_at,
            last_run=None,
        )

    def run_topic(
        self,
        *,
        topic_id: str,
        topic_title: str,
        user_input: str,
        attachments: list[str],
        metadata: dict[str, Any],
    ) -> RunResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        previous_image_ids = self._list_generated_image_ids(session.session_id)
        trace_collector = self._build_trace_collector(session=session, user_input=user_input)
        try:
            result = self._run_runtime_request(
                AgentRunRequest(
                    session_id=session.session_id,
                    user_input=user_input,
                    attachments=attachments,
                    metadata=metadata,
                ),
                trace_collector=trace_collector,
            )
        except Exception as exc:  # noqa: BLE001
            raise BackendApiError(
                error_code="runtime_run_failed",
                message="Agent 运行失败。",
                details={"reason": str(exc)},
            ) from exc

        fresh_session = self._runtime.session_manager.require(session.session_id)
        self._attach_latest_generated_image(
            session=fresh_session,
            previous_image_ids=previous_image_ids,
        )
        fresh_session = self._runtime.session_manager.require(session.session_id)
        record.updated_at = now_local()
        self._topic_store.save(record)
        self._sync_topic_meta(record, description=None)
        trace_file = (
            str(
                trace_collector.write_run_block(
                    final_text=result.final_text,
                    artifacts=result.artifacts,
                )
            )
            if trace_collector is not None
            else None
        )
        return RunResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(fresh_session, fallback=topic_title),
            session_id=record.session_id,
            messages=self._build_messages(fresh_session),
            last_run=LastRunResponse(
                final_text=result.final_text,
                tool_calls=result.tool_calls,
                artifacts=result.artifacts,
            ),
            updated_at=record.updated_at,
            trace_file=trace_file,
        )

    async def stream_topic_run(
        self,
        *,
        topic_id: str,
        topic_title: str,
        user_input: str,
        attachments: list[str],
        metadata: dict[str, Any],
    ) -> AsyncIterator[str]:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        previous_image_ids = self._list_generated_image_ids(session.session_id)
        trace_collector = self._build_trace_collector(session=session, user_input=user_input)
        event_queue: queue.Queue[StreamingRunEvent | None] = queue.Queue()
        run_id = uuid4().hex
        run_event_sink = _QueueRunEventSink(queue=event_queue, run_id=run_id)

        run_event_sink.emit(
            event="run_started",
            payload={
                "topic_id": record.topic_id,
                "session_id": record.session_id,
            },
        )

        def produce_events() -> None:
            try:
                result = self._run_runtime_request(
                    AgentRunRequest(
                        session_id=session.session_id,
                        user_input=user_input,
                        attachments=attachments,
                        metadata=metadata,
                    ),
                    trace_collector=trace_collector,
                    run_event_sink=run_event_sink,
                )
                fresh_session = self._runtime.session_manager.require(session.session_id)
                self._attach_latest_generated_image(
                    session=fresh_session,
                    previous_image_ids=previous_image_ids,
                )
                fresh_session = self._runtime.session_manager.require(session.session_id)
                record.updated_at = now_local()
                self._topic_store.save(record)
                self._sync_topic_meta(record, description=None)
                trace_file = (
                    str(
                        trace_collector.write_run_block(
                            final_text=result.final_text,
                            artifacts=result.artifacts,
                        )
                    )
                    if trace_collector is not None
                    else None
                )
                for chunk in _chunk_assistant_text(result.final_text):
                    run_event_sink.emit(
                        event="assistant_delta",
                        payload={"delta": chunk},
                    )
                    time.sleep(0.03)

                run_event_sink.emit(
                    event="run_completed",
                    payload={
                        "topic_id": record.topic_id,
                        "topic_title": self._current_topic_title(
                            fresh_session, fallback=topic_title
                        ),
                        "session_id": record.session_id,
                        "final_text": result.final_text,
                        "tool_calls": [
                            item.model_dump(mode="json") for item in result.tool_calls
                        ],
                        "artifacts": list(result.artifacts),
                        "trace_file": trace_file,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                run_event_sink.emit(
                    event="run_failed",
                    payload={"message": f"Agent 运行失败：{exc}"},
                )
            finally:
                event_queue.put(None)

        producer = threading.Thread(target=produce_events, daemon=True)
        producer.start()
        try:
            while True:
                try:
                    event = event_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.02)
                    continue
                if event is None:
                    break
                yield _format_sse_event(event)
        finally:
            producer.join(timeout=0.1)

    def get_messages(self, *, topic_id: str, topic_title: str) -> MessagesResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        return MessagesResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(session, fallback=topic_title),
            session_id=record.session_id,
            messages=self._build_messages(session),
            updated_at=record.updated_at,
        )

    def get_workspace_context(
        self,
        *,
        topic_id: str,
        topic_title: str,
    ) -> WorkspaceContextResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        post_details = self._workspace_store.list_post_details(session.session_id)
        selected_document = self._workspace_store.read_selected_posts(session.session_id)
        pattern_summary = self._workspace_store.read_pattern_summary(session.session_id)
        copy_draft = self._workspace_store.read_copy_draft(session.session_id)
        editor_images = self._workspace_store.read_editor_images(session.session_id)
        image_results = self._workspace_store.read_image_results(session.session_id)
        selected_items = selected_document.items if selected_document is not None else []
        selected_by_post_id = {item.post_id: item.manual_order for item in selected_items}
        candidate_posts = []
        updated_at = record.updated_at

        if post_details:
            candidate_posts = [
                self._convert_post_detail_to_candidate_post(
                    topic_id=topic_id,
                    detail=detail,
                    manual_order=selected_by_post_id.get(detail.post_id),
                )
                for detail in post_details
            ]
            updated_at = max(updated_at, *(detail.updated_at for detail in post_details))

        if selected_document is not None and selected_document.updated_at > updated_at:
            updated_at = selected_document.updated_at

        if pattern_summary is not None and pattern_summary.updated_at > updated_at:
            updated_at = pattern_summary.updated_at
        if copy_draft is not None and copy_draft.updated_at > updated_at:
            updated_at = copy_draft.updated_at
        if editor_images is not None and editor_images.updated_at > updated_at:
            updated_at = editor_images.updated_at
        if image_results is not None and image_results.updated_at > updated_at:
            updated_at = image_results.updated_at

        return WorkspaceContextResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(session, fallback=topic_title),
            candidate_posts=candidate_posts,
            pattern_summary=(
                PatternSummaryContentResponse.from_record(pattern_summary)
                if pattern_summary is not None
                else None
            ),
            copy_draft=(
                CopyDraftContentResponse.from_record(copy_draft)
                if copy_draft is not None
                else None
            ),
            editor_images=(
                [
                    self._convert_editor_image(topic_id=topic_id, record=item)
                    for item in sorted(editor_images.items, key=lambda image: image.order)
                ]
                if editor_images is not None
                else []
            ),
            image_results=(
                [
                    self._convert_generated_image_result(topic_id=topic_id, record=item)
                    for item in image_results.items
                ]
                if image_results is not None
                else []
            ),
            updated_at=updated_at,
        )

    def update_selected_posts(
        self,
        *,
        topic_id: str,
        topic_title: str,
        post_ids: list[str],
    ) -> SelectedPostsResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        seen: set[str] = set()
        selected_items: list[SelectedPostRecord] = []

        for post_id in post_ids:
            normalized_post_id = post_id.strip()
            if normalized_post_id == "" or normalized_post_id in seen:
                continue
            if (
                self._workspace_store.read_post_detail(session.session_id, normalized_post_id)
                is None
            ):
                continue
            seen.add(normalized_post_id)
            selected_items.append(
                SelectedPostRecord(
                    post_id=normalized_post_id,
                    manual_order=len(selected_items) + 1,
                )
            )

        updated_at = now_local()
        self._workspace_store.write_selected_posts(
            session.session_id,
            SelectedPostsDocument(
                items=selected_items,
                updated_at=updated_at,
            ),
        )
        record.updated_at = updated_at
        self._topic_store.save(record)
        self._sync_topic_meta(record, description=None)
        return SelectedPostsResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(session, fallback=topic_title),
            items=[
                SelectedPostItemResponse(
                    post_id=item.post_id,
                    manual_order=item.manual_order,
                )
                for item in selected_items
            ],
            updated_at=updated_at,
        )

    def get_editor_images(
        self,
        *,
        topic_id: str,
        topic_title: str,
    ) -> EditorImagesResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        document = self._workspace_store.read_editor_images(session.session_id)
        updated_at = document.updated_at if document is not None else record.updated_at
        return EditorImagesResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(session, fallback=topic_title),
            items=(
                [
                    self._convert_editor_image(topic_id=topic_id, record=item)
                    for item in sorted(document.items, key=lambda image: image.order)
                ]
                if document is not None
                else []
            ),
            updated_at=updated_at,
        )

    def update_editor_images(
        self,
        *,
        topic_id: str,
        topic_title: str,
        items: list[UpdateEditorImageItemRequestBody],
    ) -> EditorImagesResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        updated_at = now_local()
        normalized_items: list[EditorImageRecord] = []
        seen_ids: set[str] = set()
        for item in sorted(items, key=lambda current: current.order):
            if item.id in seen_ids:
                continue
            seen_ids.add(item.id)
            normalized_items.append(
                EditorImageRecord(
                    id=item.id,
                    order=len(normalized_items) + 1,
                    source_type=item.source_type,
                    source_post_id=item.source_post_id,
                    source_image_id=item.source_image_id,
                    source_generated_image_id=item.source_generated_image_id,
                    image_path=item.image_path,
                    alt=item.alt,
                )
            )
        document = self._workspace_store.write_editor_images(
            session.session_id,
            EditorImagesDocument(items=normalized_items, updated_at=updated_at),
        )
        record.updated_at = updated_at
        self._topic_store.save(record)
        self._sync_topic_meta(record, description=None)
        return EditorImagesResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(session, fallback=topic_title),
            items=[
                self._convert_editor_image(topic_id=topic_id, record=item)
                for item in document.items
            ],
            updated_at=updated_at,
        )

    def delete_image_result(
        self,
        *,
        topic_id: str,
        topic_title: str,
        image_id: str,
    ) -> DeleteImageResultResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        document = self._workspace_store.read_image_results(session.session_id)
        updated_at = now_local()
        if document is not None:
            self._workspace_store.write_image_results(
                session.session_id,
                document.model_copy(
                    update={
                        "items": [item for item in document.items if item.id != image_id],
                        "updated_at": updated_at,
                    }
                ),
            )
            record.updated_at = updated_at
            self._topic_store.save(record)
            self._sync_topic_meta(record, description=None)
        return DeleteImageResultResponse(deleted_image_id=image_id, updated_at=updated_at)

    def reset_topic(self, *, topic_id: str, topic_title: str) -> ResetResponse:
        record, session = self._resolve_session(topic_id=topic_id, topic_title=topic_title)
        snapshot = self._runtime.reset_session(session.session_id)
        self._workspace_store.clear_workspace(snapshot.session_id)
        record.updated_at = now_local()
        self._topic_store.save(record)
        self._sync_topic_meta(record, description=None)
        return ResetResponse(
            topic_id=record.topic_id,
            topic_title=self._current_topic_title(snapshot, fallback=topic_title),
            session_id=snapshot.session_id,
            messages=[],
            updated_at=record.updated_at,
        )

    def _resolve_session(
        self,
        *,
        topic_id: str,
        topic_title: str,
    ) -> tuple[TopicSessionRecord, Session]:
        record = self._topic_store.get(topic_id)
        if record is None:
            snapshot = self._runtime.create_session(
                topic=topic_title,
                metadata={"topic_id": topic_id},
            )
            record = TopicSessionRecord(
                topic_id=topic_id,
                session_id=snapshot.session_id,
                updated_at=snapshot.updated_at,
            )
            self._topic_store.save(record)
            if self._topic_meta_store.get(snapshot.session_id) is None:
                self._topic_meta_store.save(
                    snapshot.session_id,
                    TopicMetaRecord(
                        topic_id=topic_id,
                        title=topic_title,
                        description="",
                        created_at=snapshot.updated_at,
                        updated_at=snapshot.updated_at,
                    )
            )
            return record, self._runtime.session_manager.require(snapshot.session_id)

        try:
            session = self._runtime.session_manager.require(record.session_id)
        except Exception:
            snapshot = self._runtime.create_session(
                topic=topic_title,
                metadata={"topic_id": topic_id},
            )
            record.session_id = snapshot.session_id
            record.updated_at = snapshot.updated_at
            self._topic_store.save(record)
            self._sync_topic_meta(record, description=None)
            return record, self._runtime.session_manager.require(snapshot.session_id)

        if session.topic != topic_title:
            session.topic = topic_title
            self._runtime.session_manager.save(session)
            record.updated_at = session.updated_at
            self._topic_store.save(record)
            self._sync_topic_meta(record, description=None)
        return record, session

    def _sync_topic_meta(
        self,
        record: TopicSessionRecord,
        *,
        description: str | None,
    ) -> None:
        session = self._runtime.session_manager.require(record.session_id)
        existing = self._topic_meta_store.get(record.session_id)
        self._topic_meta_store.save(
            record.session_id,
            TopicMetaRecord(
                topic_id=record.topic_id,
                title=self._current_topic_title(session, fallback=record.topic_id),
                description=(
                    existing.description
                    if existing is not None and description is None
                    else (description or "")
                ),
                created_at=existing.created_at if existing is not None else record.updated_at,
                updated_at=record.updated_at,
            )
        )

    @staticmethod
    def _current_topic_title(session: Any, *, fallback: str) -> str:
        topic = getattr(session, "topic", None)
        return topic or fallback

    def _build_messages(self, session: Session) -> list[MessageResponse]:
        messages: list[MessageResponse] = []
        pending_tool_calls: dict[str, tuple[int, str, dict[str, Any]]] = {}
        pending_tool_summaries: list[ToolCallSummary] = []

        for index, message in enumerate(session.messages):
            if message.role == "user":
                pending_tool_calls = {}
                pending_tool_summaries = []
                messages.append(
                    MessageResponse(
                        id=f"{session.session_id}:{index}",
                        role="user",
                        text=message.content,
                        time=_format_message_time(message.timestamp),
                        image_attachments=[],
                    )
                )
                continue

            if message.role == "assistant":
                if message.tool_calls:
                    for tool_index, tool_call in enumerate(message.tool_calls):
                        key = tool_call.id or f"{index}:{tool_index}:{tool_call.name}"
                        pending_tool_calls[key] = (
                            tool_index,
                            tool_call.name,
                            tool_call.arguments,
                        )
                    continue

                messages.append(
                    MessageResponse(
                        id=f"{session.session_id}:{index}",
                        role="agent",
                        text=message.content,
                        time=_format_message_time(message.timestamp),
                        agent_name=message.name or "协作 Agent",
                        tool_summary=pending_tool_summaries.copy(),
                        image_attachments=[
                            MessageImageAttachmentResponse(
                                image_url=_to_topic_asset_url(
                                    topic_id=cast(str, session.metadata.get("topic_id")),
                                    relative_path=attachment.image_path,
                                ),
                                alt=attachment.alt,
                            )
                            for attachment in message.image_attachments
                        ]
                        if session.metadata.get("topic_id")
                        else [],
                    )
                )
                pending_tool_calls = {}
                pending_tool_summaries = []
                continue

            if message.role == "tool":
                pending_tool_summaries.append(
                    _build_tool_summary(
                        pending_tool_calls=pending_tool_calls,
                        tool_message=message,
                    )
                )
        return messages

    def _build_trace_collector(
        self,
        *,
        session: Session,
        user_input: str,
    ) -> SessionTraceCollector | None:
        if self._trace_mode is None:
            return None
        return SessionTraceCollector(
            session_id=session.session_id,
            topic=session.topic,
            workspace_path=session.workspace_path,
            raw_user_input=user_input,
            normalized_user_input=user_input,
            mode=self._trace_mode,
        )

    def _run_runtime_request(
        self,
        request: AgentRunRequest,
        *,
        trace_collector: SessionTraceCollector | None,
        run_event_sink: RunEventSink | None = None,
    ) -> Any:
        previous_runtime_sink = getattr(self._runtime, "_trace_sink", None)
        previous_runtime_run_event_sink = getattr(self._runtime, "_run_event_sink", None)
        loop_runner = getattr(self._runtime, "loop_runner", None)
        previous_loop_sink = getattr(loop_runner, "trace_sink", None)
        previous_loop_run_event_sink = getattr(loop_runner, "run_event_sink", None)
        if trace_collector is not None:
            self._runtime._trace_sink = trace_collector
            if loop_runner is not None and hasattr(loop_runner, "trace_sink"):
                loop_runner.trace_sink = trace_collector
        if run_event_sink is not None:
            self._runtime._run_event_sink = run_event_sink
            if loop_runner is not None and hasattr(loop_runner, "run_event_sink"):
                loop_runner.run_event_sink = run_event_sink
        try:
            return self._runtime.run(request)
        finally:
            self._runtime._trace_sink = previous_runtime_sink
            self._runtime._run_event_sink = previous_runtime_run_event_sink
            if loop_runner is not None and hasattr(loop_runner, "trace_sink"):
                loop_runner.trace_sink = previous_loop_sink
            if loop_runner is not None and hasattr(loop_runner, "run_event_sink"):
                loop_runner.run_event_sink = previous_loop_run_event_sink

    def _convert_post_detail_to_candidate_post(
        self,
        *,
        topic_id: str,
        detail: PostDetail,
        manual_order: int | None,
    ) -> CandidatePostContextResponse:
        body_text = detail.content.text
        image_url = self._resolve_candidate_image_url(topic_id=topic_id, detail=detail)
        return CandidatePostContextResponse(
            id=detail.post_id,
            title=detail.title,
            excerpt=_build_excerpt(body_text),
            bodyText=body_text,
            author=(
                detail.author.name
                if detail.author is not None and detail.author.name
                else "未知作者"
            ),
            heat=_format_heat(detail.metrics),
            sourceUrl=detail.url,
            imageUrl=image_url,
            images=self._build_candidate_images(
                topic_id=topic_id,
                detail=detail,
                cover_image_url=image_url,
            ),
            selected=manual_order is not None,
            manualOrder=manual_order,
        )

    def _build_candidate_images(
        self,
        *,
        topic_id: str,
        detail: PostDetail,
        cover_image_url: str,
    ) -> list[CandidatePostImageResponse]:
        if detail.media:
            return [
                CandidatePostImageResponse(
                    id=asset.asset_id,
                    imageUrl=_to_topic_asset_url(
                        topic_id=topic_id,
                        relative_path=_to_workspace_asset_path(
                            post_id=detail.post_id,
                            relative_path=asset.path,
                        ),
                    ),
                    imagePath=_to_workspace_asset_path(
                        post_id=detail.post_id,
                        relative_path=asset.path,
                    ),
                    alt=f"{detail.title} 图片 {asset.order}",
                )
                for asset in detail.media
            ]
        if cover_image_url:
            return [
                CandidatePostImageResponse(
                    id=f"{detail.post_id}-cover",
                    imageUrl=cover_image_url,
                    imagePath="",
                    alt=f"{detail.title} 封面图",
                )
            ]
        return []

    def _resolve_candidate_image_url(
        self,
        *,
        topic_id: str,
        detail: PostDetail,
    ) -> str:
        if detail.media:
            return _to_topic_asset_url(
                topic_id=topic_id,
                relative_path=_to_workspace_asset_path(
                    post_id=detail.post_id,
                    relative_path=detail.media[0].path,
                ),
            )
        return ""

    def _convert_editor_image(
        self,
        *,
        topic_id: str,
        record: EditorImageRecord,
    ) -> EditorImageResponse:
        return EditorImageResponse.from_record(
            record,
            image_url=_to_topic_asset_url(topic_id=topic_id, relative_path=record.image_path),
        )

    def _convert_generated_image_result(
        self,
        *,
        topic_id: str,
        record: GeneratedImageResultRecord,
    ) -> GeneratedImageResultResponse:
        return GeneratedImageResultResponse.from_record(
            record,
            image_url=_to_topic_asset_url(topic_id=topic_id, relative_path=record.image_path),
        )

    def _list_generated_image_ids(self, session_id: str) -> set[str]:
        document = self._workspace_store.read_image_results(session_id)
        if document is None:
            return set()
        return {item.id for item in document.items}

    def _attach_latest_generated_image(
        self,
        *,
        session: Session,
        previous_image_ids: set[str],
    ) -> None:
        document = self._workspace_store.read_image_results(session.session_id)
        if document is None:
            return
        new_item = next(
            (item for item in reversed(document.items) if item.id not in previous_image_ids),
            None,
        )
        if new_item is None:
            return
        for index in range(len(session.messages) - 1, -1, -1):
            message = session.messages[index]
            if message.role != "assistant" or message.tool_calls:
                continue
            message.image_attachments = [
                SessionImageAttachment(image_path=new_item.image_path, alt=new_item.alt)
            ]
            session.messages[index] = message
            session.updated_at = now_local()
            self._runtime.session_manager.save(session)
            return


def _format_message_time(value: datetime) -> str:
    return value.strftime("%H:%M")


def _build_tool_summary(
    *,
    pending_tool_calls: dict[str, tuple[int, str, dict[str, Any]]],
    tool_message: SessionMessage,
) -> ToolCallSummary:
    tool_call_id = tool_message.tool_call_id
    if tool_call_id is not None and tool_call_id in pending_tool_calls:
        _, name, arguments = pending_tool_calls.pop(tool_call_id)
    else:
        name = tool_message.name or "unknown_tool"
        arguments = {}

    return ToolCallSummary(
        name=name,
        arguments_summary=_summarize_tool_arguments(arguments),
        result_summary=_summarize_tool_result(tool_message.content),
    )


def _summarize_tool_arguments(arguments: dict[str, Any]) -> str:
    if not arguments:
        return "{}"
    return _truncate_tool_summary(json.dumps(arguments, ensure_ascii=False, sort_keys=True))


def _summarize_tool_result(result: str) -> str:
    return _truncate_tool_summary(result)


def _truncate_tool_summary(value: str, *, max_length: int = _TOOL_SUMMARY_MAX_LENGTH) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def _format_heat(metrics: PostMetrics) -> str:
    parts: list[str] = []
    if metrics.favorites is not None:
        parts.append(f"收藏 {metrics.favorites}")
    if metrics.likes is not None:
        parts.append(f"点赞 {metrics.likes}")
    if metrics.comments is not None:
        parts.append(f"评论 {metrics.comments}")
    return " · ".join(parts)


def _build_excerpt(text: str, *, max_length: int = 72) -> str:
    normalized = " ".join(text.split()).strip()
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[:max_length].rstrip()}..."


def _to_workspace_asset_path(*, post_id: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if normalized.startswith("posts/"):
        return normalized
    if normalized.startswith("assets/"):
        return f"posts/{post_id}/{normalized}"
    return f"posts/{post_id}/assets/{normalized}"


def _to_topic_asset_url(*, topic_id: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    return f"/api/topics/{topic_id}/assets/{normalized}"


def _split_requirements(raw: str) -> list[str]:
    if raw.strip() == "":
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _build_skill_content_summary(path: Path, *, max_length: int = 1600) -> str:
    content = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(content)
    stripped = content[match.end() :] if match is not None else content
    normalized = stripped.strip()
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[:max_length].rstrip()}\n\n..."


def _encode_crockford(value: int, length: int) -> str:
    chars = ["0"] * length
    for index in range(length - 1, -1, -1):
        chars[index] = _CROCKFORD_BASE32[value & 31]
        value >>= 5
    return "".join(chars)


def _generate_topic_id() -> str:
    timestamp_ms = int(now_local().timestamp() * 1000)
    randomness = int.from_bytes(secrets.token_bytes(10), "big")
    ulid = f"{_encode_crockford(timestamp_ms, 10)}{_encode_crockford(randomness, 16)}"
    return f"topic_{ulid}"


class _QueueRunEventSink:
    """Bridge sync runtime events into one async SSE queue."""

    def __init__(
        self,
        *,
        queue: queue.Queue[StreamingRunEvent | None],
        run_id: str,
    ) -> None:
        self._queue = queue
        self._run_id = run_id

    def emit(
        self,
        *,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        envelope = StreamingRunEvent(
            type=cast(
                Literal[
                    "run_started",
                    "tool_call_started",
                    "tool_call_finished",
                    "assistant_delta",
                    "run_completed",
                    "run_failed",
                ],
                event,
            ),
            run_id=self._run_id,
            timestamp=now_local(),
            payload=payload,
        )
        self._queue.put(envelope)


def _format_sse_event(event: StreamingRunEvent) -> str:
    return (
        f"event: {event.type}\n"
        f"data: {json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}\n\n"
    )


def _chunk_assistant_text(text: str, *, chunk_size: int = 48) -> list[str]:
    if text == "":
        return [""]
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
