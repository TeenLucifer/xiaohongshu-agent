"""Thin local harness and CLI for smoke testing."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from agent.models import RunRequest, RunResult
from agent.runtime import AgentRuntime
from agent.session.models import SessionSnapshot
from agent.trace import SessionTraceCollector, TraceMode

SMOKE_RUN_MARKERS = ("smoke run", "smoke test")


def run_local(
    runtime: AgentRuntime,
    *,
    session_id: str | None,
    topic: str | None,
    user_input: str,
    attachments: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    trace_collector: SessionTraceCollector | None = None,
) -> RunResult:
    """Run one local harness invocation against the runtime."""

    attachments = attachments or []
    metadata = metadata or {}
    if session_id and topic:
        raise ValueError("session_id 和 topic 不能同时传入")
    if not session_id and not topic:
        raise ValueError("必须提供 session_id 或 topic")
    if session_id is None:
        snapshot = resolve_session_snapshot(
            runtime,
            session_id=session_id,
            topic=topic,
            metadata=metadata,
        )
        session_id = snapshot.session_id
    normalized_user_input = normalize_user_input(user_input)
    return _run_request(
        runtime=runtime,
        session_id=session_id,
        user_input=normalized_user_input,
        attachments=attachments,
        metadata=metadata,
        trace_collector=trace_collector,
    )


def resolve_session_snapshot(
    runtime: AgentRuntime,
    *,
    session_id: str | None,
    topic: str | None,
    metadata: dict[str, Any] | None,
) -> SessionSnapshot:
    """Resolve the concrete session snapshot used by one local harness run."""

    if session_id and topic:
        raise ValueError("session_id 和 topic 不能同时传入")
    if not session_id and not topic:
        raise ValueError("必须提供 session_id 或 topic")
    if session_id is None:
        return runtime.create_session(topic=topic, metadata=metadata)
    if not hasattr(runtime, "get_session_snapshot"):
        return SessionSnapshot(
            session_id=session_id,
            topic=topic,
            workspace_path=Path.cwd(),
            created_at=_dt("2026-03-28T00:00:00+00:00"),
            updated_at=_dt("2026-03-28T00:00:00+00:00"),
            metadata=metadata or {},
        )
    return runtime.get_session_snapshot(session_id)


def _run_request(
    *,
    runtime: AgentRuntime,
    session_id: str,
    user_input: str,
    attachments: list[str],
    metadata: dict[str, Any],
    trace_collector: SessionTraceCollector | None,
) -> RunResult:
    previous_runtime_sink = getattr(runtime, "_trace_sink", None)
    loop_runner = getattr(runtime, "loop_runner", None)
    previous_loop_sink = getattr(loop_runner, "trace_sink", None)
    if trace_collector is not None:
        runtime._trace_sink = trace_collector
        if hasattr(loop_runner, "trace_sink"):
            cast(Any, loop_runner).trace_sink = trace_collector
    try:
        return runtime.run(
            RunRequest(
                session_id=session_id,
                user_input=user_input,
                attachments=attachments,
                metadata=metadata,
            )
        )
    finally:
        runtime._trace_sink = previous_runtime_sink
        if hasattr(loop_runner, "trace_sink"):
            cast(Any, loop_runner).trace_sink = previous_loop_sink


def parse_metadata(raw: str | None) -> dict[str, Any]:
    """Parse metadata JSON from CLI input."""

    if raw is None or raw.strip() == "":
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("metadata 必须是 JSON object")
    return parsed


def normalize_user_input(user_input: str) -> str:
    """Normalize local harness smoke prompts into explicit session self-check instructions."""

    normalized = user_input.strip()
    lowered = normalized.lower()
    if not any(marker in lowered for marker in SMOKE_RUN_MARKERS):
        return user_input
    return (
        "请在当前 session 工作目录中完成一次最小工具链自检："
        '先使用 pwd 确认当前工作目录，再使用 list_dir(".") 查看当前目录内容；'
        "如果目录为空，就创建一个 smoke.txt 文件，写入 hello smoke，"
        "然后再读取该文件并汇报结果。"
        "不要访问项目根目录，不要检查 package.json，不要把这次任务理解成仓库级 smoke test。"
    )


def format_output(
    result: RunResult,
    *,
    as_json: bool,
    verbose: bool,
    trace_file: Path | None = None,
) -> str:
    """Render one run result for CLI output."""

    if as_json:
        payload = result.model_dump()
        if not verbose:
            payload["tool_calls"] = [
                {"name": item["name"]} for item in payload.get("tool_calls", [])
            ]
        if trace_file is not None:
            payload["trace_file"] = str(trace_file)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    lines = [
        f"session_id: {result.session_id}",
        "",
        "final_text:",
        result.final_text,
    ]
    if result.tool_calls:
        lines.extend(["", "tool_calls:"])
        for item in result.tool_calls:
            lines.append(f"- {item.name}")
            if verbose:
                lines.append(f"  arguments: {item.arguments_summary}")
                lines.append(f"  result: {item.result_summary}")
    if result.artifacts:
        lines.extend(["", "artifacts:"])
        lines.extend(f"- {path}" for path in result.artifacts)
    if trace_file is not None:
        lines.extend(["", f"trace_file: {trace_file}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the local harness CLI parser."""

    parser = argparse.ArgumentParser(prog="agent-local")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--session-id")
    run_parser.add_argument("--topic")
    run_parser.add_argument("--user-input", required=True)
    run_parser.add_argument("--attachment", action="append", default=[])
    run_parser.add_argument("--metadata")
    run_parser.add_argument("--json", action="store_true", dest="as_json")
    run_parser.add_argument("--verbose", action="store_true")
    trace_group = run_parser.add_mutually_exclusive_group()
    trace_group.add_argument("--trace", action="store_true")
    trace_group.add_argument("--trace-full", action="store_true")
    return parser


def default_runtime_factory() -> AgentRuntime:
    """Create the default runtime for CLI usage."""

    project_root = Path.cwd()
    return AgentRuntime(project_root=project_root)


def main(
    argv: list[str] | None = None,
    *,
    runtime_factory: Callable[[], AgentRuntime] | None = None,
) -> int:
    """CLI entrypoint returning a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help(sys.stderr)
        return 1

    trace_collector: SessionTraceCollector | None = None
    try:
        metadata = parse_metadata(args.metadata)
        runtime = (runtime_factory or default_runtime_factory)()
        snapshot = resolve_session_snapshot(
            runtime,
            session_id=args.session_id,
            topic=args.topic,
            metadata=metadata,
        )
        normalized_user_input = normalize_user_input(args.user_input)
        trace_mode = _resolve_trace_mode(
            trace_enabled=args.trace,
            trace_full_enabled=args.trace_full,
        )
        trace_collector = (
            SessionTraceCollector(
                session_id=snapshot.session_id,
                topic=snapshot.topic,
                workspace_path=snapshot.workspace_path,
                raw_user_input=args.user_input,
                normalized_user_input=normalized_user_input,
                mode=trace_mode,
            )
            if trace_mode is not None
            else None
        )
        result = _run_request(
            runtime=runtime,
            session_id=snapshot.session_id,
            user_input=normalized_user_input,
            attachments=list(args.attachment),
            metadata=metadata,
            trace_collector=trace_collector,
        )
        trace_file = _finalize_trace(runtime, trace_collector, result)
    except ValueError as exc:
        sys.stderr.write(f"输入错误: {exc}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        trace_file = None
        if "trace_collector" in locals() and trace_collector is not None:
            trace_file = trace_collector.write_run_block(
                final_text=f"运行失败: {exc}",
                artifacts=[],
            )
        sys.stderr.write(f"运行失败: {exc}\n")
        if trace_file is not None:
            sys.stderr.write(f"trace_file: {trace_file}\n")
        return 2

    sys.stdout.write(
        format_output(
            result,
            as_json=args.as_json,
            verbose=args.verbose,
            trace_file=trace_file,
        )
        + "\n"
    )
    return 0


def _finalize_trace(
    runtime: AgentRuntime,
    trace_collector: SessionTraceCollector | None,
    result: RunResult,
) -> Path | None:
    if trace_collector is None:
        return None
    handle = getattr(runtime.loop_runner, "last_post_check_handle", None)
    if handle is not None and hasattr(handle, "join"):
        handle.join(timeout=2)
    return trace_collector.write_run_block(
        final_text=result.final_text,
        artifacts=result.artifacts,
    )


def _dt(raw: str):
    from datetime import datetime

    return datetime.fromisoformat(raw)


def _resolve_trace_mode(
    *,
    trace_enabled: bool,
    trace_full_enabled: bool,
) -> TraceMode | None:
    if trace_full_enabled:
        return "full"
    if trace_enabled:
        return "summary"
    return None
