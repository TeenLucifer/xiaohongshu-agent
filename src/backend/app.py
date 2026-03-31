"""FastAPI entrypoint for the minimal backend glue layer."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Annotated, Any, Literal, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from agent.runtime import AgentRuntime
from agent.trace import TraceMode
from backend.schemas import (
    CreateTopicRequestBody,
    ErrorResponse,
    ResetRequestBody,
    RunRequestBody,
    UpdateSelectedPostsRequestBody,
)
from backend.service import BackendApiError, BackendAppService
from backend.topic_meta_store import TopicMetaStore
from backend.topic_store import TopicSessionStore
from backend.topic_truth_store import SessionWorkspaceStore

DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
AppTraceMode = Literal["summary", "full", "off"]


def create_app(
    *,
    runtime: AgentRuntime | None = None,
    project_root: Path | None = None,
    data_root: Path | None = None,
    allowed_origins: list[str] | None = None,
    trace_mode: AppTraceMode | None = None,
) -> FastAPI:
    resolved_project_root = project_root or Path(__file__).resolve().parents[2]
    resolved_data_root = data_root or (resolved_project_root / "data")
    resolved_trace_mode = _resolve_trace_mode(trace_mode)
    workspace_store = SessionWorkspaceStore(resolved_data_root)
    topic_store = TopicSessionStore(resolved_data_root)
    topic_meta_store = TopicMetaStore(resolved_data_root)
    resolved_runtime = runtime or AgentRuntime(
        project_root=resolved_project_root,
        data_root=resolved_data_root,
    )
    service = BackendAppService(
        runtime=resolved_runtime,
        topic_store=topic_store,
        topic_meta_store=topic_meta_store,
        workspace_store=workspace_store,
        trace_mode=resolved_trace_mode,
    )

    app = FastAPI(title="xiaohongshu-agent backend")
    app.state.backend_service = service
    app.state.topic_meta_store = topic_meta_store
    app.state.session_workspace_store = workspace_store
    app.state.topic_store = topic_store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or DEFAULT_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(BackendApiError)
    async def handle_backend_api_error(
        _: Request,
        exc: BackendApiError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
            ).model_dump(mode="json"),
        )

    @app.get("/api/topics")
    async def list_topics(request: Request) -> Any:
        return request.app.state.backend_service.list_topics()

    @app.get("/api/skills")
    async def list_skills(request: Request) -> Any:
        return request.app.state.backend_service.list_skills()

    @app.post("/api/topics")
    async def create_topic(
        request: Request,
        payload: CreateTopicRequestBody,
    ) -> Any:
        return request.app.state.backend_service.create_topic(
            title=payload.title,
            description=payload.description,
        )

    @app.delete("/api/topics/{topic_id}")
    async def delete_topic(request: Request, topic_id: str) -> Any:
        return request.app.state.backend_service.delete_topic(topic_id=topic_id)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error_code="invalid_request",
                message="请求参数不合法。",
                details={"errors": exc.errors()},
            ).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="internal_error",
                message="后端内部错误。",
                details={"reason": str(exc)},
            ).model_dump(mode="json"),
        )

    @app.get("/api/topics/{topic_id}/workspace")
    async def get_workspace(
        request: Request,
        topic_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.get_workspace(
            topic_id=topic_id,
            topic_title=topic_title,
        )

    @app.post("/api/topics/{topic_id}/runs")
    async def run_topic(
        request: Request,
        topic_id: str,
        payload: RunRequestBody,
    ) -> Any:
        return request.app.state.backend_service.run_topic(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            user_input=payload.user_input,
            attachments=payload.attachments,
            metadata=payload.metadata,
        )

    @app.post("/api/topics/{topic_id}/runs/stream")
    async def stream_run_topic(
        request: Request,
        topic_id: str,
        payload: RunRequestBody,
    ) -> StreamingResponse:
        stream = request.app.state.backend_service.stream_topic_run(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            user_input=payload.user_input,
            attachments=payload.attachments,
            metadata=payload.metadata,
        )
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/topics/{topic_id}/messages")
    async def get_messages(
        request: Request,
        topic_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.get_messages(
            topic_id=topic_id,
            topic_title=topic_title,
        )

    @app.get("/api/topics/{topic_id}/context")
    async def get_workspace_context(
        request: Request,
        topic_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.get_workspace_context(
            topic_id=topic_id,
            topic_title=topic_title,
        )

    @app.put("/api/topics/{topic_id}/selected-posts")
    async def update_selected_posts(
        request: Request,
        topic_id: str,
        payload: UpdateSelectedPostsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.update_selected_posts(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            post_ids=payload.post_ids,
        )

    @app.get("/api/topics/{topic_id}/assets/{asset_path:path}")
    async def get_topic_asset(
        request: Request,
        topic_id: str,
        asset_path: str,
    ) -> Response:
        record = request.app.state.topic_store.get(topic_id)
        if record is None:
            raise HTTPException(status_code=404, detail="topic mapping not found")
        workspace_root = request.app.state.session_workspace_store.get_workspace_root(
            record.session_id
        ).resolve()
        candidate = (workspace_root / asset_path).resolve()
        if workspace_root not in candidate.parents and candidate != workspace_root:
            raise HTTPException(status_code=400, detail="invalid asset path")
        if not candidate.exists() or not candidate.is_file():
            raise HTTPException(status_code=404, detail="asset not found")
        media_type, _ = mimetypes.guess_type(candidate.name)
        return Response(
            content=candidate.read_bytes(),
            media_type=media_type or "application/octet-stream",
        )

    @app.post("/api/topics/{topic_id}/reset")
    async def reset_topic(
        request: Request,
        topic_id: str,
        payload: ResetRequestBody,
    ) -> Any:
        return request.app.state.backend_service.reset_topic(
            topic_id=topic_id,
            topic_title=payload.topic_title,
        )

    return app


def _resolve_trace_mode(explicit_mode: AppTraceMode | None) -> TraceMode | None:
    if explicit_mode == "off":
        return None
    if explicit_mode is not None:
        return explicit_mode
    raw_mode = os.getenv("XHS_BACKEND_TRACE_MODE", "").strip().lower()
    if raw_mode in {"off", "none", "false", "0"}:
        return None
    if raw_mode in {"summary", "full"}:
        return cast(TraceMode, raw_mode)

    environment = os.getenv("XHS_ENV", os.getenv("ENV", "development")).strip().lower()
    return None if environment == "production" else "full"


app = create_app()


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
