"""Thin local harness and CLI for smoke testing."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent.models import RunRequest, RunResult
from agent.runtime import AgentRuntime

SMOKE_RUN_MARKERS = ("smoke run", "smoke test")


def run_local(
    runtime: AgentRuntime,
    *,
    session_id: str | None,
    topic: str | None,
    user_input: str,
    attachments: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RunResult:
    """Run one local harness invocation against the runtime."""

    if session_id and topic:
        raise ValueError("session_id 和 topic 不能同时传入")
    if not session_id and not topic:
        raise ValueError("必须提供 session_id 或 topic")

    attachments = attachments or []
    metadata = metadata or {}
    if session_id is None:
        snapshot = runtime.create_session(topic=topic, metadata=metadata)
        session_id = snapshot.session_id
    normalized_user_input = normalize_user_input(user_input)

    return runtime.run(
        RunRequest(
            session_id=session_id,
            user_input=normalized_user_input,
            attachments=attachments,
            metadata=metadata,
        )
    )


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


def format_output(result: RunResult, *, as_json: bool, verbose: bool) -> str:
    """Render one run result for CLI output."""

    if as_json:
        payload = result.model_dump()
        if not verbose:
            payload["tool_calls"] = [
                {"name": item["name"]} for item in payload.get("tool_calls", [])
            ]
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

    try:
        metadata = parse_metadata(args.metadata)
        runtime = (runtime_factory or default_runtime_factory)()
        result = run_local(
            runtime,
            session_id=args.session_id,
            topic=args.topic,
            user_input=args.user_input,
            attachments=list(args.attachment),
            metadata=metadata,
        )
    except ValueError as exc:
        sys.stderr.write(f"输入错误: {exc}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"运行失败: {exc}\n")
        return 2

    sys.stdout.write(format_output(result, as_json=args.as_json, verbose=args.verbose) + "\n")
    return 0
