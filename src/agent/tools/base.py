"""Base tool abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Serializable tool definition exposed to the model layer."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionContext(BaseModel):
    """Execution-time path restrictions for tools."""

    allowed_dir: Path | None = None
    extra_allowed_dirs: list[Path] = Field(default_factory=list)
    restrict_to_workspace: bool = True


class ToolArguments(BaseModel):
    """Base class for tool argument models."""


class Tool(ABC):
    """Abstract base class for runtime tools."""

    name: str
    description: str
    arguments_model: type[ToolArguments]

    def definition(self) -> ToolDefinition:
        """Build the model-facing tool definition."""

        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.arguments_model.model_json_schema(),
        )

    def run(self, arguments: dict[str, object], context: ToolExecutionContext) -> object:
        """Validate input and execute the tool."""

        validated = self.arguments_model.model_validate(arguments)
        return self.execute(arguments=validated, context=context)

    @abstractmethod
    def execute(self, *, arguments: ToolArguments, context: ToolExecutionContext) -> object:
        """Execute the tool with validated arguments."""


class PathArguments(ToolArguments):
    """Common path-bearing arguments."""

    path: str = Field(min_length=1)


def resolve_allowed_path(
    *,
    raw_path: str,
    context: ToolExecutionContext,
    must_exist: bool = False,
) -> Path:
    """Resolve a path under the allowed directories."""

    if context.allowed_dir is None:
        raise ValueError("No tool execution context configured")

    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (context.allowed_dir / candidate).resolve()

    allowed_roots = [context.allowed_dir, *context.extra_allowed_dirs]
    if not any(_is_under(resolved, root) for root in allowed_roots):
        raise ValueError(f"Path is outside allowed directories: {raw_path}")

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {raw_path}")

    return resolved


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False
