from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
IMAGE_GENERATION_PATH = REPO_ROOT / "skills" / "image-generation" / "scripts" / "generate.py"

spec = importlib.util.spec_from_file_location("image_generation", IMAGE_GENERATION_PATH)
assert spec is not None
assert spec.loader is not None
image_generation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image_generation)


def _write_png(path: Path) -> None:
    path.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A"
            "0000000D49484452000000010000000108060000001F15C489"
            "0000000D49444154789C6360606060000000040001F6173855"
            "0000000049454E44AE426082"
        )
    )


def test_resolve_selected_editor_images_requires_existing_order() -> None:
    with pytest.raises(ValueError, match="不存在的图片编号"):
        image_generation.resolve_selected_editor_images(
            editor_images=[
                {"id": "img-1", "order": 1, "image_path": "editor/1.png"},
            ],
            prompt="参考 2 号图生成一张新图",
        )


def test_load_reference_images_reads_original_files(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    image_path = workspace_root / "editor" / "1.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    _write_png(image_path)

    references = image_generation.load_reference_images(
        workspace_root=workspace_root,
        selected_images=[
            {"id": "img-1", "order": 1, "image_path": "editor/1.png"},
        ],
    )

    assert len(references) == 1
    assert references[0]["reference_id"] == 1
    assert str(references[0]["data_url"]).startswith("data:image/png;base64,")


def test_generate_image_bytes_calls_gemini_edit_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    edit_calls: list[dict] = []

    class FakeModels:
        def create(self, **kwargs):  # noqa: ANN003, ANN201
            edit_calls.append(kwargs)

            class _InlineData:
                data = "Z2VuZXJhdGVkLWltYWdl"

            class _Part:
                inline_data = _InlineData()

            class _Message:
                multi_mod_content = [_Part()]

            class _Choice:
                message = _Message()

            class _Response:
                choices = [_Choice()]

            return _Response()

    class FakeChat:
        completions = FakeModels()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(
        image_generation,
        "get_api_config",
        lambda: ("test-key", "https://example.com/gemini", "gemini-test", "1024x1024"),
    )
    monkeypatch.setattr(
        image_generation,
        "create_gemini_client",
        lambda api_key, base_url: FakeClient(),
    )

    result = image_generation.generate_image_bytes(
        prompt="参考 1 号图生成",
        reference_images=[
            {"reference_id": 1, "data_url": "data:image/png;base64,cmVmZXJlbmNlLWltYWdl"}
        ],
        referenced_orders=[1],
    )

    assert result == b"generated-image"
    assert len(edit_calls) == 1
    assert edit_calls[0]["model"] == "gemini-test"
    assert edit_calls[0]["modalities"] == ["text", "image"]
    first_message = edit_calls[0]["messages"][0]
    content = first_message["content"]
    assert "当前参考编号：1" in content[0]["text"]
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_generate_image_bytes_raises_when_edit_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCompletions:
        def create(self, **kwargs):  # noqa: ANN003, ANN201
            raise RuntimeError("gemini edit failed")

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(
        image_generation,
        "get_api_config",
        lambda: ("test-key", "https://example.com/gemini", "gemini-test", "1024x1024"),
    )
    monkeypatch.setattr(
        image_generation,
        "create_gemini_client",
        lambda api_key, base_url: FakeClient(),
    )

    with pytest.raises(RuntimeError, match="gemini edit failed"):
        image_generation.generate_image_bytes(
            prompt="参考 1 号图生成",
            reference_images=[
                {"reference_id": 1, "data_url": "data:image/png;base64,cmVmZXJlbmNlLWltYWdl"}
            ],
            referenced_orders=[1],
        )


def test_generate_into_workspace_appends_result_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    image_path = workspace_root / "editor" / "1.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    _write_png(image_path)
    (workspace_root / "editor_images.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "editor-1",
                        "order": 1,
                        "source_type": "material",
                        "alt": "参考图",
                        "image_path": "editor/1.png",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        image_generation,
        "generate_image_bytes",
        lambda *args, **kwargs: b"png-bytes",
    )

    result = image_generation.generate_into_workspace(
        workspace_root=workspace_root,
        prompt="参考 1 号图生成",
    )

    assert result["success"] is True
    output_path = workspace_root / result["image_path"]
    assert output_path.read_bytes() == b"png-bytes"

    image_results = json.loads((workspace_root / "image_results.json").read_text(encoding="utf-8"))
    assert len(image_results["items"]) == 1
    assert image_results["items"][0]["source_editor_image_ids"] == ["editor-1"]
