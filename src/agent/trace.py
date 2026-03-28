"""Internal trace support for local harness end-to-end debugging."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Literal, Protocol

from agent.time_utils import now_local

TraceMode = Literal["summary", "full"]

SENSITIVE_FIELD_NAMES = {
    "api_key",
    "authorization",
    "cookie",
    "token",
    "access_token",
    "refresh_token",
}
REDACTED_VALUE = "[REDACTED]"


class TraceSink(Protocol):
    """Minimal event sink for runtime/loop/memory trace events."""

    def record(self, *, category: str, event: str, data: dict[str, Any]) -> None:
        """Record one internal trace event."""


class SessionTraceCollector:
    """Collect one run trace block and append it to a session-local trace file."""

    def __init__(
        self,
        *,
        session_id: str,
        topic: str | None,
        workspace_path: Path,
        raw_user_input: str,
        normalized_user_input: str,
        mode: TraceMode,
    ) -> None:
        self.session_id = session_id
        self.topic = topic
        self.workspace_path = workspace_path
        self.raw_user_input = raw_user_input
        self.normalized_user_input = normalized_user_input
        self.mode: TraceMode = mode
        self.started_at = now_local()
        self.events: list[tuple[str, str, dict[str, Any]]] = []
        self._lock = threading.Lock()

    @property
    def trace_file(self) -> Path:
        """Return the session-level trace file path."""

        return self.workspace_path / "logs" / "agent-trace.log"

    def record(self, *, category: str, event: str, data: dict[str, Any]) -> None:
        """Record one trace event in memory for this run."""

        if not _should_record_event(mode=self.mode, category=category, event=event):
            return
        with self._lock:
            self.events.append((category, event, data))

    def write_run_block(
        self,
        *,
        final_text: str,
        artifacts: list[str],
    ) -> Path:
        """Append one readable run block to the session trace file."""

        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        ended_at = now_local()
        lines = [
            "===== RUN START =====",
            f"started_at: {self.started_at.isoformat()}",
            f"ended_at: {ended_at.isoformat()}",
            f"session_id: {self.session_id}",
            f"topic: {self.topic or ''}",
            f"trace_mode: {self.mode}",
            f"workspace_path: {self.workspace_path}",
            "",
            "raw_user_input:",
            self.raw_user_input,
            "",
            "normalized_user_input:",
            self.normalized_user_input,
            "",
        ]
        with self._lock:
            events = list(self.events)
        for category, event, data in events:
            lines.append(f"[{category}] {event}")
            for key, value in _redact_mapping(data).items():
                lines.extend(_format_trace_field(key, value))
            lines.append("")
        lines.extend(
            [
                "final_text:",
                final_text,
                "",
                "artifacts:",
            ]
        )
        if artifacts:
            lines.extend(f"- {artifact}" for artifact in artifacts)
        else:
            lines.append("-")
        lines.extend(["===== RUN END =====", ""])
        with self.trace_file.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        return self.trace_file


def _format_trace_field(key: str, value: Any) -> list[str]:
    rendered = _render_trace_value(value)
    if "\n" not in rendered:
        return [f"- {key}: {rendered}"]

    lines = [f"- {key}:"]
    lines.extend(f"  {line}" if line else "  " for line in rendered.splitlines())
    return lines


def _render_trace_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int | float | bool) or value is None:
        return str(value)
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    return {key: _redact_value(key, value) for key, value in data.items()}


def _redact_value(key: str, value: Any) -> Any:
    if _is_sensitive_field(key):
        return REDACTED_VALUE
    if isinstance(value, dict):
        return {
            nested_key: _redact_value(nested_key, nested_value)
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    return value


def _is_sensitive_field(name: str) -> bool:
    normalized = name.strip().lower().replace("-", "_")
    return normalized in SENSITIVE_FIELD_NAMES or any(
        sensitive in normalized for sensitive in SENSITIVE_FIELD_NAMES
    )


def _should_record_event(*, mode: TraceMode, category: str, event: str) -> bool:
    if mode == "full":
        return True
    return (category, event) not in {
        ("prompt", "iteration_input"),
        ("model", "iteration_output"),
    }
