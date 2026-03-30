"""将小红书帖子详情下载为标准帖子包。"""

from __future__ import annotations

import base64
import json
import re
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

_HASHTAG_RE = re.compile(r"#([^\s#]+)")


class PageLike(Protocol):
    def navigate(self, url: str) -> None: ...

    def wait_for_load(self, timeout: float = 60.0) -> None: ...

    def evaluate(self, expression: str, timeout: float = 30.0) -> Any: ...

    def _send_session(self, method: str, params: dict | None = None) -> dict: ...


def ingest_posts_into_posts_dir(
    *,
    posts_dir: Path,
    posts: list[dict[str, Any]],
    page: PageLike,
    save_image_fn: Callable[[PageLike, str, Path], None] | None = None,
) -> dict[str, Any]:
    timestamp = _now_iso()
    posts_dir.mkdir(parents=True, exist_ok=True)
    written_post_ids: list[str] = []
    failures: list[dict[str, str]] = []
    skipped_video_post_ids: list[str] = []

    image_saver = save_image_fn or _save_image_via_browser

    for payload in posts:
        try:
            post_id = _resolve_post_id(payload)
            raw_detail = _resolve_raw_detail(payload)
            if _is_video_post(payload, raw_detail):
                skipped_video_post_ids.append(post_id)
                continue
            media_paths, image_failures = _persist_images(
                posts_dir=posts_dir,
                post_id=post_id,
                image_urls=_resolve_image_urls(payload, raw_detail),
                page=page,
                save_image_fn=image_saver,
            )
            post_root = posts_dir / post_id
            if raw_detail is not None:
                _write_json(post_root / "raw.json", raw_detail)
            detail = _build_post_detail(
                payload=payload,
                raw_detail=raw_detail,
                media_paths=media_paths,
                captured_at=timestamp,
            )
            _write_json(post_root / "post.json", detail)
            written_post_ids.append(post_id)
            failures.extend({"post_id": post_id, "reason": reason} for reason in image_failures)
        except Exception as exc:  # noqa: BLE001
            failed_post_id = (
                _safe_str(payload.get("post_id"))
                or _guess_note_id(payload.get("raw_detail"))
            )
            failures.append(
                {
                    "post_id": failed_post_id,
                    "reason": str(exc),
                }
            )

    return {
        "written_count": len(written_post_ids),
        "written_post_ids": written_post_ids,
        "failed_posts": failures,
        "skipped_video_post_ids": skipped_video_post_ids,
    }


def load_posts_payload(input_json_path: Path) -> list[dict[str, Any]]:
    payload = _read_json(input_json_path)
    if not isinstance(payload, dict):
        raise ValueError("ingest-posts 输入必须是 JSON 对象")
    posts = payload.get("posts")
    if not isinstance(posts, list) or len(posts) == 0:
        raise ValueError("ingest-posts 输入缺少 posts[]")
    normalized_posts = [item for item in posts if isinstance(item, dict)]
    if not normalized_posts:
        raise ValueError("ingest-posts 输入 posts[] 为空")
    return normalized_posts


def ensure_repo_src_on_path() -> None:
    repo_src = Path(__file__).resolve().parents[4] / "src"
    if repo_src.exists():
        repo_src_str = str(repo_src)
        if repo_src_str not in sys.path:
            sys.path.insert(0, repo_src_str)


def _persist_images(
    *,
    posts_dir: Path,
    post_id: str,
    image_urls: list[str],
    page: PageLike,
    save_image_fn: Callable[[PageLike, str, Path], None],
) -> tuple[list[str], list[str]]:
    if not image_urls:
        return [], []
    assets_root = posts_dir / post_id / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    relative_paths: list[str] = []
    failures: list[str] = []
    for index, image_url in enumerate(image_urls, start=1):
        target_name = f"image-{index:02d}.jpg"
        target_path = assets_root / target_name
        try:
            save_image_fn(page, image_url, target_path)
            relative_paths.append(f"posts/{post_id}/assets/{target_name}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"图片 {index} 下载失败: {exc}")
    return relative_paths, failures


def _save_image_via_browser(page: PageLike, image_url: str, output_path: Path) -> None:
    page.navigate(image_url)
    page.wait_for_load(timeout=30.0)
    _wait_for_image_ready(page)
    doc = page._send_session("DOM.getDocument", {"depth": 0})
    root_id = doc["root"]["nodeId"]
    query = page._send_session("DOM.querySelector", {"nodeId": root_id, "selector": "img"})
    node_id = query.get("nodeId", 0)
    if not node_id:
        raise RuntimeError("图片页未找到 img 元素")
    box_model = page._send_session("DOM.getBoxModel", {"nodeId": node_id})
    model = box_model["model"]
    content = model["content"]
    x, y = content[0], content[1]
    width, height = float(model["width"]), float(model["height"])
    result = page._send_session(
        "Page.captureScreenshot",
        {
            "format": "jpeg",
            "quality": 100,
            "clip": {
                "x": max(0.0, x),
                "y": max(0.0, y),
                "width": width,
                "height": height,
                "scale": 1.0,
            },
        },
    )
    data = result.get("data", "")
    if not data:
        raise RuntimeError("浏览器截图结果为空")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(data))


def _wait_for_image_ready(page: PageLike, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready = page.evaluate(
            """
            (() => {
              const img = document.images && document.images[0];
              return !!(img && img.complete && img.naturalWidth > 0 && img.naturalHeight > 0);
            })()
            """
        )
        if ready:
            return
        time.sleep(0.2)
    raise RuntimeError("图片页加载超时")


def _build_post_detail(
    *,
    payload: dict[str, Any],
    raw_detail: dict[str, Any] | None,
    media_paths: list[str],
    captured_at: str,
) -> dict[str, Any]:
    note = _extract_note(raw_detail)
    post_id = _resolve_post_id(payload)
    title = (_safe_str(payload.get("title")) or _safe_str(note.get("title")) or post_id).strip()
    content_text = (
        _safe_str(payload.get("content_text")) or _safe_str(note.get("desc")) or title
    ).strip()
    author = _resolve_author(payload, note)
    metrics = _resolve_metrics(payload, note)
    published_at = _safe_str(payload.get("published_at")) or _format_published_at(note.get("time"))
    post_type = _safe_str(note.get("type")) or "image_text"
    url = _safe_str(payload.get("url")) or f"https://www.xiaohongshu.com/explore/{post_id}"
    media = [
        {
            "asset_id": f"image-{index:02d}",
            "kind": "image",
            "path": path,
            "order": index,
        }
        for index, path in enumerate(media_paths, start=1)
    ]
    return {
        "post_id": post_id,
        "title": title,
        "post_type": post_type,
        "url": url,
        "published_at": published_at or None,
        "author": author,
        "content": {
            "text": content_text,
            "hashtags": _extract_hashtags(content_text),
        },
        "metrics": metrics,
        "media": media,
        "source": {
            "platform": "xiaohongshu",
            "source_type": "xhs_research_ingest_skill",
            "captured_at": captured_at,
        },
        "updated_at": captured_at,
    }


def _resolve_post_id(payload: dict[str, Any]) -> str:
    post_id = (
        _safe_str(payload.get("post_id")) or _guess_note_id(payload.get("raw_detail"))
    ).strip()
    if post_id == "":
        raise ValueError("缺少 post_id，无法落盘帖子")
    return post_id


def _resolve_raw_detail(payload: dict[str, Any]) -> dict[str, Any] | None:
    raw_detail = payload.get("raw_detail")
    return raw_detail if isinstance(raw_detail, dict) and raw_detail else None


def _resolve_image_urls(payload: dict[str, Any], raw_detail: dict[str, Any] | None) -> list[str]:
    payload_urls = payload.get("image_urls")
    if isinstance(payload_urls, list):
        urls = [_safe_str(url).strip() for url in payload_urls if _safe_str(url).strip()]
        if urls:
            return urls
    note = _extract_note(raw_detail)
    urls: list[str] = []
    for item in note.get("imageList", []) or []:
        if not isinstance(item, dict):
            continue
        url = _safe_str(item.get("urlDefault")) or _safe_str(item.get("urlPre"))
        if url:
            urls.append(url)
    return urls


def _resolve_author(payload: dict[str, Any], note: dict[str, Any]) -> dict[str, Any] | None:
    author_payload = payload.get("author")
    note_user = note.get("user", {})
    name = None
    author_id = None
    if isinstance(author_payload, dict):
        name = _safe_str(author_payload.get("name")) or None
        author_id = _safe_str(author_payload.get("author_id")) or None
    if name is None and isinstance(note_user, dict):
        name = _safe_str(note_user.get("nickname")) or None
    if author_id is None and isinstance(note_user, dict):
        author_id = _safe_str(note_user.get("userId")) or None
    if name is None and author_id is None:
        return None
    return {"name": name, "author_id": author_id}


def _resolve_metrics(payload: dict[str, Any], note: dict[str, Any]) -> dict[str, Any]:
    payload_metrics = payload.get("metrics", {})
    note_metrics = note.get("interactInfo", {})
    likes = _to_int(payload_metrics.get("likes")) if isinstance(payload_metrics, dict) else None
    favorites = (
        _to_int(payload_metrics.get("favorites")) if isinstance(payload_metrics, dict) else None
    )
    comments = (
        _to_int(payload_metrics.get("comments")) if isinstance(payload_metrics, dict) else None
    )
    if isinstance(note_metrics, dict):
        if likes is None:
            likes = _to_int(note_metrics.get("likedCount"))
        if favorites is None:
            favorites = _to_int(note_metrics.get("collectedCount"))
        if comments is None:
            comments = _to_int(note_metrics.get("commentCount"))
    return {
        "likes": likes,
        "favorites": favorites,
        "comments": comments,
    }


def _is_video_post(payload: dict[str, Any], raw_detail: dict[str, Any] | None) -> bool:
    if _safe_str(payload.get("post_type")) == "video":
        return True
    note = _extract_note(raw_detail)
    return _safe_str(note.get("type")) == "video"


def _extract_note(raw_detail: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(raw_detail, dict):
        return {}
    note = raw_detail.get("note", {})
    return note if isinstance(note, dict) else {}


def _guess_note_id(raw_detail: Any) -> str:
    note = _extract_note(raw_detail if isinstance(raw_detail, dict) else None)
    return _safe_str(note.get("noteId"))


def _safe_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        if normalized == "":
            return None
        if normalized.isdigit():
            return int(normalized)
        if normalized.endswith("万"):
            try:
                return int(float(normalized[:-1]) * 10_000)
            except ValueError:
                return None
    return None


def _format_published_at(value: Any) -> str | None:
    timestamp = _to_int(value)
    if timestamp is None:
        return None
    if timestamp > 10_000_000_000:
        timestamp = int(timestamp / 1000)
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def _extract_hashtags(content_text: str) -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []
    for match in _HASHTAG_RE.finditer(content_text):
        tag = match.group(1).strip()
        if tag == "" or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()
