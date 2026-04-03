from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any, cast

from httpx import ASGITransport, AsyncClient

from agent.loop_runner import LoopModelResponse
from agent.models import PromptMessage, ToolCallPayload
from agent.runtime import AgentRuntime
from agent.session.models import SessionMessage
from agent.time_utils import now_local
from agent.tools.base import Tool, ToolArguments, ToolDefinition, ToolExecutionContext
from backend.app import create_app
from backend.topic_truth_models import (
    CopyDraftRecord,
    EditorImageRecord,
    EditorImagesDocument,
    PatternSummaryRecord,
    PostContent,
    PostDetail,
    PostMediaAsset,
    PostMetrics,
)
from backend.topic_truth_store import SessionWorkspaceStore


class StubModelClient:
    def complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
        tool_choice: object | None = None,
    ) -> LoopModelResponse:
        _ = tool_definitions
        _ = tool_choice
        latest_user = messages[-1].content.split("\n\n")[-1]
        return LoopModelResponse(content=f"后端测试回复：{latest_user}")


class StreamingToolModelClient:
    def __init__(self) -> None:
        self.calls = 0

    def complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
        tool_choice: object | None = None,
    ) -> LoopModelResponse:
        _ = messages
        _ = tool_definitions
        _ = tool_choice
        if self.calls == 0:
            self.calls += 1
            return LoopModelResponse(
                tool_calls=[
                    ToolCallPayload(
                        id="call-1",
                        name="echo_tool",
                        arguments={"keyword": "openclaw"},
                    )
                ]
            )
        return LoopModelResponse(content="流式最终回复：openclaw")


class SelectionPolishModelClient:
    def complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
        tool_choice: object | None = None,
    ) -> LoopModelResponse:
        _ = tool_definitions
        _ = tool_choice
        latest_user = messages[-1].content
        if "[Selected Text]" in latest_user:
            return LoopModelResponse(
                content=json.dumps(
                    {
                        "replacement_text": "润色后的选中文本",
                        "message": "已按你的要求润色选中内容。",
                    },
                    ensure_ascii=False,
                )
            )
        return LoopModelResponse(content="默认回复")


class EchoToolArguments(ToolArguments):
    keyword: str


class EchoTool(Tool):
    name = "echo_tool"
    description = "Echo one keyword."
    arguments_model = EchoToolArguments

    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        _ = context
        parsed = cast(EchoToolArguments, arguments)
        return {"keyword": parsed.keyword, "status": "ok"}


def make_client(tmp_path: Path) -> AsyncClient:
    runtime = AgentRuntime(
        project_root=tmp_path,
        data_root=tmp_path / "data",
        model_client=StubModelClient(),
    )
    app = create_app(
        runtime=runtime,
        project_root=tmp_path,
        data_root=tmp_path / "data",
        allowed_origins=["http://127.0.0.1:5173"],
        trace_mode="off",
    )
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def make_streaming_client(tmp_path: Path) -> AsyncClient:
    runtime = AgentRuntime(
        project_root=tmp_path,
        data_root=tmp_path / "data",
        model_client=StreamingToolModelClient(),
    )
    runtime.tools_registry.register(EchoTool())
    app = create_app(
        runtime=runtime,
        project_root=tmp_path,
        data_root=tmp_path / "data",
        allowed_origins=["http://127.0.0.1:5173"],
        trace_mode="off",
    )
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def make_selection_polish_client(tmp_path: Path) -> AsyncClient:
    runtime = AgentRuntime(
        project_root=tmp_path,
        data_root=tmp_path / "data",
        model_client=SelectionPolishModelClient(),
    )
    app = create_app(
        runtime=runtime,
        project_root=tmp_path,
        data_root=tmp_path / "data",
        allowed_origins=["http://127.0.0.1:5173"],
        trace_mode="off",
    )
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def seed_session_context(tmp_path: Path, session_id: str) -> None:
    now = now_local()
    store = SessionWorkspaceStore(tmp_path / "data")
    source_asset = tmp_path / "image-01.jpg"
    source_asset.write_bytes(b"topic-image")
    source_asset_2 = tmp_path / "image-02.jpg"
    source_asset_2.write_bytes(b"topic-image-2")

    store.write_post_detail(
        session_id,
        "post-1",
        PostDetail(
            post_id="post-1",
            title="CLI 正在回归",
            post_type="image_text",
            url="https://example.com/post-1",
            content=PostContent(text="正文详情内容"),
            metrics=PostMetrics(likes=10, favorites=20, comments=3),
            media=[
                PostMediaAsset(
                    asset_id="image-01",
                    kind="image",
                    path="assets/image-01.jpg",
                    order=1,
                ),
                PostMediaAsset(
                    asset_id="image-02",
                    kind="image",
                    path="assets/image-02.jpg",
                    order=2,
                ),
            ],
            updated_at=now,
        ),
    )
    store.copy_post_asset(
        session_id,
        "post-1",
        source_asset,
        target_name="image-01.jpg",
    )
    store.copy_post_asset(
        session_id,
        "post-1",
        source_asset_2,
        target_name="image-02.jpg",
    )
    store.write_pattern_summary(
        session_id,
        PatternSummaryRecord(
            title_patterns=["场景 + 结论"],
            body_patterns=["问题", "拆解"],
            keywords=["CLI", "Agent"],
            updated_at=now,
        ),
    )
    store.write_copy_draft(
        session_id,
        CopyDraftRecord(
            title="通勤穿搭别乱买，4 件基础款就够了",
            body="先讲场景，再给公式，最后补一个可直接照搬的版本。",
            source_summary_version=now.isoformat(),
            updated_at=now,
        ),
    )


def test_workspace_first_access_creates_session_and_mapping(tmp_path: Path) -> None:
    async def run() -> dict[str, object]:
        async with make_client(tmp_path) as client:
            response = await client.get(
                "/api/topics/topic-1/workspace",
                params={"topic_title": "话题一"},
            )

            assert response.status_code == 200
            payload = response.json()
            assert payload["topic_id"] == "topic-1"
            assert payload["topic_title"] == "话题一"
            assert payload["messages"] == []
            return payload

    payload = asyncio.run(run())

    mapping_path = tmp_path / "data" / "topic-index.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    assert mapping["topic-1"]["session_id"] == payload["session_id"]
    session_id = cast(str, payload["session_id"])
    topic_meta_path = tmp_path / "data" / "sessions" / session_id / "topic.json"
    topic_meta = json.loads(topic_meta_path.read_text(encoding="utf-8"))
    assert topic_meta["topic_id"] == "topic-1"
    assert topic_meta["title"] == "话题一"


def test_workspace_reuses_active_session_and_updates_title(tmp_path: Path) -> None:
    async def run() -> tuple[dict[str, object], dict[str, object]]:
        async with make_client(tmp_path) as client:
            first = (
                await client.get(
                    "/api/topics/topic-1/workspace",
                    params={"topic_title": "旧标题"},
                )
            ).json()
            second = (
                await client.get(
                    "/api/topics/topic-1/workspace",
                    params={"topic_title": "新标题"},
                )
            ).json()
            return first, second

    first, second = asyncio.run(run())

    assert first["session_id"] == second["session_id"]
    assert second["topic_title"] == "新标题"

    session_id = cast(str, second["session_id"])
    topic_meta_path = tmp_path / "data" / "sessions" / session_id / "topic.json"
    topic_meta = json.loads(topic_meta_path.read_text(encoding="utf-8"))
    assert topic_meta["title"] == "新标题"


def test_run_returns_messages_and_filters_tool_messages(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            response = await client.post(
                "/api/topics/topic-1/runs",
                json={
                    "topic_title": "话题一",
                    "user_input": "帮我总结一下",
                },
            )

            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert payload["last_run"]["final_text"] == "后端测试回复：帮我总结一下"
    assert [message["role"] for message in payload["messages"]] == ["user", "agent"]
    assert payload["messages"][0]["text"] == "帮我总结一下"
    assert payload["messages"][1]["text"] == "后端测试回复：帮我总结一下"
    assert payload["trace_file"] is None


def test_run_returns_trace_file_and_writes_session_trace_when_enabled(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        runtime = AgentRuntime(
            project_root=tmp_path,
            data_root=tmp_path / "data",
            model_client=StubModelClient(),
        )
        app = create_app(
            runtime=runtime,
            project_root=tmp_path,
            data_root=tmp_path / "data",
            allowed_origins=["http://127.0.0.1:5173"],
            trace_mode="full",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/topics/topic-1/runs",
                json={
                    "topic_title": "话题一",
                    "user_input": "帮我总结一下",
                },
            )
            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    trace_path = Path(cast(str, payload["trace_file"]))
    assert trace_path.exists()
    content = trace_path.read_text(encoding="utf-8")
    assert "trace_mode: full" in content
    assert "final_text:" in content
    assert "后端测试回复：帮我总结一下" in content


def test_messages_endpoint_returns_current_session_messages(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            await client.post(
                "/api/topics/topic-1/runs",
                json={
                    "topic_title": "话题一",
                    "user_input": "继续执行",
                },
            )

            response = await client.get(
                "/api/topics/topic-1/messages",
                params={"topic_title": "话题一"},
            )

            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert [message["role"] for message in payload["messages"]] == ["user", "agent"]


def test_messages_endpoint_returns_only_final_answer_with_tool_summary(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        runtime = AgentRuntime(
            project_root=tmp_path,
            data_root=tmp_path / "data",
            model_client=StubModelClient(),
        )
        app = create_app(
            runtime=runtime,
            project_root=tmp_path,
            data_root=tmp_path / "data",
            allowed_origins=["http://127.0.0.1:5173"],
            trace_mode="off",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            first = await client.get(
                "/api/topics/topic-1/workspace",
                params={"topic_title": "话题一"},
            )
            session_id = cast(str, first.json()["session_id"])
            session = runtime.session_manager.require(session_id)
            session.add_message(SessionMessage(role="user", content="请帮我搜集"))
            session.add_message(
                SessionMessage(
                    role="assistant",
                    content="我先搜索一下",
                    tool_calls=[
                        ToolCallPayload(
                            id="call-1",
                            name="xhs-explore",
                            arguments={"keyword": "openclaw", "note_type": "图文"},
                        )
                    ],
                )
            )
            session.add_message(
                SessionMessage(
                    role="tool",
                    name="xhs-explore",
                    tool_call_id="call-1",
                    content="已返回 3 条帖子",
                )
            )
            session.add_message(SessionMessage(role="assistant", content="最终只保留这 3 条帖子。"))
            runtime.session_manager.save(session)

            response = await client.get(
                "/api/topics/topic-1/messages",
                params={"topic_title": "话题一"},
            )

            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert [message["role"] for message in payload["messages"]] == ["user", "agent"]
    assert payload["messages"][1]["text"] == "最终只保留这 3 条帖子。"
    assert payload["messages"][1]["tool_summary"] == [
        {
            "name": "xhs-explore",
            "arguments_summary": '{"keyword": "openclaw", "note_type": "图文"}',
            "result_summary": "已返回 3 条帖子",
        }
    ]


def test_update_editor_images_accepts_camel_case_payload(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            created = await client.post(
                "/api/topics",
                json={"title": "图片话题", "description": ""},
            )
            topic = cast(dict[str, Any], created.json())
            response = await client.put(
                f"/api/topics/{topic['topic_id']}/editor-images",
                json={
                    "topicTitle": "图片话题",
                    "items": [
                        {
                            "id": "editor-1",
                            "order": 1,
                            "sourceType": "material",
                            "sourcePostId": "post-1",
                            "sourceImageId": "image-1",
                            "imagePath": "posts/post-1/assets/image-01.png",
                            "alt": "测试图片",
                        }
                    ],
                },
            )
            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert payload["items"][0]["sourceType"] == "material"
    assert payload["items"][0]["sourcePostId"] == "post-1"
    assert payload["items"][0]["sourceImageId"] == "image-1"
    assert payload["items"][0]["imagePath"] == "posts/post-1/assets/image-01.png"


def test_update_copy_draft_persists_workspace_file(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            created = await client.post(
                "/api/topics",
                json={"title": "文案话题", "description": ""},
            )
            topic = cast(dict[str, Any], created.json())
            response = await client.put(
                f"/api/topics/{topic['topic_id']}/copy-draft",
                json={
                    "topic_title": "文案话题",
                    "title": "新的标题",
                    "body": "## 第一行\n\n- 第二行",
                },
            )
            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert payload["copy_draft"]["title"] == "新的标题"
    assert payload["copy_draft"]["body"] == "## 第一行\n\n- 第二行"


def test_polish_copy_draft_selection_returns_replacement_and_only_appends_agent_message(
    tmp_path: Path,
) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any]]:
        async with make_selection_polish_client(tmp_path) as client:
            created = await client.post(
                "/api/topics",
                json={"title": "润色话题", "description": ""},
            )
            topic = cast(dict[str, Any], created.json())
            response = await client.post(
                f"/api/topics/{topic['topic_id']}/copy-draft/polish-selection",
                json={
                    "topic_title": "润色话题",
                    "selected_text": "原始选中文本",
                    "instruction": "更口语一点",
                    "document_markdown": "# 标题\n\n原始选中文本",
                },
            )
            assert response.status_code == 200
            messages_response = await client.get(
                f"/api/topics/{topic['topic_id']}/messages",
                params={"topic_title": "润色话题"},
            )
            assert messages_response.status_code == 200
            return (
                cast(dict[str, Any], response.json()),
                cast(dict[str, Any], messages_response.json()),
            )

    payload, messages_payload = asyncio.run(run())
    assert payload["replacement_text"] == "润色后的选中文本"
    assert payload["message"] == "已按你的要求润色选中内容。"
    assert [message["role"] for message in messages_payload["messages"]] == ["user", "agent"]
    assert messages_payload["messages"][0]["text"] == "更口语一点"
    assert messages_payload["messages"][1]["text"] == "已按你的要求润色选中内容。"


def test_polish_copy_draft_selection_rejects_empty_fields(tmp_path: Path) -> None:
    async def run() -> tuple[int, dict[str, Any], int, dict[str, Any], int, dict[str, Any]]:
        async with make_selection_polish_client(tmp_path) as client:
            created = await client.post(
                "/api/topics",
                json={"title": "润色话题", "description": ""},
            )
            topic = cast(dict[str, Any], created.json())
            empty_selection = await client.post(
                f"/api/topics/{topic['topic_id']}/copy-draft/polish-selection",
                json={
                    "topic_title": "润色话题",
                    "selected_text": "",
                    "instruction": "更口语一点",
                    "document_markdown": "# 标题\n\n正文",
                },
            )
            empty_instruction = await client.post(
                f"/api/topics/{topic['topic_id']}/copy-draft/polish-selection",
                json={
                    "topic_title": "润色话题",
                    "selected_text": "正文",
                    "instruction": "",
                    "document_markdown": "# 标题\n\n正文",
                },
            )
            empty_document = await client.post(
                f"/api/topics/{topic['topic_id']}/copy-draft/polish-selection",
                json={
                    "topic_title": "润色话题",
                    "selected_text": "正文",
                    "instruction": "更口语一点",
                    "document_markdown": "",
                },
            )
            return (
                empty_selection.status_code,
                cast(dict[str, Any], empty_selection.json()),
                empty_instruction.status_code,
                cast(dict[str, Any], empty_instruction.json()),
                empty_document.status_code,
                cast(dict[str, Any], empty_document.json()),
            )

    (
        empty_selection_status,
        empty_selection_payload,
        empty_instruction_status,
        empty_instruction_payload,
        empty_document_status,
        empty_document_payload,
    ) = asyncio.run(run())
    assert empty_selection_status == 422
    assert empty_selection_payload["error_code"] == "invalid_request"
    assert empty_instruction_status == 422
    assert empty_instruction_payload["error_code"] == "invalid_request"
    assert empty_document_status == 422
    assert empty_document_payload["error_code"] == "invalid_request"


def test_streaming_run_endpoint_emits_ordered_sse_events(tmp_path: Path) -> None:
    async def run() -> str:
        async with make_streaming_client(tmp_path) as client:
            async with client.stream(
                "POST",
                "/api/topics/topic-1/runs/stream",
                json={
                    "topic_title": "话题一",
                    "user_input": "帮我流式执行",
                },
            ) as response:
                assert response.status_code == 200
                chunks: list[str] = []
                async for chunk in response.aiter_text():
                    chunks.append(chunk)
                return "".join(chunks)

    payload = asyncio.run(run())
    assert "event: run_started" in payload
    assert "event: tool_call_started" in payload
    assert "event: tool_call_finished" in payload
    assert "event: assistant_delta" in payload
    assert "event: run_completed" in payload
    assert "流式最终回复：openclaw" in payload


def test_context_endpoint_returns_candidate_posts_and_pattern_summary(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            workspace_response = await client.get(
                "/api/topics/topic-1/workspace",
                params={"topic_title": "话题一"},
            )
            session_id = cast(dict[str, Any], workspace_response.json())["session_id"]
            seed_session_context(tmp_path, session_id)
            response = await client.get(
                "/api/topics/topic-1/context",
                params={"topic_title": "话题一"},
            )
            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert payload["topic_id"] == "topic-1"
    assert payload["candidate_posts"][0]["id"] == "post-1"
    assert payload["candidate_posts"][0]["bodyText"] == "正文详情内容"
    assert (
        payload["candidate_posts"][0]["imageUrl"]
        == "/api/topics/topic-1/assets/posts/post-1/assets/image-01.jpg"
    )
    assert [image["id"] for image in payload["candidate_posts"][0]["images"]] == [
        "image-01",
        "image-02",
    ]
    assert payload["candidate_posts"][0]["images"][1]["imageUrl"] == (
        "/api/topics/topic-1/assets/posts/post-1/assets/image-02.jpg"
    )
    assert payload["candidate_posts"][0]["heat"] == "收藏 20 · 点赞 10 · 评论 3"
    assert payload["materials"] == []
    assert payload["pattern_summary"]["titlePatterns"] == ["场景 + 结论"]
    assert payload["copy_draft"]["title"] == "通勤穿搭别乱买，4 件基础款就够了"


def test_materials_endpoints_create_delete_and_surface_in_context(tmp_path: Path) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        async with make_client(tmp_path) as client:
            created = await client.post(
                "/api/topics",
                json={"title": "素材话题", "description": ""},
            )
            topic = cast(dict[str, Any], created.json())

            text_response = await client.post(
                f"/api/topics/{topic['topic_id']}/materials/text",
                json={
                    "topic_title": "素材话题",
                    "title": "选题要求",
                    "text_content": "强调低预算和高效率",
                },
            )
            assert text_response.status_code == 200

            image_response = await client.post(
                f"/api/topics/{topic['topic_id']}/materials/images",
                json={
                    "topic_title": "素材话题",
                    "items": [
                        {
                            "filename": "cover.png",
                            "content_type": "image/png",
                            "content_base64": base64.b64encode(b"fake-image").decode("ascii"),
                        }
                    ],
                },
            )
            assert image_response.status_code == 200

            materials_response = await client.get(
                f"/api/topics/{topic['topic_id']}/materials",
                params={"topic_title": "素材话题"},
            )
            context_response = await client.get(
                f"/api/topics/{topic['topic_id']}/context",
                params={"topic_title": "素材话题"},
            )
            assert materials_response.status_code == 200
            assert context_response.status_code == 200
            image_material_id = cast(dict[str, Any], image_response.json())["items"][1]["id"]
            delete_response = await client.delete(
                f"/api/topics/{topic['topic_id']}/materials/{image_material_id}",
                params={"topic_title": "素材话题"},
            )
            assert delete_response.status_code == 200
            return (
                cast(dict[str, Any], image_response.json()),
                cast(dict[str, Any], materials_response.json()),
                cast(dict[str, Any], context_response.json()),
                cast(dict[str, Any], delete_response.json()),
            )

    image_payload, materials_payload, context_payload, delete_payload = asyncio.run(run())
    assert [item["type"] for item in image_payload["items"]] == ["text", "image"]
    assert materials_payload["items"][0]["title"] == "选题要求"
    assert materials_payload["items"][1]["imagePath"].startswith("materials/")
    assert context_payload["materials"][1]["imageUrl"].startswith("/api/topics/")
    assert delete_payload["deleted_material_id"] == image_payload["items"][1]["id"]


def test_delete_candidate_post_endpoint_removes_post_and_related_editor_images(
    tmp_path: Path,
) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any]]:
        async with make_client(tmp_path) as client:
            workspace_response = await client.get(
                "/api/topics/topic-1/workspace",
                params={"topic_title": "话题一"},
            )
            session_id = cast(dict[str, Any], workspace_response.json())["session_id"]
            seed_session_context(tmp_path, session_id)
            store = SessionWorkspaceStore(tmp_path / "data")
            now = now_local()
            store.write_post_detail(
                session_id,
                "post-2",
                PostDetail(
                    post_id="post-2",
                    title="Agent 调研工作流",
                    post_type="image_text",
                    url="https://example.com/post-2",
                    content=PostContent(text="另一条正文"),
                    metrics=PostMetrics(likes=1, favorites=2, comments=3),
                    updated_at=now,
                ),
            )
            store.write_editor_images(
                session_id,
                EditorImagesDocument(
                    items=[
                        EditorImageRecord(
                            id="editor-1",
                            order=1,
                            source_type="material",
                            source_post_id="post-2",
                            source_image_id="image-01",
                            image_path="posts/post-2/assets/image-01.jpg",
                            alt="待删除素材图",
                        )
                    ],
                    updated_at=now,
                ),
            )

            delete_response = await client.delete(
                "/api/topics/topic-1/posts/post-2",
                params={"topic_title": "话题一"},
            )
            context_response = await client.get(
                "/api/topics/topic-1/context",
                params={"topic_title": "话题一"},
            )
            assert delete_response.status_code == 200
            assert context_response.status_code == 200
            return (
                cast(dict[str, Any], delete_response.json()),
                cast(dict[str, Any], context_response.json()),
            )

    delete_payload, context_payload = asyncio.run(run())
    assert delete_payload["deleted_post_id"] == "post-2"
    assert [item["id"] for item in context_payload["candidate_posts"]] == ["post-1"]
    assert context_payload["editor_images"] == []


def test_topic_asset_endpoint_serves_copied_asset(tmp_path: Path) -> None:
    async def run() -> tuple[bytes, str]:
        async with make_client(tmp_path) as client:
            workspace_response = await client.get(
                "/api/topics/topic-1/workspace",
                params={"topic_title": "话题一"},
            )
            session_id = cast(dict[str, Any], workspace_response.json())["session_id"]
            seed_session_context(tmp_path, session_id)
            response = await client.get(
                "/api/topics/topic-1/assets/posts/post-1/assets/image-01.jpg"
            )
            assert response.status_code == 200
            return response.content, response.headers["content-type"]

    payload, content_type = asyncio.run(run())
    assert payload == b"topic-image"
    assert content_type == "image/jpeg"


def test_reset_clears_session_workspace_data(tmp_path: Path) -> None:
    async def run() -> tuple[str, dict[str, Any], dict[str, Any]]:
        async with make_client(tmp_path) as client:
            workspace_response = await client.get(
                "/api/topics/topic-1/workspace",
                params={"topic_title": "话题一"},
            )
            session_id = cast(dict[str, Any], workspace_response.json())["session_id"]
            seed_session_context(tmp_path, session_id)
            before = await client.get(
                "/api/topics/topic-1/context",
                params={"topic_title": "话题一"},
            )
            reset_response = await client.post(
                "/api/topics/topic-1/reset",
                json={"topic_title": "话题一"},
            )
            after = await client.get(
                "/api/topics/topic-1/context",
                params={"topic_title": "话题一"},
            )
            assert reset_response.status_code == 200
            assert before.status_code == 200
            assert after.status_code == 200
            return (
                session_id,
                cast(dict[str, Any], before.json()),
                cast(dict[str, Any], after.json()),
            )

    session_id, before_payload, after_payload = asyncio.run(run())
    assert before_payload["candidate_posts"]
    assert after_payload["candidate_posts"] == []
    assert after_payload["pattern_summary"] is None
    assert not (
        tmp_path / "data" / "sessions" / session_id / "workspace"
    ).exists()


def test_reset_clears_current_session_messages(tmp_path: Path) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any]]:
        async with make_client(tmp_path) as client:
            run_response = (
                await client.post(
                    "/api/topics/topic-1/runs",
                    json={
                        "topic_title": "话题一",
                        "user_input": "继续执行",
                    },
                )
            ).json()

            reset_response = await client.post(
                "/api/topics/topic-1/reset",
                json={"topic_title": "话题一"},
            )

            assert reset_response.status_code == 200
            return cast(dict[str, Any], run_response), cast(dict[str, Any], reset_response.json())

    run_response, payload = asyncio.run(run())
    assert payload["session_id"] == run_response["session_id"]
    assert payload["messages"] == []


def test_validation_errors_return_error_response(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            response = await client.post(
                "/api/topics/topic-1/runs",
                json={
                    "topic_title": "",
                    "user_input": "",
                },
            )

            assert response.status_code == 422
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert payload["error_code"] == "invalid_request"
    assert payload["message"] == "请求参数不合法。"


def test_cors_preflight_is_enabled_for_local_frontend(tmp_path: Path) -> None:
    async def run() -> tuple[int, str | None]:
        async with make_client(tmp_path) as client:
            response = await client.options(
                "/api/topics/topic-1/workspace?topic_title=话题一",
                headers={
                    "Origin": "http://127.0.0.1:5173",
                    "Access-Control-Request-Method": "GET",
                },
            )

            return response.status_code, response.headers.get("access-control-allow-origin")

    status_code, allow_origin = asyncio.run(run())
    assert status_code == 200
    assert allow_origin == "http://127.0.0.1:5173"
