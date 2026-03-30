from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

from httpx import ASGITransport, AsyncClient

from agent.loop_runner import LoopModelResponse
from agent.models import PromptMessage
from agent.runtime import AgentRuntime
from agent.tools.registry import ToolDefinition
from backend.app import create_app


class StubModelClient:
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
        return LoopModelResponse(content="ok")


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


def test_create_topic_generates_topic_id_and_persists_files(tmp_path: Path) -> None:
    async def run() -> dict[str, Any]:
        async with make_client(tmp_path) as client:
            response = await client.post(
                "/api/topics",
                json={
                    "title": "新的话题",
                    "description": "测试描述",
                },
            )
            assert response.status_code == 200
            return cast(dict[str, Any], response.json())

    payload = asyncio.run(run())
    assert payload["topic_id"].startswith("topic_")
    assert len(payload["topic_id"]) == 32
    assert payload["session_id"]

    topic_index = json.loads(
        (tmp_path / "data" / "topic-index.json").read_text(encoding="utf-8")
    )
    topic_meta = json.loads(
        (tmp_path / "data" / "sessions" / payload["session_id"] / "topic.json").read_text(
            encoding="utf-8"
        )
    )

    assert topic_meta["title"] == "新的话题"
    assert topic_meta["description"] == "测试描述"
    assert topic_index[payload["topic_id"]]["session_id"] == payload["session_id"]
    assert (tmp_path / "data" / "sessions" / payload["session_id"]).exists()


def test_list_topics_returns_descending_updated_at(tmp_path: Path) -> None:
    async def run() -> list[dict[str, Any]]:
        async with make_client(tmp_path) as client:
            await client.post("/api/topics", json={"title": "第一个话题"})
            await client.post("/api/topics", json={"title": "第二个话题"})
            response = await client.get("/api/topics")
            assert response.status_code == 200
            return cast(dict[str, list[dict[str, Any]]], response.json())["items"]

    items = asyncio.run(run())
    assert len(items) == 2
    assert items[0]["title"] == "第二个话题"
    assert items[1]["title"] == "第一个话题"


def test_delete_topic_hard_deletes_topic_and_session(tmp_path: Path) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any]]:
        async with make_client(tmp_path) as client:
            created = cast(
                dict[str, Any],
                (
                    await client.post(
                        "/api/topics",
                        json={"title": "待删除话题"},
                    )
                ).json(),
            )
            deleted = cast(
                dict[str, Any],
                (await client.delete(f"/api/topics/{created['topic_id']}")).json(),
            )
            return created, deleted

    created, deleted = asyncio.run(run())
    assert deleted["deleted_topic_id"] == created["topic_id"]
    topic_index_path = tmp_path / "data" / "topic-index.json"
    if topic_index_path.exists():
        payload = json.loads(topic_index_path.read_text(encoding="utf-8"))
        assert created["topic_id"] not in payload
    assert not (tmp_path / "data" / "sessions" / created["session_id"]).exists()


def test_delete_missing_topic_returns_404(tmp_path: Path) -> None:
    async def run() -> tuple[int, dict[str, Any]]:
        async with make_client(tmp_path) as client:
            response = await client.delete("/api/topics/topic_missing")
            return response.status_code, cast(dict[str, Any], response.json())

    status_code, payload = asyncio.run(run())
    assert status_code == 404
    assert payload["error_code"] == "topic_not_found"
