from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

from httpx import ASGITransport, AsyncClient

from agent.loop_runner import LoopModelResponse
from agent.models import PromptMessage
from agent.runtime import AgentRuntime
from agent.skills.loader import SkillsLoader
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


def _write_skill(
    skill_dir: Path,
    *,
    description: str,
    metadata: str | None = None,
    body: str = "这是一个技能正文。",
) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = [
        "---",
        f"description: {description}",
    ]
    if metadata is not None:
        frontmatter.append("metadata: |")
        frontmatter.extend(f"  {line}" for line in metadata.splitlines())
    frontmatter.append("---")
    frontmatter.append("")
    frontmatter.append(body)
    (skill_dir / "SKILL.md").write_text("\n".join(frontmatter), encoding="utf-8")


def make_client(tmp_path: Path) -> AsyncClient:
    builtin_skills_dir = tmp_path / "skills"
    _write_skill(
        builtin_skills_dir / "builtin-skill",
        description="builtin skill",
        body="builtin 正文",
    )
    _write_skill(
        builtin_skills_dir / "bundle-parent",
        description="bundle parent",
        body="bundle parent 正文",
    )
    _write_skill(
        builtin_skills_dir / "bundle-parent" / "skills" / "bundle-child",
        description="bundle child",
        body="bundle child 正文",
    )
    _write_skill(
        builtin_skills_dir / "missing-skill",
        description="missing skill",
        metadata='{"nanobot":{"requires":{"bins":["definitely-missing-binary"]}}}',
        body="缺依赖 skill 正文",
    )

    workspace_skills_dir = tmp_path / "data" / "sessions" / "session-workspace" / "skills"
    _write_skill(
        workspace_skills_dir / "workspace-skill",
        description="workspace skill",
        body="workspace 正文",
    )

    runtime = AgentRuntime(
        project_root=tmp_path,
        data_root=tmp_path / "data",
        model_client=StubModelClient(),
        skills_loader=SkillsLoader(builtin_skills_dir=builtin_skills_dir),
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


def test_skills_endpoint_returns_builtin_workspace_and_nested_skills(tmp_path: Path) -> None:
    async def run() -> list[dict[str, Any]]:
        async with make_client(tmp_path) as client:
            response = await client.get("/api/skills")
            assert response.status_code == 200
            return cast(dict[str, list[dict[str, Any]]], response.json())["items"]

    items = asyncio.run(run())
    names = [item["name"] for item in items]
    assert "builtin-skill" in names
    assert "bundle-parent" in names
    assert "bundle-child" in names
    assert "workspace-skill" in names
    assert "missing-skill" in names


def test_skills_endpoint_includes_availability_and_content_summary(tmp_path: Path) -> None:
    async def run() -> list[dict[str, Any]]:
        async with make_client(tmp_path) as client:
            response = await client.get("/api/skills")
            assert response.status_code == 200
            return cast(dict[str, list[dict[str, Any]]], response.json())["items"]

    items = asyncio.run(run())
    by_name = {item["name"]: item for item in items}

    assert by_name["builtin-skill"]["available"] is True
    assert by_name["builtin-skill"]["content_summary"] == "builtin 正文"

    assert by_name["missing-skill"]["available"] is False
    assert by_name["missing-skill"]["requires"] == ["CLI: definitely-missing-binary"]
    assert "缺依赖 skill 正文" in by_name["missing-skill"]["content_summary"]

    assert by_name["workspace-skill"]["source"] == "workspace"
