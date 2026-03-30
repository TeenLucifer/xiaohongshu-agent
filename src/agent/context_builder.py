"""Context builder for runtime foundation."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

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
        parts: list[str] = [self._build_identity_rules(workspace_path=workspace_path)]

        parts.append(self._build_memory_section(memory_context))

        if always_skills:
            parts.append(f"# {self._prompt_config.sections.always_skills}\n\n{always_skills}")

        if skills_summary:
            parts.append(self._build_skills_summary_section(skills_summary))

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

    def _build_identity_rules(self, *, workspace_path: Path) -> str:
        skills_root = self._project_root / "skills"
        top_level_rule = (
            f"- 若 skill 文件位于 {skills_root}/<name>/SKILL.md，"
            f"则默认执行根目录为 {skills_root}/<name>"
        )
        nested_rule = (
            f"- 若 skill 文件位于 {skills_root}/<bundle>/skills/<child>/SKILL.md，"
            f"则默认执行根目录为 {skills_root}/<bundle>"
        )
        accessible_paths = "\n".join(
            [
                "当前允许访问的目录包括：",
                f"- {workspace_path}",
                f"- {skills_root}",
                "",
                "builtin skill 的相对路径命令解析规则：",
                top_level_rule,
                nested_rule,
                (
                    "- 当命令示例使用 `python scripts/...` 这类相对路径时，"
                    "不要在 session workspace 中直接执行。"
                ),
            ]
        )
        return "\n".join(
            [
                f"# {self._prompt_config.identity.title}",
                *self._prompt_config.identity.rules,
                accessible_paths,
            ]
        )

    def _build_memory_section(self, memory_context: str) -> str:
        rules = "\n".join(f"- {rule}" for rule in self._prompt_config.memory.rules)
        parts = [f"## {self._prompt_config.memory.rules_title}\n\n{rules}"]
        if memory_context:
            parts.append(memory_context)
        return f"# {self._prompt_config.sections.memory}\n\n" + "\n\n".join(parts)

    def _build_skills_summary_section(self, skills_summary: str) -> str:
        intro = (
            "以下是当前可用技能的概览。"
            "如果你要使用某个 skill，请先读取对应的 SKILL.md，再根据其中说明执行。"
        )
        return f"# {self._prompt_config.sections.skills_summary}\n\n{intro}\n\n{skills_summary}"

    def _build_current_user_message(
        self,
        *,
        request: RunRequest,
        workspace_path: Path,
    ) -> str:
        runtime_context = self._prompt_config.runtime_context
        workspace_data_root = workspace_path / "workspace"
        lines = [
            runtime_context.header,
            f"{runtime_context.current_time}: {format_runtime_time()}",
            f"{runtime_context.session_id}: {request.session_id}",
            f"{runtime_context.workspace_path}: {workspace_path}",
            f"{runtime_context.workspace_data_root}: {workspace_data_root}",
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
