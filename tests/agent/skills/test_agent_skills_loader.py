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


def write_nested_skill(
    parent_dir: Path,
    name: str,
    *,
    frontmatter: str,
    body: str = "skill body",
) -> Path:
    return write_skill(parent_dir / "skills", name, frontmatter=frontmatter, body=body)


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


def test_frontmatter_supports_yaml_multiline_description_and_nested_metadata(
    tmp_path: Path,
) -> None:
    builtin = tmp_path / "builtin"
    write_skill(
        builtin,
        "demo",
        frontmatter=(
            "name: demo\n"
            "description: |\n"
            "  第一行描述\n"
            "  第二行描述\n"
            "metadata:\n"
            "  openclaw:\n"
            "    always: true\n"
            "    requires:\n"
            "      bins:\n"
            "        - python3\n"
        ),
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    record = loader.require_skill("demo")

    assert record.description == "第一行描述\n第二行描述\n"
    assert record.metadata["description"] == "第一行描述\n第二行描述\n"
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


def test_build_skills_summary_includes_real_description_and_location(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    path = write_skill(
        builtin,
        "demo",
        frontmatter=("name: demo\ndescription: |\n  小红书发布技能\n  支持图文内容草稿\n"),
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    summary = loader.build_skills_summary()

    assert "<name>demo</name>" in summary
    assert "<description>小红书发布技能\n支持图文内容草稿\n</description>" in summary
    assert f"<location>{path}</location>" in summary


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


def test_list_skills_discovers_parent_and_nested_skills(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    parent_dir = builtin / "xiaohongshu-skills"
    write_skill(
        builtin,
        "xiaohongshu-skills",
        frontmatter="name: xiaohongshu-skills\ndescription: parent skill",
    )
    write_nested_skill(
        parent_dir,
        "xhs-auth",
        frontmatter="name: xhs-auth\ndescription: auth skill",
    )
    write_nested_skill(
        parent_dir,
        "xhs-publish",
        frontmatter="name: xhs-publish\ndescription: publish skill",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills(filter_unavailable=False)

    assert [skill.name for skill in skills] == [
        "xiaohongshu-skills",
        "xhs-auth",
        "xhs-publish",
    ]


def test_recursive_discovery_only_walks_nested_skills_container(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    parent_dir = builtin / "xiaohongshu-skills"
    write_skill(
        builtin,
        "xiaohongshu-skills",
        frontmatter="name: xiaohongshu-skills\ndescription: parent skill",
    )
    scripts_dir = parent_dir / "scripts" / "fake-skill"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "SKILL.md").write_text(
        "---\nname: fake-skill\ndescription: should not load\n---\n",
        encoding="utf-8",
    )
    assets_dir = parent_dir / "assets" / "fake-asset-skill"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "SKILL.md").write_text(
        "---\nname: fake-asset-skill\ndescription: should not load\n---\n",
        encoding="utf-8",
    )
    write_nested_skill(
        parent_dir,
        "xhs-auth",
        frontmatter="name: xhs-auth\ndescription: auth skill",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills(filter_unavailable=False)

    assert [skill.name for skill in skills] == ["xiaohongshu-skills", "xhs-auth"]


def test_recursive_discovery_skips_noise_directories(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    parent_dir = builtin / "xiaohongshu-skills"
    write_skill(
        builtin,
        "xiaohongshu-skills",
        frontmatter="name: xiaohongshu-skills\ndescription: parent skill",
    )
    for dirname in (".git", "node_modules", "__pycache__", ".hidden"):
        noise_dir = parent_dir / "skills" / dirname / "ignored"
        noise_dir.mkdir(parents=True, exist_ok=True)
        (noise_dir / "SKILL.md").write_text(
            "---\nname: ignored\ndescription: should not load\n---\n",
            encoding="utf-8",
        )
    write_nested_skill(
        parent_dir,
        "xhs-auth",
        frontmatter="name: xhs-auth\ndescription: auth skill",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    skills = loader.list_skills(filter_unavailable=False)

    assert [skill.name for skill in skills] == ["xiaohongshu-skills", "xhs-auth"]


def test_same_source_recursive_collision_keeps_first_discovered_skill(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    parent_dir = builtin / "xiaohongshu-skills"
    write_skill(
        builtin,
        "alpha-parent",
        frontmatter="name: alpha-parent\ndescription: alpha parent",
    )
    write_nested_skill(
        builtin / "alpha-parent",
        "shared-skill",
        frontmatter="name: shared-skill\ndescription: first skill",
    )
    write_skill(
        builtin,
        "xiaohongshu-skills",
        frontmatter="name: xiaohongshu-skills\ndescription: parent skill",
    )
    write_nested_skill(
        parent_dir,
        "shared-skill",
        frontmatter="name: shared-skill\ndescription: second skill",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    record = loader.require_skill("shared-skill")

    assert record.description == "first skill"


def test_workspace_nested_skill_overrides_builtin_nested_skill(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    workspace = tmp_path / "workspace"
    builtin_parent = builtin / "xiaohongshu-skills"
    workspace_parent = workspace / "skills" / "xiaohongshu-skills"
    write_skill(
        builtin,
        "xiaohongshu-skills",
        frontmatter="name: xiaohongshu-skills\ndescription: builtin parent",
    )
    write_nested_skill(
        builtin_parent,
        "xhs-auth",
        frontmatter="name: xhs-auth\ndescription: builtin auth",
    )
    write_skill(
        workspace / "skills",
        "xiaohongshu-skills",
        frontmatter="name: xiaohongshu-skills\ndescription: workspace parent",
    )
    write_nested_skill(
        workspace_parent,
        "xhs-auth",
        frontmatter="name: xhs-auth\ndescription: workspace auth",
    )
    loader = SkillsLoader(builtin_skills_dir=builtin)

    record = loader.require_skill("xhs-auth", workspace_path=workspace)

    assert record.source == "workspace"
    assert record.description == "workspace auth"
