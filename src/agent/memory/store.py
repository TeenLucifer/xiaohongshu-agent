"""Persistent long-term memory store."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from agent.session.models import SessionMessage

logger = logging.getLogger(__name__)


class MemoryStore:
    """Two-layer session memory backed by MEMORY.md and HISTORY.md."""

    _MAX_FAILURES_BEFORE_RAW_ARCHIVE = 3

    def __init__(self, workspace_path: Path) -> None:
        self.memory_dir = workspace_path / "memory"
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.history_file = self.memory_dir / "HISTORY.md"
        self._consecutive_failures = 0

    def read_long_term(self) -> str:
        """Read long-term memory markdown."""

        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""

    def write_long_term(self, content: str) -> None:
        """Write the current full long-term memory."""

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(content, encoding="utf-8")

    def append_history(self, entry: str) -> None:
        """Append one history archive entry."""

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        with self.history_file.open("a", encoding="utf-8") as handle:
            handle.write(entry.rstrip() + "\n\n")

    def get_memory_context(self) -> str:
        """Build the memory context injected into the system prompt."""

        long_term = self.read_long_term()
        return f"## Long-term Memory\n{long_term}" if long_term else ""

    def mark_failure_or_raw_archive(self, messages: list[SessionMessage]) -> bool:
        """Return True if fallback archived the messages, else False."""

        self._consecutive_failures += 1
        if self._consecutive_failures < self._MAX_FAILURES_BEFORE_RAW_ARCHIVE:
            return False
        self.raw_archive(messages)
        self._consecutive_failures = 0
        return True

    def mark_success(self) -> None:
        """Reset the failure counter after a successful consolidation."""

        self._consecutive_failures = 0

    def raw_archive(self, messages: list[SessionMessage]) -> None:
        """Fallback by dumping raw messages into HISTORY.md."""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.append_history(
            f"[{timestamp}] [RAW] {len(messages)} messages\n{self.format_messages(messages)}"
        )
        logger.warning("Memory consolidation degraded: raw-archived %s messages", len(messages))

    @staticmethod
    def format_messages(messages: list[SessionMessage]) -> str:
        """Format a message chunk for memory consolidation."""

        lines: list[str] = []
        for message in messages:
            if not message.content:
                continue
            tool_names = [tool_call.name for tool_call in message.tool_calls]
            tools_suffix = f" [tools: {', '.join(tool_names)}]" if tool_names else ""
            timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M")
            lines.append(f"[{timestamp}] {message.role.upper()}{tools_suffix}: {message.content}")
        return "\n".join(lines)

    @staticmethod
    def normalize_text(value: object) -> str:
        """Normalize a memory payload value to text."""

        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
