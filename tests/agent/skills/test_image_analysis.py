from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
IMAGE_ANALYSIS_PATH = REPO_ROOT / "skills" / "image-analysis" / "scripts" / "analyze.py"

spec = importlib.util.spec_from_file_location("image_analysis", IMAGE_ANALYSIS_PATH)
assert spec is not None
assert spec.loader is not None
image_analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image_analysis)


def test_load_skill_config_reads_local_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "api_key": "vision-key",
                "base_url": "https://example.com/vision",
                "model": "vision-model",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(image_analysis, "CONFIG_PATH", config_path)

    config = image_analysis.load_skill_config()

    assert config == {
        "api_key": "vision-key",
        "base_url": "https://example.com/vision",
        "model": "vision-model",
    }


def test_load_skill_config_requires_local_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "missing.json"
    monkeypatch.setattr(image_analysis, "CONFIG_PATH", config_path)

    with pytest.raises(ValueError, match="缺少 skill 配置文件"):
        image_analysis.load_skill_config()
