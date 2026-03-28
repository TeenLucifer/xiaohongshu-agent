"""Tool registry and execution context."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from agent.tools.base import Tool, ToolDefinition, ToolExecutionContext
from agent.tools.exec import ExecTool
from agent.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool


class ToolExecutionError(Exception):
    """Raised when a tool cannot execute successfully."""


class ToolsRegistry:
    """Registry for built-in runtime tools."""

    def __init__(
        self,
        *,
        allowed_dir: Path | None = None,
        extra_allowed_dirs: list[Path] | None = None,
        restrict_to_workspace: bool = True,
        register_defaults: bool = True,
    ) -> None:
        self._context = ToolExecutionContext(
            allowed_dir=allowed_dir.resolve() if allowed_dir is not None else None,
            extra_allowed_dirs=[path.resolve() for path in (extra_allowed_dirs or [])],
            restrict_to_workspace=restrict_to_workspace,
        )
        self._tools: dict[str, Tool] = {}
        if register_defaults:
            self._register_defaults()

    def for_context(
        self,
        *,
        allowed_dir: Path | None = None,
        extra_allowed_dirs: list[Path] | None = None,
        restrict_to_workspace: bool | None = None,
    ) -> ToolsRegistry:
        """Create a new registry view bound to one execution context."""

        cloned = ToolsRegistry(
            allowed_dir=allowed_dir if allowed_dir is not None else self._context.allowed_dir,
            extra_allowed_dirs=(
                extra_allowed_dirs
                if extra_allowed_dirs is not None
                else list(self._context.extra_allowed_dirs)
            ),
            restrict_to_workspace=(
                self._context.restrict_to_workspace
                if restrict_to_workspace is None
                else restrict_to_workspace
            ),
            register_defaults=False,
        )
        cloned._tools = self._tools.copy()
        return cloned

    def register(self, tool: Tool) -> None:
        """Register one tool implementation."""

        self._tools[tool.name] = tool

    def list_tool_definitions(self) -> list[ToolDefinition]:
        """List definitions for all registered tools."""

        return [tool.definition() for tool in self._tools.values()]

    def execute_tool(self, name: str, arguments: dict[str, object]) -> object:
        """Execute one registered tool."""

        tool = self._tools.get(name)
        if tool is None:
            raise ToolExecutionError(f"Tool '{name}' is not registered")
        try:
            return tool.run(arguments, self._context)
        except (ValidationError, ValueError, FileNotFoundError) as exc:
            raise ToolExecutionError(str(exc)) from exc

    def _register_defaults(self) -> None:
        self.register(ReadFileTool())
        self.register(WriteFileTool())
        self.register(EditFileTool())
        self.register(ListDirTool())
        self.register(ExecTool())
