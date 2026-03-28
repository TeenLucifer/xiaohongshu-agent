from __future__ import annotations

from pathlib import Path

from agent.skills.loader import SkillRecord, SkillsLoader


def write_skill(
    base_dir: Path,
    name: str,
    *,
    frontmatter: str,
    body: str = "skill body",
) -> Path:
    skill_dir = base_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    path = skill_dir / "SKILL.md"
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8")
    return path


def test_list_skills_prefers_workspace_over_builtin(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    workspace = tmp_path / "workspace"
    write_skill(
        builtin,
        "demo",
        frontmatter=(
            "name: demo\n"
            "description: builtin demo\n"
            'metadata: {"nanobot":{"requires":{"bins":["python3"]}}}'
        ),
        body="builtin body",
    )
    write_skill(
        workspace / "skills",
        "demo",
        frontmatter=(
            "name: demo\n"
            "description: workspace demo\n"
            'metadata: {"nanobot":{"requires":{"bins":["python3"]}}}'
        ),
        body="workspace body",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills(workspace_path=workspace)

    assert len(skills) == 1
    assert skills[0].source == "workspace"
    assert skills[0].description == "workspace demo"


def test_frontmatter_and_metadata_json_are_parsed(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "demo",
        frontmatter=(
            "name: demo\ndescription: desc\nmetadata: "
            '{"nanobot":{"always":true,"requires":{"bins":["python3"],"env":["OPENAI_API_KEY"]}}}'
        ),
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    record = loader.require_skill("demo")

    assert record.metadata["name"] == "demo"
    assert record.metadata["description"] == "desc"
    assert record.nanobot_metadata["always"] is True
    assert record.nanobot_metadata["requires"]["bins"] == ["python3"]


def test_requirement_check_marks_missing_bins_and_env(tmp_path: Path, monkeypatch) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "demo",
        frontmatter=(
            "name: demo\ndescription: desc\nmetadata: "
            '{"nanobot":{"requires":{"bins":["missing-bin"],"env":["MISSING_ENV"]}}}'
        ),
    )
    monkeypatch.delenv("MISSING_ENV", raising=False)
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills(filter_unavailable=False)

    assert len(skills) == 1
    assert skills[0].available is False
    assert "CLI: missing-bin" in skills[0].missing_requirements
    assert "ENV: MISSING_ENV" in skills[0].missing_requirements


def test_list_skills_filters_unavailable_by_default(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "available",
        frontmatter=(
            "name: available\n"
            "description: ok\n"
            'metadata: {"nanobot":{"requires":{"bins":["python3"]}}}'
        ),
    )
    write_skill(
        builtin,
        "blocked",
        frontmatter=(
            "name: blocked\n"
            "description: nope\n"
            'metadata: {"nanobot":{"requires":{"bins":["missing-bin"]}}}'
        ),
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills()

    assert [skill.name for skill in skills] == ["available"]


def test_build_skills_summary_includes_unavailable_skills(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "blocked",
        frontmatter=(
            "name: blocked\n"
            "description: nope\n"
            'metadata: {"nanobot":{"requires":{"bins":["missing-bin"]}}}'
        ),
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    summary = loader.build_skills_summary()

    assert '<skill available="false">' in summary
    assert "<name>blocked</name>" in summary
    assert "<requires>CLI: missing-bin</requires>" in summary


def test_get_always_skills_returns_only_available_ones(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "always-ok",
        frontmatter=(
            "name: always-ok\n"
            "description: ok\n"
            'metadata: {"nanobot":{"always":true,"requires":{"bins":["python3"]}}}'
        ),
        body="always ok body",
    )
    write_skill(
        builtin,
        "always-blocked",
        frontmatter=(
            "name: always-blocked\n"
            "description: nope\n"
            'metadata: {"nanobot":{"always":true,"requires":{"bins":["missing-bin"]}}}'
        ),
        body="always blocked body",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.get_always_skills()

    assert [skill.name for skill in skills] == ["always-ok"]


def test_load_skill_returns_full_content_and_context_strips_frontmatter(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "demo",
        frontmatter="name: demo\ndescription: desc",
        body="line one\nline two",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    full = loader.load_skill("demo")
    context = loader.load_skills_for_context(["demo"])

    assert full is not None
    assert full.startswith("---\nname: demo")
    assert "### Skill: demo" in context
    assert "line one" in context
    assert "description: desc" not in context


def test_require_skill_raises_for_missing_skill(tmp_path: Path) -> None:
    loader = SkillsLoader(builtin_skills_dir=tmp_path / "builtin")

    try:
        loader.require_skill("missing")
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_runtime_loader_return_type_is_structured(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "demo",
        frontmatter="name: demo\ndescription: desc",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills(filter_unavailable=False)

    assert isinstance(skills[0], SkillRecord)
