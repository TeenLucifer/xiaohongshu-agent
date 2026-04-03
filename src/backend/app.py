"""FastAPI entrypoint for the minimal backend glue layer."""

from __future__ import annotations

import base64
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
    CopyDraftResponse,
    CopyDraftSelectionPolishResponse,
    CreateImageMaterialsRequestBody,
    CreateLinkMaterialRequestBody,
    CreateTextMaterialRequestBody,
    CreateTopicRequestBody,
    ErrorResponse,
    MaterialsResponse,
    PolishCopyDraftSelectionRequestBody,
    ResetRequestBody,
    RunRequestBody,
    TestProviderSettingsRequestBody,
    UpdateCopyDraftRequestBody,
    UpdateEditorImagesRequestBody,
    UpdateProviderSettingsRequestBody,
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

    @app.get("/api/settings")
    async def get_settings(request: Request) -> Any:
        return request.app.state.backend_service.get_settings()

    @app.put("/api/settings/llm")
    async def update_llm_settings(
        request: Request,
        payload: UpdateProviderSettingsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.update_llm_settings(
            base_url=payload.base_url,
            model=payload.model,
            api_key=payload.api_key,
        )

    @app.put("/api/settings/image-analysis")
    async def update_image_analysis_settings(
        request: Request,
        payload: UpdateProviderSettingsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.update_image_analysis_settings(
            base_url=payload.base_url,
            model=payload.model,
            api_key=payload.api_key,
        )

    @app.put("/api/settings/image-generation")
    async def update_image_generation_settings(
        request: Request,
        payload: UpdateProviderSettingsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.update_image_generation_settings(
            base_url=payload.base_url,
            model=payload.model,
            api_key=payload.api_key,
        )

    @app.post("/api/settings/llm/test")
    async def test_llm_settings(
        request: Request,
        payload: TestProviderSettingsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.test_llm_settings(
            base_url=payload.base_url,
            model=payload.model,
            api_key=payload.api_key,
        )

    @app.post("/api/settings/image-analysis/test")
    async def test_image_analysis_settings(
        request: Request,
        payload: TestProviderSettingsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.test_image_analysis_settings(
            base_url=payload.base_url,
            model=payload.model,
            api_key=payload.api_key,
        )

    @app.post("/api/settings/image-generation/test")
    async def test_image_generation_settings(
        request: Request,
        payload: TestProviderSettingsRequestBody,
    ) -> Any:
        return request.app.state.backend_service.test_image_generation_settings(
            base_url=payload.base_url,
            model=payload.model,
            api_key=payload.api_key,
        )

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

    @app.get("/api/topics/{topic_id}/editor-images")
    async def get_editor_images(
        request: Request,
        topic_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.get_editor_images(
            topic_id=topic_id,
            topic_title=topic_title,
        )

    @app.get("/api/topics/{topic_id}/materials")
    async def get_materials(
        request: Request,
        topic_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> MaterialsResponse:
        return request.app.state.backend_service.get_materials(
            topic_id=topic_id,
            topic_title=topic_title,
        )

    @app.post("/api/topics/{topic_id}/materials/text")
    async def create_text_material(
        request: Request,
        topic_id: str,
        payload: CreateTextMaterialRequestBody,
    ) -> MaterialsResponse:
        return request.app.state.backend_service.create_text_material(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            title=payload.title,
            text_content=payload.text_content,
        )

    @app.post("/api/topics/{topic_id}/materials/link")
    async def create_link_material(
        request: Request,
        topic_id: str,
        payload: CreateLinkMaterialRequestBody,
    ) -> MaterialsResponse:
        return request.app.state.backend_service.create_link_material(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            title=payload.title,
            url=payload.url,
        )

    @app.post("/api/topics/{topic_id}/materials/images")
    async def upload_material_images(
        request: Request,
        topic_id: str,
        payload: CreateImageMaterialsRequestBody,
    ) -> MaterialsResponse:
        file_payloads: list[dict[str, Any]] = []
        for item in payload.items:
            file_payloads.append(
                {
                    "filename": item.filename,
                    "content_type": item.content_type,
                    "content": base64.b64decode(item.content_base64),
                }
            )
        return request.app.state.backend_service.upload_material_images(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            files=file_payloads,
        )

    @app.delete("/api/topics/{topic_id}/materials/{material_id}")
    async def delete_material(
        request: Request,
        topic_id: str,
        material_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.delete_material(
            topic_id=topic_id,
            topic_title=topic_title,
            material_id=material_id,
        )

    @app.put("/api/topics/{topic_id}/editor-images")
    async def update_editor_images(
        request: Request,
        topic_id: str,
        payload: UpdateEditorImagesRequestBody,
    ) -> Any:
        return request.app.state.backend_service.update_editor_images(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            items=payload.items,
        )

    @app.put("/api/topics/{topic_id}/copy-draft")
    async def update_copy_draft(
        request: Request,
        topic_id: str,
        payload: UpdateCopyDraftRequestBody,
    ) -> CopyDraftResponse:
        return request.app.state.backend_service.update_copy_draft(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            title=payload.title,
            body=payload.body,
        )

    @app.post("/api/topics/{topic_id}/copy-draft/polish-selection")
    async def polish_copy_draft_selection(
        request: Request,
        topic_id: str,
        payload: PolishCopyDraftSelectionRequestBody,
    ) -> CopyDraftSelectionPolishResponse:
        return request.app.state.backend_service.polish_copy_draft_selection(
            topic_id=topic_id,
            topic_title=payload.topic_title,
            selected_text=payload.selected_text,
            instruction=payload.instruction,
            document_markdown=payload.document_markdown,
        )

    @app.delete("/api/topics/{topic_id}/image-results/{image_id}")
    async def delete_image_result(
        request: Request,
        topic_id: str,
        image_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.delete_image_result(
            topic_id=topic_id,
            topic_title=topic_title,
            image_id=image_id,
        )

    @app.delete("/api/topics/{topic_id}/posts/{post_id}")
    async def delete_candidate_post(
        request: Request,
        topic_id: str,
        post_id: str,
        topic_title: Annotated[str, Query(min_length=1)],
    ) -> Any:
        return request.app.state.backend_service.delete_candidate_post(
            topic_id=topic_id,
            topic_title=topic_title,
            post_id=post_id,
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
