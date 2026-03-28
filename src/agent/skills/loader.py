"""Nanobot-style skills loader with light local adaptation."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

BUILTIN_SKILLS_DIR = Path(__file__).resolve().parents[3] / "skills"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


class SkillRecord(BaseModel):
    """Structured representation of one discovered skill."""

    name: str
    path: Path
    source: str
    description: str
    metadata: dict[str, str] = Field(default_factory=dict)
    nanobot_metadata: dict[str, Any] = Field(default_factory=dict)
    available: bool = True
    missing_requirements: str = ""


class SkillsLoader:
    """Loader for nanobot-style `SKILL.md` folders."""

    def __init__(self, builtin_skills_dir: Path | None = None) -> None:
        self._builtin_skills_dir = builtin_skills_dir or BUILTIN_SKILLS_DIR

    def list_skills(
        self,
        *,
        workspace_path: Path | None = None,
        filter_unavailable: bool = True,
    ) -> list[SkillRecord]:
        skills = self._discover_skills(workspace_path=workspace_path)
        if filter_unavailable:
            return [skill for skill in skills if skill.available]
        return skills

    def build_skills_summary(self, workspace_path: Path | None = None) -> str:
        skills = self.list_skills(workspace_path=workspace_path, filter_unavailable=False)
        if not skills:
            return ""

        lines = ["<skills>"]
        for skill in skills:
            lines.append(f'  <skill available="{str(skill.available).lower()}">')
            lines.append(f"    <name>{_escape_xml(skill.name)}</name>")
            lines.append(f"    <description>{_escape_xml(skill.description)}</description>")
            lines.append(f"    <location>{_escape_xml(str(skill.path))}</location>")
            if not skill.available and skill.missing_requirements:
                lines.append(f"    <requires>{_escape_xml(skill.missing_requirements)}</requires>")
            lines.append("  </skill>")
        lines.append("</skills>")
        return "\n".join(lines)

    def load_skill(self, name: str, workspace_path: Path | None = None) -> str | None:
        record = self.get_skill(name, workspace_path=workspace_path)
        if record is None:
            return None
        return record.path.read_text(encoding="utf-8")

    def require_skill(self, name: str, workspace_path: Path | None = None) -> SkillRecord:
        record = self.get_skill(name, workspace_path=workspace_path)
        if record is None:
            raise ValueError(f"Skill not found: {name}")
        return record

    def get_skill(self, name: str, workspace_path: Path | None = None) -> SkillRecord | None:
        for skill in self._discover_skills(workspace_path=workspace_path):
            if skill.name == name:
                return skill
        return None

    def get_always_skills(self, workspace_path: Path | None = None) -> list[SkillRecord]:
        return [
            skill
            for skill in self.list_skills(workspace_path=workspace_path, filter_unavailable=True)
            if _is_truthy(skill.metadata.get("always"))
            or _is_truthy(skill.nanobot_metadata.get("always"))
        ]

    def load_always_skills_for_context(self, workspace_path: Path | None = None) -> str:
        names = [skill.name for skill in self.get_always_skills(workspace_path=workspace_path)]
        return self.load_skills_for_context(names, workspace_path=workspace_path)

    def load_skills_for_context(
        self,
        skill_names: list[str],
        workspace_path: Path | None = None,
    ) -> str:
        parts: list[str] = []
        for name in skill_names:
            content = self.load_skill(name, workspace_path=workspace_path)
            if not content:
                continue
            stripped = self._strip_frontmatter(content)
            parts.append(f"### Skill: {name}\n\n{stripped}")
        return "\n\n---\n\n".join(parts) if parts else ""

    def _discover_skills(self, workspace_path: Path | None = None) -> list[SkillRecord]:
        discovered: dict[str, SkillRecord] = {}
        for source, root in (
            ("workspace", self._workspace_skills_dir(workspace_path)),
            ("builtin", self._builtin_skills_dir),
        ):
            if root is None or not root.exists():
                continue
            for skill_dir in sorted(root.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_path = skill_dir / "SKILL.md"
                if not skill_path.exists() or skill_dir.name in discovered:
                    continue
                metadata = self._parse_frontmatter(skill_path.read_text(encoding="utf-8"))
                nanobot_metadata = self._parse_nanobot_metadata(metadata.get("metadata", ""))
                missing = self._get_missing_requirements(nanobot_metadata)
                discovered[skill_dir.name] = SkillRecord(
                    name=skill_dir.name,
                    path=skill_path,
                    source=source,
                    description=metadata.get("description", skill_dir.name),
                    metadata=metadata,
                    nanobot_metadata=nanobot_metadata,
                    available=missing == "",
                    missing_requirements=missing,
                )
        return list(discovered.values())

    def _workspace_skills_dir(self, workspace_path: Path | None) -> Path | None:
        if workspace_path is None:
            return None
        return workspace_path / "skills"

    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        match = FRONTMATTER_RE.match(content)
        if match is None:
            return {}
        metadata: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip("\"'")
        return metadata

    def _strip_frontmatter(self, content: str) -> str:
        match = FRONTMATTER_RE.match(content)
        if match is None:
            return content.strip()
        return content[match.end() :].strip()

    def _parse_nanobot_metadata(self, raw: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
        if not isinstance(data, dict):
            return {}
        extracted = data.get("nanobot", data.get("openclaw", {}))
        return extracted if isinstance(extracted, dict) else {}

    def _get_missing_requirements(self, skill_meta: dict[str, Any]) -> str:
        missing: list[str] = []
        requires = skill_meta.get("requires", {})
        if not isinstance(requires, dict):
            return ""
        for binary in requires.get("bins", []):
            if isinstance(binary, str) and shutil.which(binary) is None:
                missing.append(f"CLI: {binary}")
        for env_name in requires.get("env", []):
            if isinstance(env_name, str) and not os.environ.get(env_name):
                missing.append(f"ENV: {env_name}")
        return ", ".join(missing)


def _escape_xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False
