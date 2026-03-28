"""Loader for internal runtime prompt configuration."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from agent.errors import PromptConfigError


class PromptSectionTitles(BaseModel):
    bootstrap_files: str
    memory: str
    always_skills: str
    skills_summary: str


class IdentityPromptConfig(BaseModel):
    title: str
    rules: list[str] = Field(min_length=1)


class RuntimeContextLabels(BaseModel):
    header: str
    current_time: str
    session_id: str
    workspace_path: str
    attachments: str


class MemoryPromptConfig(BaseModel):
    rules_title: str
    rules: list[str] = Field(min_length=1)
    consolidation_system: str
    consolidation_user_template: str


class RuntimePromptConfig(BaseModel):
    sections: PromptSectionTitles
    identity: IdentityPromptConfig
    memory: MemoryPromptConfig
    runtime_context: RuntimeContextLabels


class RuntimePromptLoader:
    """Loads static runtime prompt text from a YAML file."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path(__file__).with_name("runtime.yaml")
        self._cached: RuntimePromptConfig | None = None

    def load(self) -> RuntimePromptConfig:
        if self._cached is not None:
            return self._cached

        if not self._config_path.exists():
            raise PromptConfigError(f"Runtime prompt config not found: {self._config_path}")

        try:
            raw = yaml.safe_load(self._config_path.read_text(encoding="utf-8")) or {}
            self._cached = RuntimePromptConfig.model_validate(raw)
        except (OSError, yaml.YAMLError, ValidationError) as exc:
            raise PromptConfigError(
                f"Failed to load runtime prompt config: {self._config_path}"
            ) from exc

        return self._cached
