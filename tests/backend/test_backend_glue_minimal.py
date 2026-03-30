from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

from httpx import ASGITransport, AsyncClient

from agent.loop_runner import LoopModelResponse
from agent.models import PromptMessage
from agent.runtime import AgentRuntime
from agent.time_utils import now_local
from agent.tools.registry import ToolDefinition
from backend.app import create_app
from backend.topic_truth_models import (
    PatternSummaryRecord,
    PostContent,
    PostDetail,
    PostMediaAsset,
    PostMetrics,
    SelectedPostRecord,
    SelectedPostsDocument,
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
    store.write_selected_posts(
        session_id,
        SelectedPostsDocument(
            items=[SelectedPostRecord(post_id="post-1", manual_order=1)],
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
    assert payload["pattern_summary"]["titlePatterns"] == ["场景 + 结论"]


def test_update_selected_posts_endpoint_persists_selection_order(tmp_path: Path) -> None:
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

            update_response = await client.put(
                "/api/topics/topic-1/selected-posts",
                json={
                    "topic_title": "话题一",
                    "post_ids": ["post-2", "post-1"],
                },
            )
            context_response = await client.get(
                "/api/topics/topic-1/context",
                params={"topic_title": "话题一"},
            )
            assert update_response.status_code == 200
            assert context_response.status_code == 200
            return (
                cast(dict[str, Any], update_response.json()),
                cast(dict[str, Any], context_response.json()),
            )

    update_payload, context_payload = asyncio.run(run())
    assert [item["post_id"] for item in update_payload["items"]] == ["post-2", "post-1"]
    selected_posts = {item["id"]: item for item in context_payload["candidate_posts"]}
    assert selected_posts["post-2"]["selected"] is True
    assert selected_posts["post-2"]["manualOrder"] == 1
    assert selected_posts["post-1"]["manualOrder"] == 2


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
