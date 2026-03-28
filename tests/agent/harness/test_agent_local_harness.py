from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.local_harness.cli import (
    build_parser,
    format_output,
    main,
    normalize_user_input,
    parse_metadata,
    run_local,
)
from agent.loop_runner import LoopModelResponse, LoopRunner
from agent.models import RunResult, ToolCallSummary
from agent.runtime import AgentRuntime
from agent.session.models import SessionSnapshot
from agent.trace import SessionTraceCollector


class StubRuntime:
    def __init__(self) -> None:
        self.created: list[tuple[str | None, dict[str, Any] | None]] = []
        self.requests: list[dict[str, Any]] = []

    def create_session(
        self,
        topic: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionSnapshot:
        self.created.append((topic, metadata))
        return SessionSnapshot(
            session_id="sess-new",
            topic=topic,
            workspace_path=Path("/tmp/workspace"),
            created_at=_dt("2026-03-28T00:00:00+00:00"),
            updated_at=_dt("2026-03-28T00:00:00+00:00"),
            metadata=metadata or {},
        )

    def run(self, request: Any) -> RunResult:
        self.requests.append(request.model_dump())
        return RunResult(
            session_id=request.session_id,
            final_text="done",
            tool_calls=[
                ToolCallSummary(
                    name="read_file",
                    arguments_summary="path=a.md",
                    result_summary="ok",
                )
            ],
            artifacts=["data/sessions/demo/out.md"],
        )


def _dt(raw: str):
    from datetime import datetime

    return datetime.fromisoformat(raw)


def test_python_entry_runs_existing_session() -> None:
    runtime = StubRuntime()

    result = run_local(
        runtime,  # type: ignore[arg-type]
        session_id="sess-1",
        topic=None,
        user_input="执行",
        attachments=["a.png"],
        metadata={"source": "smoke"},
    )

    assert result.session_id == "sess-1"
    assert runtime.created == []
    assert runtime.requests[0]["attachments"] == ["a.png"]


def test_python_entry_creates_session_from_topic() -> None:
    runtime = StubRuntime()

    result = run_local(
        runtime,  # type: ignore[arg-type]
        session_id=None,
        topic="话题",
        user_input="执行",
    )

    assert result.session_id == "sess-new"
    assert runtime.created == [("话题", {})]
    assert runtime.requests[0]["session_id"] == "sess-new"


def test_smoke_run_input_is_normalized_to_explicit_session_self_check() -> None:
    normalized = normalize_user_input("帮我执行一次 smoke run")

    assert "当前 session 工作目录" in normalized
    assert "pwd" in normalized
    assert 'list_dir(".")' in normalized
    assert "smoke.txt" in normalized
    assert "package.json" in normalized


def test_non_smoke_input_is_not_normalized() -> None:
    raw = "继续整理这个 session 的结果"

    assert normalize_user_input(raw) == raw


def test_cli_parser_and_metadata_json() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run",
            "--topic",
            "话题",
            "--user-input",
            "执行",
            "--attachment",
            "a.png",
            "--attachment",
            "b.png",
            "--metadata",
            '{"source":"smoke"}',
        ]
    )

    assert args.topic == "话题"
    assert args.attachment == ["a.png", "b.png"]
    assert parse_metadata(args.metadata) == {"source": "smoke"}


def test_cli_parser_accepts_trace_full() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "run",
            "--topic",
            "话题",
            "--user-input",
            "执行",
            "--trace-full",
        ]
    )

    assert args.trace is False
    assert args.trace_full is True


def test_run_local_rejects_invalid_session_and_topic_combination() -> None:
    runtime = StubRuntime()

    try:
        run_local(runtime, session_id="sess-1", topic="话题", user_input="执行")  # type: ignore[arg-type]
    except ValueError as exc:
        assert "不能同时传入" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_format_output_supports_human_json_and_verbose() -> None:
    result = RunResult(
        session_id="sess-1",
        final_text="done",
        tool_calls=[
            ToolCallSummary(
                name="exec",
                arguments_summary="command=python",
                result_summary="ok",
            )
        ],
        artifacts=["/tmp/out.txt"],
    )

    human = format_output(result, as_json=False, verbose=False)
    verbose = format_output(result, as_json=False, verbose=True)
    payload = json.loads(format_output(result, as_json=True, verbose=False))

    assert "session_id: sess-1" in human
    assert "arguments:" in verbose
    assert payload["session_id"] == "sess-1"
    assert payload["tool_calls"] == [{"name": "exec"}]


def test_cli_exit_codes_and_output_modes(capsys) -> None:
    runtime = StubRuntime()

    def factory() -> StubRuntime:
        return runtime

    ok = main(
        [
            "run",
            "--topic",
            "话题",
            "--user-input",
            "执行",
            "--json",
        ],
        runtime_factory=factory,  # type: ignore[arg-type]
    )
    bad_input = main(
        [
            "run",
            "--session-id",
            "sess-1",
            "--topic",
            "话题",
            "--user-input",
            "执行",
        ],
        runtime_factory=factory,  # type: ignore[arg-type]
    )

    class FailingRuntime(StubRuntime):
        def run(self, request: Any) -> RunResult:
            raise RuntimeError("boom")

    bad_runtime = main(
        ["run", "--topic", "话题", "--user-input", "执行"],
        runtime_factory=FailingRuntime,  # type: ignore[arg-type]
    )

    out = capsys.readouterr()
    assert ok == 0
    assert bad_input == 1
    assert bad_runtime == 2
    assert '"session_id": "sess-new"' in out.out
    assert "输入错误:" in out.err
    assert "运行失败:" in out.err


def test_minimal_smoke_run_with_real_runtime(tmp_path: Path) -> None:
    class CapturingLoopRunner:
        def run(self, **kwargs: object) -> RunResult:
            request = kwargs["request"]
            return RunResult(
                session_id=request.session_id,  # type: ignore[attr-defined]
                final_text="smoke ok",
                tool_calls=[],
                artifacts=[],
            )

    runtime = AgentRuntime(project_root=tmp_path, loop_runner=CapturingLoopRunner())  # type: ignore[arg-type]

    result = run_local(
        runtime,
        session_id=None,
        topic="smoke",
        user_input="smoke run",
    )

    assert result.final_text == "smoke ok"


def test_trace_creates_session_log_file_and_reports_path(tmp_path: Path, capsys) -> None:
    class StubModelClient:
        def complete(self, **kwargs: object) -> LoopModelResponse:
            _ = kwargs
            return LoopModelResponse(content="done")

    def factory() -> AgentRuntime:
        return AgentRuntime(
            project_root=tmp_path,
            data_root=tmp_path / "data",
            loop_runner=LoopRunner(model_client=StubModelClient()),
        )

    exit_code = main(
        [
            "run",
            "--topic",
            "trace",
            "--user-input",
            "smoke run",
            "--trace",
        ],
        runtime_factory=factory,
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "trace_file:" in out
    trace_path = Path(out.split("trace_file:", 1)[1].strip())
    assert trace_path.exists()
    content = trace_path.read_text(encoding="utf-8")
    assert "===== RUN START =====" in content
    started_line = next(line for line in content.splitlines() if line.startswith("started_at: "))
    ended_line = next(line for line in content.splitlines() if line.startswith("ended_at: "))
    started_at = _dt(started_line.split(": ", 1)[1])
    ended_at = _dt(ended_line.split(": ", 1)[1])
    started_offset = started_at.utcoffset()
    ended_offset = ended_at.utcoffset()
    assert started_offset is not None
    assert started_offset.total_seconds() == 8 * 3600
    assert ended_offset is not None
    assert ended_offset.total_seconds() == 8 * 3600
    assert "trace_mode: summary" in content
    assert "raw_user_input:" in content
    assert "normalized_user_input:" in content
    assert "workspace_path:" in content
    assert "[prompt] summary" in content
    assert "[prompt] iteration_input" not in content
    assert "[model] iteration_output" not in content
    assert "- system_prompt:" not in content
    assert "- messages:" not in content
    assert "- tool_definitions:" not in content
    assert "[loop] end" in content


def test_trace_full_writes_complete_prompt_and_model_payloads(tmp_path: Path, capsys) -> None:
    class StubModelClient:
        def complete(self, **kwargs: object) -> LoopModelResponse:
            _ = kwargs
            return LoopModelResponse(content="done")

    def factory() -> AgentRuntime:
        return AgentRuntime(
            project_root=tmp_path,
            data_root=tmp_path / "data",
            loop_runner=LoopRunner(model_client=StubModelClient()),
        )

    exit_code = main(
        [
            "run",
            "--topic",
            "trace",
            "--user-input",
            "smoke run",
            "--trace-full",
        ],
        runtime_factory=factory,
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    trace_path = Path(out.split("trace_file:", 1)[1].strip())
    content = trace_path.read_text(encoding="utf-8")

    assert "trace_mode: full" in content
    assert "[prompt] iteration_input" in content
    assert "[model] iteration_output" in content
    assert "- system_prompt:" in content
    assert "- messages:" in content
    assert "- tool_definitions:" in content
    assert '"input_schema"' in content
    assert "- content: done" in content


def test_trace_redacts_sensitive_fields_by_name(tmp_path: Path) -> None:
    collector = SessionTraceCollector(
        session_id="sess-1",
        topic="trace",
        workspace_path=tmp_path / "workspace",
        raw_user_input="执行",
        normalized_user_input="执行",
        mode="full",
    )
    collector.record(
        category="prompt",
        event="iteration_input",
        data={
            "tool_definitions": [
                {
                    "name": "exec",
                    "input_schema": {
                        "properties": {
                            "api_key": {"type": "string"},
                            "normal_field": {"type": "string"},
                        }
                    },
                }
            ],
            "authorization": "Bearer secret",
            "normal_field": "visible",
        },
    )

    trace_path = collector.write_run_block(final_text="done", artifacts=[])
    content = trace_path.read_text(encoding="utf-8")

    assert "[REDACTED]" in content
    assert "Bearer secret" not in content
    assert "- normal_field: visible" in content
