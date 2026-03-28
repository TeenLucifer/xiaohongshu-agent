"""Context builder for runtime foundation."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from agent.models import PromptMessage, RunRequest
from agent.prompts import RuntimePromptLoader


class ContextBuilder:
    """Builds the system prompt and current message list."""

    _BOOTSTRAP_FILES = ("AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md")

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._prompt_config = RuntimePromptLoader().load()

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

        parts.append(self._build_memory_section(memory_context))

        if always_skills:
            parts.append(f"# {self._prompt_config.sections.always_skills}\n\n{always_skills}")

        if skills_summary:
            parts.append(f"# {self._prompt_config.sections.skills_summary}\n\n{skills_summary}")

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
            [f"# {self._prompt_config.identity.title}", *self._prompt_config.identity.rules]
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
        return f"# {self._prompt_config.sections.bootstrap_files}\n\n" + "\n\n".join(sections)

    def _build_memory_section(self, memory_context: str) -> str:
        rules = "\n".join(f"- {rule}" for rule in self._prompt_config.memory.rules)
        parts = [f"## {self._prompt_config.memory.rules_title}\n\n{rules}"]
        if memory_context:
            parts.append(memory_context)
        return f"# {self._prompt_config.sections.memory}\n\n" + "\n\n".join(parts)

    def _build_current_user_message(
        self,
        *,
        request: RunRequest,
        workspace_path: Path,
    ) -> str:
        runtime_context = self._prompt_config.runtime_context
        lines = [
            runtime_context.header,
            f"{runtime_context.current_time}: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}",
            f"{runtime_context.session_id}: {request.session_id}",
            f"{runtime_context.workspace_path}: {workspace_path}",
            "",
            request.user_input,
        ]
        if request.attachments:
            lines.extend(
                [
                    "",
                    f"{runtime_context.attachments}:",
                    *[f"- {attachment}" for attachment in request.attachments],
                ]
            )
        return "\n".join(lines)
