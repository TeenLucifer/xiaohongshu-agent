from __future__ import annotations

from pathlib import Path
from typing import cast

from agent.context_builder import ContextBuilder
from agent.memory.consolidator import (
    DefaultMemoryConsolidationAgent,
    MemoryConsolidationResult,
    MemoryConsolidator,
    RuntimeMemoryConsolidator,
)
from agent.memory.store import MemoryStore
from agent.models import PromptMessage, RunRequest, RunResult, ToolCallPayload
from agent.runtime import AgentRuntime
from agent.session.models import Session, SessionMessage
from agent.skills.loader import SkillsLoader


class StubTraceSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, object]]] = []

    def record(self, *, category: str, event: str, data: dict[str, object]) -> None:
        self.events.append((category, event, data))


class StubMemoryAgent:
    def __init__(self, *, result: MemoryConsolidationResult | dict[str, object] | None) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    def consolidate(
        self,
        *,
        current_memory: str,
        messages_text: str,
    ) -> MemoryConsolidationResult | dict[str, object] | None:
        self.calls.append((current_memory, messages_text))
        return self.result


class StubToolCallingModelClient:
    def __init__(self, tool_calls: list[ToolCallPayload] | None = None) -> None:
        self.tool_calls = tool_calls or []
        self.calls: list[tuple[list[str], object | None]] = []

    def complete(
        self,
        *,
        messages: list[object],
        tool_definitions: list[object],
        tool_choice: object | None = None,
    ) -> object:
        _ = tool_definitions
        self.calls.append(
            ([cast(PromptMessage, message).role for message in messages], tool_choice)
        )
        return type(
            "Response",
            (),
            {
                "content": "",
                "tool_calls": self.tool_calls,
            },
        )()


def make_session(tmp_path: Path, session_id: str = "sess-1") -> Session:
    return Session(session_id=session_id, workspace_path=tmp_path / "sessions" / session_id)


def test_memory_store_uses_session_memory_directory(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "sessions" / "sess-1")

    store.write_long_term("# facts")
    store.append_history("[2026-03-28 12:00] summary")

    assert store.memory_file == tmp_path / "sessions" / "sess-1" / "memory" / "MEMORY.md"
    assert store.history_file == tmp_path / "sessions" / "sess-1" / "memory" / "HISTORY.md"
    assert store.read_long_term() == "# facts"
    assert "summary" in store.history_file.read_text(encoding="utf-8")
    assert store.get_memory_context() == "## Long-term Memory\n# facts"


def test_default_memory_consolidation_agent_uses_save_memory_tool() -> None:
    model_client = StubToolCallingModelClient(
        tool_calls=[
            ToolCallPayload(
                id="call-1",
                name="save_memory",
                arguments={
                    "history_entry": "[2026-03-28 12:00] summary",
                    "memory_update": "# facts",
                },
            )
        ]
    )
    agent = DefaultMemoryConsolidationAgent(model_client=model_client)  # type: ignore[arg-type]

    result = agent.consolidate(
        current_memory="# current",
        messages_text="[2026-03-28 12:01] USER: hi",
    )

    assert isinstance(result, MemoryConsolidationResult)
    assert result.history_entry == "[2026-03-28 12:00] summary"
    assert result.memory_update == "# facts"
    assert model_client.calls[0][1] == {"type": "function", "function": {"name": "save_memory"}}


def test_memory_consolidator_exposes_budget_and_target_formulas(tmp_path: Path) -> None:
    consolidator = MemoryConsolidator(
        store=MemoryStore(tmp_path / "sessions" / "sess-1"),
        agent=StubMemoryAgent(
            result=MemoryConsolidationResult(
                history_entry="[2026-03-28 12:00] summary",
                memory_update="# facts",
            )
        ),
        context_window_tokens=16_000,
        max_completion_tokens=2_000,
    )

    assert consolidator.budget == 12_976
    assert consolidator.target == 6_488


def test_pick_consolidation_boundary_chooses_user_turn_boundary(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    session.add_message(SessionMessage(role="user", content="a" * 2000))
    session.add_message(SessionMessage(role="assistant", content="b" * 2000))
    session.add_message(SessionMessage(role="user", content="c" * 2000))
    session.add_message(SessionMessage(role="assistant", content="d" * 2000))
    consolidator = MemoryConsolidator(
        store=MemoryStore(session.workspace_path),
        agent=StubMemoryAgent(
            result=MemoryConsolidationResult(
                history_entry="[2026-03-28 12:00] summary",
                memory_update="# facts",
            )
        ),
        context_window_tokens=10_000,
        max_completion_tokens=1_000,
    )

    boundary = consolidator.pick_consolidation_boundary(session, tokens_to_remove=100)

    assert boundary is not None
    assert boundary[0] == 2


def test_consolidation_success_updates_memory_history_and_cursor(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    session.add_message(SessionMessage(role="user", content="a" * 4000))
    session.add_message(SessionMessage(role="assistant", content="b" * 4000))
    session.add_message(SessionMessage(role="user", content="c" * 4000))
    session.add_message(SessionMessage(role="assistant", content="d" * 4000))
    agent = StubMemoryAgent(
        result=MemoryConsolidationResult(
            history_entry="[2026-03-28 12:00] summarized chunk",
            memory_update="# long term facts",
        )
    )
    store = MemoryStore(session.workspace_path)
    consolidator = MemoryConsolidator(
        store=store,
        agent=agent,
        context_window_tokens=6_000,
        max_completion_tokens=1_000,
    )

    changed = consolidator.maybe_consolidate_by_tokens(session)

    assert changed is True
    assert session.last_consolidated == 2
    assert store.read_long_term() == "# long term facts"
    history_text = store.history_file.read_text(encoding="utf-8")
    assert "summarized chunk" in history_text
    assert agent.calls


def test_consolidation_invalid_payload_does_not_advance_cursor(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    session.add_message(SessionMessage(role="user", content="a" * 4000))
    session.add_message(SessionMessage(role="assistant", content="b" * 4000))
    session.add_message(SessionMessage(role="user", content="c" * 4000))
    agent = StubMemoryAgent(result={"memory_update": "# facts"})
    store = MemoryStore(session.workspace_path)
    consolidator = MemoryConsolidator(
        store=store,
        agent=agent,
        context_window_tokens=4_500,
        max_completion_tokens=500,
    )

    changed = consolidator.maybe_consolidate_by_tokens(session)

    assert changed is False
    assert session.last_consolidated == 0
    assert not store.history_file.exists()


def test_raw_archive_fallback_after_three_failures(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "sessions" / "sess-1")
    messages = [SessionMessage(role="user", content="hello")]

    assert store.mark_failure_or_raw_archive(messages) is False
    assert store.mark_failure_or_raw_archive(messages) is False
    assert store.mark_failure_or_raw_archive(messages) is True
    history_text = store.history_file.read_text(encoding="utf-8")
    assert "[RAW] 1 messages" in history_text


def test_post_check_runs_in_background(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    session.add_message(SessionMessage(role="user", content="a" * 4000))
    session.add_message(SessionMessage(role="assistant", content="b" * 4000))
    session.add_message(SessionMessage(role="user", content="c" * 4000))
    agent = StubMemoryAgent(
        result=MemoryConsolidationResult(
            history_entry="[2026-03-28 12:00] summary",
            memory_update="# facts",
        )
    )
    consolidator = MemoryConsolidator(
        store=MemoryStore(session.workspace_path),
        agent=agent,
        context_window_tokens=4_500,
        max_completion_tokens=500,
    )
    results: list[bool] = []

    thread = consolidator.schedule_post_check(session, on_complete=results.append)
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert results == [True]


def test_runtime_injects_memory_context_into_system_prompt(tmp_path: Path) -> None:
    memory_path = tmp_path / "data" / "sessions" / "sess-1" / "memory"
    memory_path.mkdir(parents=True, exist_ok=True)
    (memory_path / "MEMORY.md").write_text("# persisted memory", encoding="utf-8")
    runtime = AgentRuntime(project_root=tmp_path, data_root=tmp_path / "data")
    session = runtime.session_manager.get_or_create("sess-1", topic="话题")

    captured: dict[str, str] = {}

    class CapturingLoopRunner:
        def run(self, **kwargs: object) -> RunResult:
            session_obj = cast(Session, kwargs["session"])
            request = cast(RunRequest, kwargs["request"])
            context_builder = cast(ContextBuilder, kwargs["context_builder"])
            skills_loader = cast(SkillsLoader, kwargs["skills_loader"])
            messages = context_builder.build_messages(
                system_prompt=context_builder.build_system_prompt(
                    workspace_path=session_obj.workspace_path,
                    memory_context=MemoryStore(session_obj.workspace_path).get_memory_context(),
                    always_skills=skills_loader.load_always_skills_for_context(
                        workspace_path=session_obj.workspace_path
                    ),
                    skills_summary=skills_loader.build_skills_summary(
                        workspace_path=session_obj.workspace_path
                    ),
                ),
                session_history=session_obj.get_history(),
                request=request,
                workspace_path=session_obj.workspace_path,
            )
            captured["system"] = messages[0].content
            return RunResult(session_id="sess-1", final_text="", tool_calls=[], artifacts=[])

    runtime.loop_runner = CapturingLoopRunner()  # type: ignore[assignment]
    runtime.run(RunRequest(session_id=session.session_id, user_input="test"))

    assert "# Memory" in captured["system"]
    assert "## Memory Usage Rules" in captured["system"]
    assert "MEMORY.md 记录长期事实" in captured["system"]
    assert "## Long-term Memory\n# persisted memory" in captured["system"]


def test_runtime_default_memory_consolidator_archives_and_advances_cursor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class HybridModelClient:
        def complete(
            self,
            *,
            messages: list[object],
            tool_definitions: list[object],
            tool_choice: object | None = None,
        ) -> object:
            tool_names = [getattr(item, "name", None) for item in tool_definitions]
            if "save_memory" in tool_names:
                return type(
                    "Response",
                    (),
                    {
                        "content": "",
                        "tool_calls": [
                            ToolCallPayload(
                                id="save-1",
                                name="save_memory",
                                arguments={
                                    "history_entry": "[2026-03-28 12:00] summarized chunk",
                                    "memory_update": "# facts",
                                },
                            )
                        ],
                    },
                )()
            return type("Response", (), {"content": "done", "tool_calls": []})()

    monkeypatch.setattr(
        "agent.runtime.create_default_model_client",
        lambda config=None: HybridModelClient(),
    )
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_MODEL", "model")
    monkeypatch.setattr(AgentRuntime, "_DEFAULT_CONTEXT_WINDOW_TOKENS", 4_500)
    monkeypatch.setattr(AgentRuntime, "_DEFAULT_MAX_COMPLETION_TOKENS", 500)

    runtime = AgentRuntime(project_root=tmp_path, data_root=tmp_path / "data")
    session = runtime.session_manager.create(topic="话题")
    session.add_message(SessionMessage(role="user", content="a" * 4000))
    session.add_message(SessionMessage(role="assistant", content="b" * 4000))
    session.add_message(SessionMessage(role="user", content="c" * 4000))

    result = runtime.run(RunRequest(session_id=session.session_id, user_input="继续"))

    assert result.final_text == "done"
    assert isinstance(runtime.loop_runner.memory_consolidator, RuntimeMemoryConsolidator)
    assert session.last_consolidated == 2
    store = MemoryStore(session.workspace_path)
    assert store.read_long_term() == "# facts"
    assert "summarized chunk" in store.history_file.read_text(encoding="utf-8")


def test_memory_consolidator_emits_trace_events(tmp_path: Path) -> None:
    session = make_session(tmp_path)
    session.add_message(SessionMessage(role="user", content="a" * 4000))
    session.add_message(SessionMessage(role="assistant", content="b" * 4000))
    session.add_message(SessionMessage(role="user", content="c" * 4000))
    trace = StubTraceSink()
    consolidator = MemoryConsolidator(
        store=MemoryStore(session.workspace_path),
        agent=StubMemoryAgent(
            result=MemoryConsolidationResult(
                history_entry="[2026-03-28 12:00] summary",
                memory_update="# facts",
            )
        ),
        context_window_tokens=4_500,
        max_completion_tokens=500,
        trace_sink=trace,
    )

    changed = consolidator.run_pre_check(session)

    assert changed is True
    events = {(category, event) for category, event, _ in trace.events}
    assert ("memory", "pre_check") in events
    assert ("memory", "check") in events
    assert ("memory", "consolidation_success") in events
