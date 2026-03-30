from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, cast

import pytest

from agent.tools.registry import ToolExecutionError, ToolsRegistry

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2Y6a0AAAAASUVORK5CYII="
)


def make_registry(tmp_path: Path) -> tuple[ToolsRegistry, Path, Path, Path]:
    workspace = tmp_path / "workspace"
    extra = tmp_path / "skills" / "demo"
    temp_dir = tmp_path / "tmp"
    workspace.mkdir(parents=True)
    extra.mkdir(parents=True)
    temp_dir.mkdir(parents=True)
    registry = ToolsRegistry(
        allowed_dir=workspace,
        extra_allowed_dirs=[extra, temp_dir],
    )
    return registry, workspace, extra, temp_dir


def test_registry_registers_default_tools(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    names = [tool.name for tool in registry.list_tool_definitions()]

    assert names == ["read_file", "write_file", "edit_file", "list_dir", "exec"]


def test_filesystem_tools_read_write_and_list_dir(tmp_path: Path) -> None:
    registry, workspace, _, _ = make_registry(tmp_path)

    write_result = registry.execute_tool(
        "write_file",
        {"path": "notes/idea.txt", "content": "hello world"},
    )
    read_result = registry.execute_tool("read_file", {"path": "notes/idea.txt"})
    list_result = registry.execute_tool("list_dir", {"path": "notes"})
    write_payload = cast(dict[str, Any], write_result)
    list_payload = cast(dict[str, Any], list_result)

    assert write_payload["path"] == str(workspace / "notes" / "idea.txt")
    assert read_result == "hello world"
    assert cast(list[dict[str, Any]], list_payload["entries"])[0]["name"] == "idea.txt"


def test_write_file_serializes_json_objects(tmp_path: Path) -> None:
    registry, workspace, _, _ = make_registry(tmp_path)

    write_result = registry.execute_tool(
        "write_file",
        {
            "path": "notes/payload.json",
            "content": {"posts": [{"post_id": "note-1", "title": "标题"}]},
        },
    )
    write_payload = cast(dict[str, Any], write_result)
    saved = json.loads((workspace / "notes" / "payload.json").read_text(encoding="utf-8"))

    assert write_payload["path"] == str(workspace / "notes" / "payload.json")
    assert saved["posts"][0]["post_id"] == "note-1"


def test_write_file_rejects_non_text_non_json_inputs(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    with pytest.raises(ToolExecutionError):
        registry.execute_tool("write_file", {"path": "notes/value.json", "content": 42})


def test_filesystem_tools_can_read_files_from_extra_allowed_skill_dirs(tmp_path: Path) -> None:
    registry, _, extra, _ = make_registry(tmp_path)
    skill_file = extra / "SKILL.md"
    skill_file.write_text("demo skill", encoding="utf-8")

    result = registry.execute_tool("read_file", {"path": str(skill_file)})

    assert result == "demo skill"


def test_read_file_supports_images(tmp_path: Path) -> None:
    registry, workspace, _, _ = make_registry(tmp_path)
    image_path = workspace / "tiny.png"
    image_path.write_bytes(PNG_1X1)

    result = registry.execute_tool("read_file", {"path": "tiny.png"})
    payload = cast(dict[str, Any], result)

    assert payload["type"] == "image"
    assert payload["mime_type"] == "image/png"
    assert payload["path"] == str(image_path)


def test_edit_file_supports_fuzzy_whitespace_matching(tmp_path: Path) -> None:
    registry, workspace, _, _ = make_registry(tmp_path)
    target = workspace / "draft.md"
    target.write_text("alpha\n  beta\n gamma\n", encoding="utf-8")

    result = registry.execute_tool(
        "edit_file",
        {
            "path": "draft.md",
            "old_text": "alpha\nbeta\ngamma",
            "new_text": "done",
        },
    )
    payload = cast(dict[str, Any], result)

    assert target.read_text(encoding="utf-8") == "done\n"
    assert payload["updated"] is True


def test_filesystem_tools_block_paths_outside_allowed_dirs(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("blocked", encoding="utf-8")

    with pytest.raises(ToolExecutionError):
        registry.execute_tool("read_file", {"path": str(outside)})


def test_exec_allows_pwd_but_blocks_other_diagnostic_commands(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    pwd_result = registry.execute_tool("exec", {"command": "pwd"})

    assert "Exit code: 0" in cast(str, pwd_result)

    with pytest.raises(ToolExecutionError):
        registry.execute_tool("exec", {"command": "ls -la"})

    with pytest.raises(ToolExecutionError):
        registry.execute_tool("exec", {"command": "cat README.md"})


def test_exec_can_run_python_scripts_inside_extra_allowed_skill_dirs(tmp_path: Path) -> None:
    registry, _, extra, _ = make_registry(tmp_path)
    scripts_dir = extra / "scripts"
    scripts_dir.mkdir(parents=True)
    script = scripts_dir / "hello.py"
    script.write_text("print('skill ok')\n", encoding="utf-8")

    result = registry.execute_tool(
        "exec",
        {
            "command": "python scripts/hello.py",
            "working_dir": str(extra),
            "timeout": 5,
        },
    )

    output = cast(str, result)
    assert "Exit code: 0" in output
    assert "skill ok" in output


def test_exec_blocks_dangerous_commands_even_if_prefixed(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    with pytest.raises(ToolExecutionError):
        registry.execute_tool(
            "exec",
            {"command": "python -c \"import os; os.system('rm -rf /tmp/x')\""},
        )


def test_exec_allows_specific_uv_run_and_npx_playwright_prefixes(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    uv_result = registry.execute_tool(
        "exec",
        {"command": "uv run python -c \"print('ok')\"", "timeout": 5},
    )
    npx_result = registry.execute_tool(
        "exec",
        {"command": "npx playwright --version", "timeout": 5},
    )
    uv_output = cast(str, uv_result)
    npx_output = cast(str, npx_result)

    assert "Exit code:" in uv_output
    assert "ok" in uv_output
    assert "Error:" in npx_output or "Exit code:" in npx_output


def test_exec_enforces_timeout_and_max_timeout(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    with pytest.raises(ToolExecutionError):
        registry.execute_tool("exec", {"command": "python -c \"print('x')\"", "timeout": 601})

    timeout_result = registry.execute_tool(
        "exec",
        {"command": 'python -c "import time; time.sleep(2)"', "timeout": 1},
    )
    timeout_output = cast(str, timeout_result)

    assert "Exit code:" in timeout_output or "Error:" in timeout_output


def test_exec_truncates_large_output(tmp_path: Path) -> None:
    registry, _, _, _ = make_registry(tmp_path)

    result = registry.execute_tool(
        "exec",
        {
            "command": "python -c \"print('A'*12000)\"",
            "timeout": 5,
        },
    )
    output = cast(str, result)

    assert "Exit code: 0" in output
    assert "[truncated]" in output


def test_exec_returns_clear_errors_for_private_urls_and_working_dir_escape(tmp_path: Path) -> None:
    registry, workspace, _, _ = make_registry(tmp_path)

    with pytest.raises(ToolExecutionError):
        registry.execute_tool(
            "exec",
            {"command": "python -c \"print('http://127.0.0.1:8000')\""},
        )

    with pytest.raises(ToolExecutionError):
        registry.execute_tool(
            "exec",
            {
                "command": "python -c \"print('ok')\"",
                "working_dir": str(workspace.parent),
            },
        )
