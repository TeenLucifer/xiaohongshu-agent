from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

from agent.context_builder import ContextBuilder
from agent.loop_runner import (
    MAX_ITERATIONS,
    MAX_ITERATIONS_FALLBACK_TEXT,
    LoopModelResponse,
    LoopRunner,
)
from agent.models import PromptMessage, RunRequest, ToolCallPayload
from agent.session.models import Session
from agent.skills.loader import SkillsLoader
from agent.tools.registry import ToolDefinition, ToolsRegistry


class StubTraceSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, object]]] = []

    def record(self, *, category: str, event: str, data: dict[str, object]) -> None:
        self.events.append((category, event, data))


class StubModelClient:
    def __init__(self, responses: list[LoopModelResponse | Exception]) -> None:
        self._responses = responses
        self.calls: list[list[PromptMessage]] = []

    def complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
        tool_choice: object | None = None,
    ) -> LoopModelResponse:
        _ = tool_definitions
        _ = tool_choice
        self.calls.append([message.model_copy(deep=True) for message in messages])
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class StubMemoryConsolidator:
    def __init__(self) -> None:
        self.events: list[str] = []
        self.pre_calls: list[str] = []
        self.post_calls: list[str] = []

    def run_pre_check(self, session: Session) -> bool:
        self.events.append("pre")
        self.pre_calls.append(session.session_id)
        return False

    def schedule_post_check(self, session: Session, on_complete: Any | None = None) -> object:
        self.events.append("post")
        self.post_calls.append(session.session_id)
        if on_complete is not None:
            on_complete(False)
        return object()


class StubSkillsLoader(SkillsLoader):
    def __init__(self, *, summary: str = "<skills></skills>", always: str = "") -> None:
        super().__init__()
        self.summary = summary
        self.always = always

    def build_skills_summary(self, workspace_path: Path | None = None) -> str:
        _ = workspace_path
        return self.summary

    def load_always_skills_for_context(self, workspace_path: Path | None = None) -> str:
        _ = workspace_path
        return self.always


class StubToolsRegistry(ToolsRegistry):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.handlers: dict[str, Any] = {}
        self.definitions = [
            ToolDefinition(name="alpha", description="alpha tool"),
            ToolDefinition(name="beta", description="beta tool"),
        ]

    def list_tool_definitions(self) -> list[ToolDefinition]:
        return self.definitions

    def execute_tool(self, name: str, arguments: dict[str, object]) -> object:
        self.calls.append((name, arguments))
        handler = self.handlers[name]
        return handler(arguments)


def make_session(tmp_path: Path) -> Session:
    return Session(session_id="sess-1", workspace_path=tmp_path / "data" / "sessions" / "sess-1")


def test_loop_runs_memory_hooks_before_and_after_model_call(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    memory = StubMemoryConsolidator()
    model = StubModelClient([LoopModelResponse(content="done")])
    runner = LoopRunner(model_client=model, memory_consolidator=memory)

    result = runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(),
        tools_registry=StubToolsRegistry(),
        save_session=lambda _: None,
    )

    assert result.final_text == "done"
    assert memory.pre_calls == [session.session_id]
    assert memory.post_calls == [session.session_id]
    assert memory.events == ["pre", "post"]


def test_loop_stops_when_model_returns_no_tool_calls(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    model = StubModelClient([LoopModelResponse(content="done")])
    runner = LoopRunner(model_client=model)
    saved_sessions: list[str] = []

    result = runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(),
        tools_registry=StubToolsRegistry(),
        save_session=lambda saved: saved_sessions.append(saved.session_id),
    )

    assert result.final_text == "done"
    assert saved_sessions == [session.session_id]
    assert [message.role for message in session.messages] == ["user", "assistant"]
    assert session.messages[0].content == "执行"


def test_loop_executes_tool_calls_and_reinjects_results_in_order(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    tools = StubToolsRegistry()
    tools.handlers["alpha"] = lambda arguments: f"alpha:{arguments['value']}"
    tools.handlers["beta"] = lambda arguments: f"beta:{arguments['value']}"
    model = StubModelClient(
        [
            LoopModelResponse(
                content="先调工具",
                tool_calls=[
                    ToolCallPayload(id="call-1", name="alpha", arguments={"value": 1}),
                    ToolCallPayload(id="call-2", name="beta", arguments={"value": 2}),
                ],
            ),
            LoopModelResponse(content="done"),
        ]
    )
    runner = LoopRunner(model_client=model)

    result = runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(),
        tools_registry=tools,
        save_session=lambda _: None,
    )

    assert result.final_text == "done"
    assert [message.role for message in session.messages] == [
        "user",
        "assistant",
        "tool",
        "tool",
        "assistant",
    ]
    assert session.messages[2].tool_call_id == "call-1"
    assert session.messages[3].tool_call_id == "call-2"
    second_call_messages = model.calls[1]
    assert [message.role for message in second_call_messages[-3:]] == ["assistant", "tool", "tool"]
    assert [summary.name for summary in result.tool_calls] == ["alpha", "beta"]


def test_loop_turns_tool_failures_into_tool_messages(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    tools = StubToolsRegistry()

    def broken(_: dict[str, object]) -> object:
        raise ValueError("boom")

    tools.handlers["alpha"] = broken
    model = StubModelClient(
        [
            LoopModelResponse(
                content="调工具",
                tool_calls=[ToolCallPayload(id="call-1", name="alpha", arguments={"value": 1})],
            ),
            LoopModelResponse(content="done"),
        ]
    )
    runner = LoopRunner(model_client=model)

    result = runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(),
        tools_registry=tools,
        save_session=lambda _: None,
    )

    assert result.final_text == "done"
    assert session.messages[2].content == "Error: ValueError: boom"
    assert result.tool_calls[0].result_summary == "Error: ValueError: boom"


def test_batched_tool_calls_execute_concurrently(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    tools = StubToolsRegistry()
    active = 0
    max_active = 0
    lock = threading.Lock()

    def slow(arguments: dict[str, object]) -> str:
        nonlocal active, max_active
        _ = arguments
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return "ok"

    tools.handlers["alpha"] = slow
    tools.handlers["beta"] = slow
    model = StubModelClient(
        [
            LoopModelResponse(
                content="调工具",
                tool_calls=[
                    ToolCallPayload(id="call-1", name="alpha", arguments={}),
                    ToolCallPayload(id="call-2", name="beta", arguments={}),
                ],
            ),
            LoopModelResponse(content="done"),
        ]
    )
    runner = LoopRunner(model_client=model)

    runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(),
        tools_registry=tools,
        save_session=lambda _: None,
    )

    assert max_active >= 2


def test_loop_returns_fixed_fallback_after_max_iterations(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    tools = StubToolsRegistry()
    tools.handlers["alpha"] = lambda arguments: "ok"
    model = StubModelClient(
        [
            LoopModelResponse(
                content="继续",
                tool_calls=[ToolCallPayload(id=f"call-{index}", name="alpha", arguments={})],
            )
            for index in range(MAX_ITERATIONS)
        ]
    )
    runner = LoopRunner(model_client=model)

    result = runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(),
        tools_registry=tools,
        save_session=lambda _: None,
    )

    assert result.final_text == MAX_ITERATIONS_FALLBACK_TEXT
    assert session.messages[-1].content == MAX_ITERATIONS_FALLBACK_TEXT


def test_loop_exposes_skill_summary_to_model(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    model = StubModelClient([LoopModelResponse(content="done")])
    runner = LoopRunner(model_client=model)

    runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(summary="<skills><skill>demo</skill></skills>"),
        tools_registry=StubToolsRegistry(),
        save_session=lambda _: None,
    )

    assert "<skills><skill>demo</skill></skills>" in model.calls[0][0].content


def test_loop_emits_trace_events(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    tools = StubToolsRegistry()
    tools.handlers["alpha"] = lambda arguments: f"alpha:{arguments['value']}"
    trace = StubTraceSink()
    model = StubModelClient(
        [
            LoopModelResponse(
                content="先调工具",
                tool_calls=[ToolCallPayload(id="call-1", name="alpha", arguments={"value": 1})],
            ),
            LoopModelResponse(content="done"),
        ]
    )
    runner = LoopRunner(model_client=model, trace_sink=trace)

    runner.run(
        session=session,
        request=RunRequest(session_id=session.session_id, user_input="执行"),
        context_builder=ContextBuilder(tmp_path),
        skills_loader=StubSkillsLoader(summary="<skills><name>demo</name></skills>"),
        tools_registry=tools,
        save_session=lambda _: None,
    )

    events = {(category, event) for category, event, _ in trace.events}
    assert ("run", "start") in events
    assert ("prompt", "summary") in events
    assert ("prompt", "iteration_input") in events
    assert ("model", "iteration_output") in events
    assert ("loop", "iteration") in events
    assert ("tool", "call") in events
    assert ("loop", "end") in events

    prompt_events = [
        data
        for category, event, data in trace.events
        if (category, event) == ("prompt", "iteration_input")
    ]
    model_events = [
        data
        for category, event, data in trace.events
        if (category, event) == ("model", "iteration_output")
    ]
    assert prompt_events[0]["iteration"] == 1
    assert isinstance(prompt_events[0]["system_prompt"], str)
    assert isinstance(prompt_events[0]["messages"], list)
    assert isinstance(prompt_events[0]["tool_definitions"], list)
    assert prompt_events[0]["tool_definitions"][0]["name"] == "alpha"
    assert "input_schema" in prompt_events[0]["tool_definitions"][0]
    assert model_events[0]["content"] == "先调工具"
