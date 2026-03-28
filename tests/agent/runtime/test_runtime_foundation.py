from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast

import pytest

from agent.context_builder import ContextBuilder
from agent.errors import SessionNotFoundError
from agent.loop_runner import LoopRunner
from agent.memory.store import MemoryStore
from agent.models import PromptMessage, RunRequest, RunResult, ToolCallPayload, ToolCallSummary
from agent.runtime import AgentRuntime
from agent.session.models import SessionMessage
from agent.skills.loader import SkillsLoader


class AnySession(Protocol):
    workspace_path: Path

    def get_history(self) -> list[PromptMessage]:
        """Return the session history slice."""
        ...


class CapturingLoopRunner(LoopRunner):
    def __init__(self) -> None:
        self.captured_messages: list[PromptMessage] | None = None
        self.captured_request: RunRequest | None = None

    def run(self, **kwargs: object) -> RunResult:  # type: ignore[override]
        self.captured_request = cast(RunRequest, kwargs["request"])
        session = cast(AnySession, kwargs["session"])
        context_builder = cast(ContextBuilder, kwargs["context_builder"])
        skills_loader = cast(SkillsLoader, kwargs["skills_loader"])
        memory_context = MemoryStore(session.workspace_path).get_memory_context()
        system_prompt = context_builder.build_system_prompt(
            memory_context=memory_context,
            always_skills=skills_loader.load_always_skills_for_context(
                workspace_path=session.workspace_path
            ),
            skills_summary=skills_loader.build_skills_summary(
                workspace_path=session.workspace_path
            ),
        )
        self.captured_messages = context_builder.build_messages(
            system_prompt=system_prompt,
            session_history=session.get_history(),
            request=self.captured_request,
            workspace_path=session.workspace_path,
        )
        request = cast(RunRequest, kwargs["request"])
        return RunResult(
            session_id=request.session_id,
            final_text="done",
            tool_calls=[
                ToolCallSummary(
                    name="read_file",
                    arguments_summary="path=notes.md",
                    result_summary="ok",
                )
            ],
            artifacts=["data/sessions/demo/result.md"],
        )


def test_runtime_initializes_with_fixed_components(tmp_path: Path) -> None:
    runtime = AgentRuntime(project_root=tmp_path)

    assert runtime.session_manager is not None
    assert runtime.context_builder is not None
    assert runtime.skills_loader is not None
    assert runtime.tools_registry is not None
    assert runtime.loop_runner is not None


def test_create_session_generates_session_id_and_workspace_path(tmp_path: Path) -> None:
    runtime = AgentRuntime(project_root=tmp_path)

    snapshot = runtime.create_session(topic="早八穿搭", metadata={"source": "test"})

    assert snapshot.session_id
    assert snapshot.topic == "早八穿搭"
    assert snapshot.metadata == {"source": "test"}
    assert snapshot.workspace_path == tmp_path / "data" / "sessions" / snapshot.session_id


def test_context_builder_builds_system_prompt_in_fixed_order(tmp_path: Path) -> None:
    builder = ContextBuilder(project_root=tmp_path)

    prompt = builder.build_system_prompt(
        memory_context="long-term memory",
        always_skills="always skill body",
        skills_summary="<skills></skills>",
    )

    identity_idx = prompt.index("# Identity")
    memory_idx = prompt.index("# Memory")
    always_skills_idx = prompt.index("# Always Skills")
    skills_summary_idx = prompt.index("# Skills Summary")

    assert identity_idx < memory_idx < always_skills_idx < skills_summary_idx
    assert "# Bootstrap Files" not in prompt
    assert "AGENTS.md" not in prompt
    assert "你只能在当前 session workspace 内工作。" in prompt
    assert "查看目录时优先使用 list_dir" in prompt
    assert "smoke run" not in prompt
    assert "如果你要使用某个 skill，请先读取对应的 SKILL.md" in prompt


def test_context_builder_builds_messages_with_session_history_and_runtime_context(
    tmp_path: Path,
) -> None:
    builder = ContextBuilder(project_root=tmp_path)
    request = RunRequest(
        session_id="sess-1",
        user_input="继续处理这个 session",
        attachments=["/tmp/a.png"],
    )

    messages = builder.build_messages(
        system_prompt="system prompt",
        session_history=[PromptMessage(role="assistant", content="history message")],
        request=request,
        workspace_path=tmp_path / "data" / "sessions" / "sess-1",
    )

    assert [message.role for message in messages] == ["system", "assistant", "user"]
    assert messages[0].content == "system prompt"
    assert messages[1].content == "history message"
    assert "Current Time:" in messages[2].content
    assert "Asia/Shanghai" in messages[2].content
    assert "+0800" in messages[2].content
    assert "Session ID: sess-1" in messages[2].content
    assert f"Workspace Path: {tmp_path / 'data' / 'sessions' / 'sess-1'}" in messages[2].content
    assert "- /tmp/a.png" in messages[2].content


def test_run_delegates_to_loop_runner_and_returns_run_result(tmp_path: Path) -> None:
    loop_runner = CapturingLoopRunner()
    runtime = AgentRuntime(project_root=tmp_path, loop_runner=loop_runner)
    snapshot = runtime.create_session(topic="topic")

    result = runtime.run(
        RunRequest(
            session_id=snapshot.session_id,
            user_input="执行一次",
        )
    )

    assert result.session_id == snapshot.session_id
    assert result.final_text == "done"
    assert result.tool_calls[0].name == "read_file"
    assert loop_runner.captured_request is not None
    assert loop_runner.captured_request.session_id == snapshot.session_id
    assert loop_runner.captured_messages is not None
    assert loop_runner.captured_messages[0].role == "system"
    assert loop_runner.captured_messages[-1].role == "user"


def test_run_uses_session_get_history_not_raw_messages(tmp_path: Path) -> None:
    loop_runner = CapturingLoopRunner()
    runtime = AgentRuntime(project_root=tmp_path, loop_runner=loop_runner)
    session = runtime.session_manager.create(topic="topic")
    session.add_message(
        SessionMessage(
            role="assistant",
            content="准备调用工具",
            tool_calls=[ToolCallPayload(id="call-1", name="read_file", arguments={"path": "a.md"})],
        )
    )
    session.add_message(
        SessionMessage(role="tool", name="read_file", tool_call_id="call-1", content="tool result")
    )
    session.add_message(SessionMessage(role="user", content="保留的用户消息"))
    session.last_consolidated = 1

    runtime.run(
        RunRequest(
            session_id=session.session_id,
            user_input="执行一次",
        )
    )

    assert loop_runner.captured_messages is not None
    history_roles = [message.role for message in loop_runner.captured_messages[1:-1]]
    assert history_roles == ["user"]


def test_missing_session_raises_session_not_found(tmp_path: Path) -> None:
    runtime = AgentRuntime(project_root=tmp_path)

    with pytest.raises(SessionNotFoundError):
        runtime.get_session_snapshot("missing")

    with pytest.raises(SessionNotFoundError):
        runtime.run(RunRequest(session_id="missing", user_input="test"))
