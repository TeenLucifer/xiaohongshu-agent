"""Filesystem tools."""

from __future__ import annotations

import base64
import json
import mimetypes
from typing import Any

from pydantic import Field

from agent.tools.base import (
    PathArguments,
    Tool,
    ToolArguments,
    ToolExecutionContext,
    resolve_allowed_path,
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


class ReadFileArguments(PathArguments):
    """Arguments for reading one file."""


class WriteFileArguments(PathArguments):
    """Arguments for writing one file."""

    content: str | dict[str, Any] | list[Any]


class EditFileArguments(PathArguments):
    """Arguments for editing one file."""

    old_text: str = Field(min_length=1)
    new_text: str


class ListDirArguments(PathArguments):
    """Arguments for listing one directory."""


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a text or image file from the allowed workspace."
    arguments_model = ReadFileArguments

    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        args = ReadFileArguments.model_validate(arguments)
        path = resolve_allowed_path(raw_path=args.path, context=context, must_exist=True)
        if path.is_dir():
            raise ValueError(f"Expected a file but got directory: {args.path}")
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            return {
                "type": "image",
                "path": str(path),
                "mime_type": mime_type,
                "base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
        return path.read_text(encoding="utf-8")


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write a text or JSON file inside the allowed workspace."
    arguments_model = WriteFileArguments

    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        args = WriteFileArguments.model_validate(arguments)
        path = resolve_allowed_path(raw_path=args.path, context=context)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = _serialize_write_content(args.content)
        path.write_text(content, encoding="utf-8")
        return {"path": str(path), "bytes_written": len(content.encode("utf-8"))}


class EditFileTool(Tool):
    name = "edit_file"
    description = "Replace text in a file with exact or fuzzy whitespace matching."
    arguments_model = EditFileArguments

    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        args = EditFileArguments.model_validate(arguments)
        path = resolve_allowed_path(raw_path=args.path, context=context, must_exist=True)
        content = path.read_text(encoding="utf-8")
        updated = _apply_edit(content=content, old_text=args.old_text, new_text=args.new_text)
        if updated is None:
            raise ValueError("Could not find text to replace")
        path.write_text(updated, encoding="utf-8")
        return {"path": str(path), "updated": True}


class ListDirTool(Tool):
    name = "list_dir"
    description = "List directory entries inside the allowed workspace."
    arguments_model = ListDirArguments

    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        args = ListDirArguments.model_validate(arguments)
        path = resolve_allowed_path(raw_path=args.path, context=context, must_exist=True)
        if not path.is_dir():
            raise ValueError(f"Expected a directory but got file: {args.path}")
        entries = [
            {
                "name": child.name,
                "path": str(child),
                "is_dir": child.is_dir(),
            }
            for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name))
        ]
        return {"path": str(path), "entries": entries}


def _apply_edit(*, content: str, old_text: str, new_text: str) -> str | None:
    if old_text in content:
        updated = content.replace(old_text, new_text, 1)
        if content.endswith("\n") and not updated.endswith("\n"):
            updated += "\n"
        return updated

    content_lines = content.splitlines(keepends=True)
    old_lines = old_text.splitlines()
    if not old_lines:
        return None

    normalized_old = [_normalize_line(line) for line in old_lines]
    normalized_content = [_normalize_line(line) for line in content_lines]
    window = len(normalized_old)
    for start in range(len(normalized_content) - window + 1):
        if normalized_content[start : start + window] != normalized_old:
            continue
        leading = "".join(content_lines[:start])
        trailing = "".join(content_lines[start + window :])
        replacement = new_text
        if (trailing or content.endswith("\n")) and not replacement.endswith("\n"):
            replacement += "\n"
        return leading + replacement + trailing
    return None


def _normalize_line(value: str) -> str:
    return "".join(value.split())


def _serialize_write_content(value: str | dict[str, Any] | list[Any]) -> str:
    if isinstance(value, str):
        return value
    serialized = json.dumps(value, ensure_ascii=False, indent=2)
    if not serialized.endswith("\n"):
        serialized += "\n"
    return serialized
