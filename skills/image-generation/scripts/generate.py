"""基于编辑区参考图和提示词生成图片，并写回 workspace。"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from openai import OpenAI

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"
DEFAULT_GEMINI_IMAGE_BASE_URL = "https://aihubmix.com/v1"
DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image-preview"
DEFAULT_GEMINI_IMAGE_SIZE = "1024x1024"
REFERENCE_PATTERN = re.compile(r"(\d+)\s*号图")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n", encoding="utf-8")


def parse_referenced_orders(prompt: str) -> list[int]:
    seen: set[int] = set()
    orders: list[int] = []
    for match in REFERENCE_PATTERN.finditer(prompt):
        order = int(match.group(1))
        if order in seen:
            continue
        seen.add(order)
        orders.append(order)
    return orders


def load_editor_images(workspace_root: Path) -> list[dict]:
    path = workspace_root / "editor_images.json"
    if not path.exists():
        return []
    payload = load_json(path)
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []
    return sorted(
        [item for item in items if isinstance(item, dict)],
        key=lambda item: int(item.get("order", 0)),
    )


def resolve_selected_editor_images(
    editor_images: list[dict],
    prompt: str,
) -> tuple[list[dict], list[int]]:
    referenced_orders = parse_referenced_orders(prompt)
    if not editor_images:
        raise ValueError("编辑区为空，请先拖入参考图。")
    if not referenced_orders:
        return editor_images, [int(item["order"]) for item in editor_images]

    order_map = {
        int(item["order"]): item for item in editor_images if isinstance(item.get("order"), int)
    }
    missing = [order for order in referenced_orders if order not in order_map]
    if missing:
        raise ValueError(f"引用了不存在的图片编号：{', '.join(str(item) for item in missing)}。")
    return [order_map[order] for order in referenced_orders], referenced_orders


def get_api_config() -> tuple[str, str, str, str]:
    if not CONFIG_PATH.exists():
        raise ValueError(f"缺少 skill 配置文件: {CONFIG_PATH}")

    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"skill 配置文件格式错误: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("skill 配置文件格式错误: 根对象必须是 JSON object")

    api_key = str(payload.get("api_key", "")).strip()
    base_url = str(payload.get("base_url", DEFAULT_GEMINI_IMAGE_BASE_URL)).strip()
    model = str(payload.get("model", DEFAULT_GEMINI_IMAGE_MODEL)).strip()
    image_size = str(payload.get("size", DEFAULT_GEMINI_IMAGE_SIZE)).strip()
    if not api_key:
        raise ValueError(f"{CONFIG_PATH} 缺少 api_key")
    return (
        api_key,
        base_url or DEFAULT_GEMINI_IMAGE_BASE_URL,
        model or DEFAULT_GEMINI_IMAGE_MODEL,
        image_size or DEFAULT_GEMINI_IMAGE_SIZE,
    )


def guess_mime_type(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(image_path.name)
    if mime_type is None:
        raise ValueError(f"无法识别参考图 MIME 类型：{image_path.name}")
    return mime_type


def load_reference_images(
    workspace_root: Path,
    selected_images: list[dict],
) -> list[dict[str, str | int]]:
    references: list[dict[str, str | int]] = []
    for item in selected_images:
        image_path = workspace_root / str(item.get("image_path", ""))
        if not image_path.exists():
            raise FileNotFoundError(f"参考图不存在：{image_path}")
        mime_type = guess_mime_type(image_path)
        image_base64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        references.append(
            {
                "reference_id": int(item.get("order", len(references) + 1)),
                "data_url": f"data:{mime_type};base64,{image_base64}",
            }
        )
    return references


def create_gemini_client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


def extract_image_bytes(response: object) -> bytes:
    choices = getattr(response, "choices", None) or []
    if not choices:
        raise RuntimeError("Gemini 图片生成响应缺少 choices。")
    message = getattr(choices[0], "message", None)
    if message is None:
        raise RuntimeError("Gemini 图片生成响应缺少 message。")
    multi_mod_content = getattr(message, "multi_mod_content", None) or []
    for part in multi_mod_content:
        inline_data = None
        if isinstance(part, dict):
            inline_data = part.get("inline_data")
        else:
            inline_data = getattr(part, "inline_data", None)
        if not inline_data:
            continue
        if isinstance(inline_data, dict):
            data = inline_data.get("data")
        else:
            data = getattr(inline_data, "data", None)
        if data:
            return base64.b64decode(data)
    raise RuntimeError("Gemini 图片生成响应缺少 inline_data 图片结果。")


def generate_image_bytes(
    prompt: str,
    reference_images: list[dict[str, str | int]],
    referenced_orders: list[int],
) -> bytes:
    api_key, base_url, model, image_size = get_api_config()
    client = create_gemini_client(api_key=api_key, base_url=base_url)
    prompt_text = (
        "请严格基于参考图完成编辑任务，并输出一张图片。"
        f"当前参考编号：{', '.join(str(order) for order in referenced_orders)}。"
        f"目标输出尺寸：{image_size}。"
        f"用户要求：{prompt}"
    )
    content: list[dict[str, object]] = [{"type": "text", "text": prompt_text}]
    for reference in reference_images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": str(reference["data_url"])},
            }
        )
    request_messages: Any = [{"role": "user", "content": content}]
    request_modalities: Any = ["text", "image"]
    response = client.chat.completions.create(
        model=model,
        messages=request_messages,
        modalities=request_modalities,
    )
    return extract_image_bytes(response)


def append_image_result(
    workspace_root: Path,
    *,
    image_id: str,
    image_path: str,
    prompt: str,
    source_editor_image_ids: list[str],
) -> None:
    results_path = workspace_root / "image_results.json"
    if results_path.exists():
        payload = load_json(results_path)
    else:
        payload = {"items": [], "updated_at": now_iso()}
    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []
    items.append(
        {
            "id": image_id,
            "image_path": image_path,
            "alt": "生成结果图",
            "prompt": prompt,
            "source_editor_image_ids": source_editor_image_ids,
            "created_at": now_iso(),
        }
    )
    payload["items"] = items
    payload["updated_at"] = now_iso()
    save_json(results_path, payload)


def generate_into_workspace(workspace_root: Path, prompt: str) -> dict:
    editor_images = load_editor_images(workspace_root)
    selected_images, referenced_orders = resolve_selected_editor_images(editor_images, prompt)
    reference_images = load_reference_images(workspace_root, selected_images)
    image_bytes = generate_image_bytes(prompt, reference_images, referenced_orders)

    generated_images_dir = workspace_root / "generated_images"
    generated_images_dir.mkdir(parents=True, exist_ok=True)
    image_id = f"gen-{uuid4().hex[:12]}"
    filename = f"{image_id}.png"
    output_path = generated_images_dir / filename
    output_path.write_bytes(image_bytes)

    append_image_result(
        workspace_root,
        image_id=image_id,
        image_path=f"generated_images/{filename}",
        prompt=prompt,
        source_editor_image_ids=[str(item.get("id")) for item in selected_images],
    )

    return {
        "success": True,
        "image_id": image_id,
        "image_path": f"generated_images/{filename}",
        "referenced_orders": referenced_orders,
        "source_editor_image_ids": [str(item.get("id")) for item in selected_images],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="基于编辑区参考图生成图片")
    parser.add_argument("--workspace", required=True, help="Workspace 根目录")
    parser.add_argument("--prompt", required=True, help="用户生成提示词")
    args = parser.parse_args()

    workspace_root = Path(args.workspace)
    if not workspace_root.exists():
        print(json.dumps({"error": f"Workspace 目录不存在: {workspace_root}"}, ensure_ascii=False))
        return 1

    try:
        result = generate_into_workspace(workspace_root, args.prompt)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
