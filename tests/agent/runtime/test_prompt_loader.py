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
                "sections:",
                '  bootstrap_files: "Bootstrap Files"',
                '  memory: "Memory"',
                '  always_skills: "Always Skills"',
                '  skills_summary: "Skills Summary"',
                "identity:",
                '  title: "Identity"',
                "  rules:",
                '    - "rule one"',
                "memory:",
                '  rules_title: "Memory Rules"',
                "  rules:",
                '    - "remember facts"',
                '  consolidation_system: "system prompt"',
                '  consolidation_user_template: "user {current_memory} {messages_text}"',
                "runtime_context:",
                '  header: "[Runtime Context]"',
                '  current_time: "Current Time"',
                '  session_id: "Session ID"',
                '  workspace_path: "Workspace Path"',
                '  attachments: "Attachments"',
            ]
        ),
        encoding="utf-8",
    )

    config = RuntimePromptLoader(config_path).load()

    assert config.identity.title == "Identity"
    assert config.identity.rules == ["rule one"]
    assert config.runtime_context.workspace_path == "Workspace Path"


def test_runtime_prompt_loader_raises_for_invalid_yaml_schema(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text("identity: {}\n", encoding="utf-8")

    with pytest.raises(PromptConfigError):
        RuntimePromptLoader(config_path).load()
