"""Context builder for runtime foundation."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from agent.errors import PromptConfigError
from agent.models import PromptMessage, RunRequest
from agent.prompts import RuntimePromptLoader
from agent.time_utils import format_runtime_time


class ContextBuilder:
    """Builds the system prompt and current message list."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._prompt_config = RuntimePromptLoader().load()

    def build_system_prompt(
        self,
        *,
        workspace_path: Path,
        memory_context: str = "",
        always_skills: str = "",
        skills_summary: str = "",
    ) -> str:
        skills_root = self._project_root / "skills"
        return self._render_template(
            self._prompt_config.system.template,
            {
                "workspace_path": workspace_path,
                "skills_root": skills_root,
                "memory_context_block": self._build_memory_context_block(memory_context),
                "always_skills_block": self._build_always_skills_block(always_skills),
                "skills_summary_block": self._build_skills_summary_block(skills_summary),
            },
        )

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

    def _build_current_user_message(
        self,
        *,
        request: RunRequest,
        workspace_path: Path,
    ) -> str:
        workspace_data_root = workspace_path / "workspace"
        return self._render_template(
            self._prompt_config.user.template,
            {
                "current_time": format_runtime_time(),
                "session_id": request.session_id,
                "workspace_path": workspace_path,
                "workspace_data_root": workspace_data_root,
                "attachments_block": self._build_attachments_block(request.attachments),
                "user_input": request.user_input,
            },
        )

    def _build_memory_context_block(self, memory_context: str) -> str:
        if not memory_context:
            return ""
        return self._render_template(
            self._prompt_config.system.memory_context_template,
            {"memory_context": memory_context},
        )

    def _build_always_skills_block(self, always_skills: str) -> str:
        if not always_skills:
            return ""
        return self._render_template(
            self._prompt_config.system.always_skills_template,
            {"always_skills": always_skills},
        )

    def _build_skills_summary_block(self, skills_summary: str) -> str:
        if not skills_summary:
            return ""
        return self._render_template(
            self._prompt_config.system.skills_summary_template,
            {"skills_summary": skills_summary},
        )

    def _build_attachments_block(self, attachments: list[str]) -> str:
        if not attachments:
            return ""
        return self._render_template(
            self._prompt_config.user.attachments_template,
            {"attachment_lines": "\n".join(f"- {attachment}" for attachment in attachments)},
        )

    def _render_template(self, template: str, values: dict[str, object]) -> str:
        try:
            rendered = template.format_map(values)
        except KeyError as exc:
            raise PromptConfigError(f"Missing runtime prompt placeholder: {exc.args[0]}") from exc
        return rendered.strip()
