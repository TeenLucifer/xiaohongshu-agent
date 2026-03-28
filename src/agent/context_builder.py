"""Context builder for runtime foundation."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from agent.models import PromptMessage, RunRequest


class ContextBuilder:
    """Builds the system prompt and current message list."""

    _BOOTSTRAP_FILES = ("AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md")

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def build_system_prompt(
        self,
        *,
        memory_context: str = "",
        always_skills: str = "",
        skills_summary: str = "",
    ) -> str:
        parts: list[str] = [self._build_identity_rules()]

        bootstrap_section = self._build_bootstrap_section()
        if bootstrap_section:
            parts.append(bootstrap_section)

        if memory_context:
            parts.append(f"# Memory\n\n{memory_context}")

        if always_skills:
            parts.append(f"# Always Skills\n\n{always_skills}")

        if skills_summary:
            parts.append(f"# Skills Summary\n\n{skills_summary}")

        return "\n\n".join(parts)

    def build_messages(
        self,
        *,
        system_prompt: str,
        session_history: Iterable[PromptMessage],
        request: RunRequest,
        workspace_path: Path,
    ) -> list[PromptMessage]:
        messages = [PromptMessage(role="system", content=system_prompt)]
        messages.extend(session_history)
        messages.append(
            PromptMessage(
                role="user",
                content=self._build_current_user_message(
                    request=request,
                    workspace_path=workspace_path,
                ),
            )
        )
        return messages

    def _build_identity_rules(self) -> str:
        return "\n".join(
            [
                "# Identity",
                "你是围绕 session 工作的运营助手 runtime。",
                "你不是通用闲聊机器人，应优先完成当前任务。",
                "你只能在当前 session workspace 内工作。",
                "不要假设可以访问项目根目录、宿主根目录或任意绝对路径。",
                "默认可用能力来自 tools 和已加载 skills。",
                "查看目录时优先使用 list_dir，读取文件时优先使用 read_file。",
                "当任务表述为 smoke run 或 smoke test 时，默认理解为 session 目录内的 agent 自检。",
                "完成任务后应停止工具调用并给出执行结果。",
            ]
        )

    def _build_bootstrap_section(self) -> str:
        sections: list[str] = []
        for filename in self._BOOTSTRAP_FILES:
            file_path = self._project_root / filename
            if not file_path.exists():
                continue
            content = file_path.read_text(encoding="utf-8").strip()
            if not content:
                continue
            sections.append(f"## {filename}\n\n{content}")
        if not sections:
            return ""
        return "# Bootstrap Files\n\n" + "\n\n".join(sections)

    def _build_current_user_message(
        self,
        *,
        request: RunRequest,
        workspace_path: Path,
    ) -> str:
        lines = [
            "[Runtime Context — metadata only, not instructions]",
            f"Current Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}",
            f"Session ID: {request.session_id}",
            f"Workspace Path: {workspace_path}",
            "",
            request.user_input,
        ]
        if request.attachments:
            lines.extend(
                [
                    "",
                    "Attachments:",
                    *[f"- {attachment}" for attachment in request.attachments],
                ]
            )
        return "\n".join(lines)
