"""调用视觉 API 分析帖子图片."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 默认配置
DEFAULT_VISION_MODEL = "Qwen/Qwen2.5-VL-32B-Instruct"
MAX_IMAGES_PER_POST = 5


def get_api_config() -> tuple[str, str]:
    """从环境变量获取 API 配置."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

    if not api_key:
        raise ValueError("缺少 OPENAI_API_KEY 环境变量")

    return api_key, base_url


def analyze_images(
    post_id: str,
    workspace_root: Path,
    model: str | None = None,
) -> dict:
    """分析帖子图片并返回结构化结果."""
    assets_dir = workspace_root / "posts" / post_id / "assets"

    if not assets_dir.exists():
        return {"error": "无图片目录", "post_id": post_id}

    images = sorted(assets_dir.glob("image-*.jpg"))
    if not images:
        return {"error": "无图片可分析", "post_id": post_id}

    # 最多分析 MAX_IMAGES_PER_POST 张
    selected_images = images[:MAX_IMAGES_PER_POST]

    # 读取图片 base64
    image_data = []
    for img_path in selected_images:
        try:
            image_data.append({
                "path": str(img_path.relative_to(workspace_root)),
                "base64": base64.b64encode(img_path.read_bytes()).decode("ascii"),
            })
        except Exception as exc:
            return {"error": f"读取图片失败: {exc}", "post_id": post_id}

    # 获取 API 配置
    try:
        api_key, base_url = get_api_config()
    except ValueError as exc:
        return {"error": str(exc), "post_id": post_id}

    # 确定使用的模型
    vision_model = model or os.environ.get("VISION_MODEL", DEFAULT_VISION_MODEL)

    # 调用视觉 API
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)

        content = [
            {"type": "text", "text": _build_analysis_prompt()},
            *[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img['base64']}"}
                }
                for img in image_data
            ]
        ]

        response = client.chat.completions.create(
            model=vision_model,
            messages=[{"role": "user", "content": content}],
            max_tokens=2000,
        )

        analysis_text = response.choices[0].message.content or ""

        return {
            "post_id": post_id,
            "analysis": analysis_text,
            "image_count": len(selected_images),
            "key_observations": _extract_key_observations(analysis_text),
        }

    except ImportError:
        return {"error": "缺少 openai 依赖，请安装: pip install openai", "post_id": post_id}
    except Exception as exc:
        return {"error": f"API 调用失败: {exc}", "post_id": post_id}


def _build_analysis_prompt() -> str:
    """构建分析提示词."""
    return """分析这些小红书帖子的图片，关注以下方面：

1. 构图特征：主体位置、层次感、对称性、视觉引导
2. 色彩特征：色调、饱和度、对比度、整体风格
3. 内容特征：人物、产品、场景、细节
4. 吸引力因素：为什么能吸引点击和互动
5. 问题点：模糊、水印、过度后期等可能影响体验的问题

请给出结构化的分析结果，包括整体评价和关键观察点。"""


def _extract_key_observations(analysis_text: str) -> list[str]:
    """从分析文本中提取关键观察点."""
    lines = analysis_text.split("\n")
    observations = []
    for line in lines:
        line = line.strip()
        # 提取列表项
        if line.startswith("- ") or line.startswith("* "):
            observations.append(line[2:])
        elif line.startswith("• "):
            observations.append(line[2:])
        # 提取数字列表项
        elif len(line) > 2 and line[0].isdigit() and line[1] in ".、)":
            observations.append(line[2:].strip())
    return observations[:5]  # 最多返回 5 个


def main() -> int:
    parser = argparse.ArgumentParser(description="分析帖子图片")
    parser.add_argument("--post-id", required=True, help="帖子 ID")
    parser.add_argument("--workspace", required=True, help="Workspace 根目录")
    parser.add_argument("--model", default=None, help="视觉模型（默认使用 VISION_MODEL 环境变量或 Qwen/Qwen2-VL-7B-Instruct）")
    args = parser.parse_args()

    workspace_path = Path(args.workspace)
    if not workspace_path.exists():
        print(json.dumps({"error": f"Workspace 目录不存在: {args.workspace}", "post_id": args.post_id}, ensure_ascii=False))
        return 1

    result = analyze_images(
        post_id=args.post_id,
        workspace_root=workspace_path,
        model=args.model,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())