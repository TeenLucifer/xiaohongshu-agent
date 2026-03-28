"""Restricted shell exec tool."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Final

from pydantic import Field

from agent.tools.base import Tool, ToolArguments, ToolExecutionContext

DEFAULT_TIMEOUT: Final[int] = 60
MAX_TIMEOUT: Final[int] = 600
MAX_OUTPUT_CHARS: Final[int] = 4000
TRUNCATED_MARKER: Final[str] = "\n...[truncated]...\n"
ALLOWED_PREFIXES: Final[tuple[str, ...]] = (
    "pwd",
    "python",
    "python3",
    "node",
    "ffmpeg",
    "jq",
    "unzip",
    "playwright",
    "python -m playwright",
    "python3 -m playwright",
    "uv run python",
    "uv run python3",
    "uv run node",
    "npx playwright",
)
DENY_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"\brm\s+-r\b"),
    re.compile(r"\bdel\s+/[fq]\b", re.IGNORECASE),
    re.compile(r"\brmdir\s+/s\b", re.IGNORECASE),
    re.compile(r"\bformat\b", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdiskpart\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if="),
    re.compile(r"/dev/sd[a-z]"),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\breboot\b", re.IGNORECASE),
    re.compile(r"\bpoweroff\b", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\};:"),
)
PRIVATE_URL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(https?://(?:127\.0\.0\.1|localhost|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|\[::1\]))",
    re.IGNORECASE,
)


class ExecArguments(ToolArguments):
    """Arguments for one exec command."""

    command: str = Field(min_length=1)
    working_dir: str | None = None
    timeout: int = DEFAULT_TIMEOUT


class ExecTool(Tool):
    name = "exec"
    description = "Execute one allowlisted shell command inside the allowed workspace."
    arguments_model = ExecArguments

    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        args = ExecArguments.model_validate(arguments)
        if args.timeout > MAX_TIMEOUT:
            raise ValueError(f"timeout must be <= {MAX_TIMEOUT}")
        if not _is_allowed_command(args.command):
            raise ValueError("Command blocked by safety guard (not in allowlist)")
        if _matches_deny_pattern(args.command):
            raise ValueError("Command blocked by safety guard (dangerous command)")
        if PRIVATE_URL_PATTERN.search(args.command):
            raise ValueError("Command blocked by safety guard (private/internal URL)")

        working_dir = _resolve_working_dir(
            raw_working_dir=args.working_dir,
            context=context,
        )
        if context.restrict_to_workspace:
            _validate_command_paths(args.command, context=context)

        command = _rewrite_python_prefix(args.command)
        env = None
        if command.strip().startswith("uv run "):
            env = os.environ.copy()
            env["UV_CACHE_DIR"] = "/tmp/uv-cache"

        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=args.timeout,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return f"Error: TimeoutExpired: command timed out after {args.timeout}s"

        return _format_command_output(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def _is_allowed_command(command: str) -> bool:
    stripped = command.strip()
    for prefix in ALLOWED_PREFIXES:
        if stripped == prefix or stripped.startswith(prefix + " "):
            return True
    return False


def _matches_deny_pattern(command: str) -> bool:
    return any(pattern.search(command) for pattern in DENY_PATTERNS)


def _rewrite_python_prefix(command: str) -> str:
    stripped = command.strip()
    replacements = (
        ("python -m ", f"{shlex.quote(sys.executable)} -m "),
        ("python3 -m ", f"{shlex.quote(sys.executable)} -m "),
        ("python ", f"{shlex.quote(sys.executable)} "),
        ("python3 ", f"{shlex.quote(sys.executable)} "),
        ("python", shlex.quote(sys.executable)),
        ("python3", shlex.quote(sys.executable)),
        ("uv run python -m ", f"uv run {shlex.quote(sys.executable)} -m "),
        ("uv run python3 -m ", f"uv run {shlex.quote(sys.executable)} -m "),
        ("uv run python ", f"uv run {shlex.quote(sys.executable)} "),
        ("uv run python3 ", f"uv run {shlex.quote(sys.executable)} "),
        ("uv run python", f"uv run {shlex.quote(sys.executable)}"),
        ("uv run python3", f"uv run {shlex.quote(sys.executable)}"),
    )
    for prefix, replacement in replacements:
        if stripped == prefix or stripped.startswith(prefix + " "):
            return stripped.replace(prefix, replacement, 1)
    return command


def _resolve_working_dir(
    *,
    raw_working_dir: str | None,
    context: ToolExecutionContext,
) -> Path | None:
    if raw_working_dir is None:
        return context.allowed_dir
    if context.allowed_dir is None:
        raise ValueError("No allowed workspace configured")

    candidate = Path(raw_working_dir).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (context.allowed_dir / candidate).resolve()
    allowed_roots = [context.allowed_dir, *context.extra_allowed_dirs]
    if not any(_is_under(resolved, root) for root in allowed_roots):
        raise ValueError(f"Working directory escapes allowed roots: {raw_working_dir}")
    return resolved


def _validate_command_paths(command: str, *, context: ToolExecutionContext) -> None:
    tokens = shlex.split(command)
    for token in tokens:
        if "../" in token or token == "..":
            raise ValueError("Command blocked by safety guard (path traversal)")
        if not token.startswith("/"):
            continue
        path = Path(token).resolve()
        allowed_roots = [context.allowed_dir, *context.extra_allowed_dirs]
        if context.allowed_dir is None or not any(_is_under(path, root) for root in allowed_roots):
            raise ValueError("Command blocked by safety guard (absolute path escape)")


def _format_command_output(*, exit_code: int, stdout: str, stderr: str) -> str:
    rendered = "\n".join(
        [
            f"Exit code: {exit_code}",
            "STDOUT:",
            stdout.rstrip(),
            "STDERR:",
            stderr.rstrip(),
        ]
    ).strip()
    if len(rendered) <= MAX_OUTPUT_CHARS:
        return rendered
    head = rendered[: MAX_OUTPUT_CHARS // 2]
    tail = rendered[-MAX_OUTPUT_CHARS // 2 :]
    return head + TRUNCATED_MARKER + tail


def _is_under(path: Path, root: Path | None) -> bool:
    if root is None:
        return False
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False
