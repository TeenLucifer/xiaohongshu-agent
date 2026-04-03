from __future__ import annotations

from pathlib import Path

import pytest

from agent.errors import PromptConfigError
from agent.prompts.loader import RuntimePromptLoader


def test_runtime_prompt_loader_reads_yaml_config(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text(
        "\n".join(
            [
                "system:",
                '  template: >-',
                '    system {workspace_path} {skills_root} {memory_context_block}',
                '    {always_skills_block} {skills_summary_block}',
                '  memory_context_template: "memory {memory_context}"',
                '  always_skills_template: "always {always_skills}"',
                '  skills_summary_template: "summary {skills_summary}"',
                "user:",
                '  template: >-',
                '    Current Time: {current_time}\n'
                '    Session ID: {session_id}\n'
                '    Session Root Path: {workspace_path}\n'
                '    Workspace Data Root: {workspace_data_root}\n'
                '    {attachments_block}\n\n'
                '    {user_input}',
                '  attachments_template: "Attachments:\\n{attachment_lines}"',
                "memory:",
                '  consolidation_system: "system prompt"',
                '  consolidation_user_template: "user {current_memory} {messages_text}"',
            ]
        ),
        encoding="utf-8",
    )

    config = RuntimePromptLoader(config_path).load()

    assert config.system.template.startswith("system")
    assert config.user.template.startswith("Current Time:")
    assert config.memory.consolidation_system == "system prompt"


def test_runtime_prompt_loader_raises_for_invalid_yaml_schema(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text("identity: {}\n", encoding="utf-8")

    with pytest.raises(PromptConfigError):
        RuntimePromptLoader(config_path).load()
