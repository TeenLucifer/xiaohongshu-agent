"""Persist xiaohongshu research posts into the current session workspace."""

from __future__ import annotations

import importlib.util
import re
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field

from agent.time_utils import now_local
from agent.tools.base import Tool, ToolArguments, ToolExecutionContext
from backend.topic_truth_models import (
    CandidatePostRecord,
    CandidatePostsDocument,
    PostAuthor,
    PostContent,
    PostDetail,
    PostHeat,
    PostMediaAsset,
    PostMetrics,
    PostSource,
    RawPostRecord,
)
from backend.topic_truth_store import SessionWorkspaceStore

_HASHTAG_RE = re.compile(r"#([^\s#]+)")


class PersistAuthorInput(BaseModel):
    name: str | None = None
    author_id: str | None = None


class PersistMetricsInput(BaseModel):
    likes: int | None = None
    favorites: int | None = None
    comments: int | None = None


class PersistPostInput(BaseModel):
    post_id: str | None = None
    title: str | None = None
    url: str | None = None
    published_at: str | None = None
    author: PersistAuthorInput | None = None
    content_text: str | None = None
    metrics: PersistMetricsInput | None = None
    image_urls: list[str] = Field(default_factory=list)
    raw_detail: dict[str, Any] = Field(default_factory=dict)


class PersistXhsPostsArguments(ToolArguments):
    posts: list[PersistPostInput] = Field(min_length=1, max_length=6)


class PersistXhsPostsTool(Tool):
    """Persist structured xhs post payloads into the current session workspace."""

    name = "persist_xhs_posts"
    description = (
        "将已获取到详情的 1 到 6 篇小红书帖子写入当前 session workspace。"
        "只负责建目录、下载图片、写 post.json/raw.json/candidate_posts.json，"
        "不负责搜索或获取详情。传入 get-feed-detail 的结构化结果即可。"
    )
    arguments_model = PersistXhsPostsArguments

    def __init__(
        self,
        *,
        project_root: Path,
        data_root: Path,
        workspace_store: SessionWorkspaceStore | None = None,
        image_download_fn: Callable[[str, Path], str] | None = None,
    ) -> None:
        self._project_root = project_root
        self._workspace_store = workspace_store or SessionWorkspaceStore(data_root)
        self._image_download_fn = image_download_fn or self._download_image_with_skill_script

    def execute(
        self,
        *,
        arguments: ToolArguments,
        context: ToolExecutionContext,
    ) -> object:
        validated = cast(PersistXhsPostsArguments, arguments)
        session_id = _resolve_session_id(context)
        timestamp = now_local()
        self._workspace_store.initialize_workspace(session_id)
        existing_document = self._workspace_store.read_candidate_posts(session_id)
        existing_items = existing_document.items if existing_document is not None else []
        existing_by_id = {item.post_id: item for item in existing_items}

        updated_records: dict[str, CandidatePostRecord] = {}
        input_order: list[str] = []
        written_post_ids: list[str] = []
        failures: list[dict[str, str]] = []

        for payload in validated.posts:
            try:
                post_id = self._resolve_post_id(payload)
                input_order.append(post_id)
                raw_detail = self._resolve_raw_detail(payload)
                media_paths, image_failures = self._persist_images(
                    session_id=session_id,
                    post_id=post_id,
                    image_urls=self._resolve_image_urls(payload, raw_detail),
                )
                if raw_detail is not None:
                    self._workspace_store.write_raw_post(session_id, post_id, raw_detail)
                detail = self._build_post_detail(
                    payload=payload,
                    raw_detail=raw_detail,
                    media_paths=media_paths,
                    captured_at=timestamp,
                )
                self._workspace_store.write_post_detail(session_id, post_id, detail)
                updated_records[post_id] = self._build_candidate_record(
                    payload=payload,
                    detail=detail,
                    media_paths=media_paths,
                    existing=existing_by_id.get(post_id),
                    updated_at=timestamp,
                )
                written_post_ids.append(post_id)
                failures.extend(
                    {
                        "post_id": post_id,
                        "reason": reason,
                    }
                    for reason in image_failures
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    {
                        "post_id": payload.post_id or self._guess_note_id(payload.raw_detail),
                        "reason": str(exc),
                    }
                )

        if updated_records:
            merged_items: list[CandidatePostRecord] = []
            seen: set[str] = set()
            for item in existing_items:
                replacement = updated_records.get(item.post_id)
                if replacement is None:
                    merged_items.append(item)
                    continue
                merged_items.append(replacement)
                seen.add(item.post_id)
            for post_id in input_order:
                replacement = updated_records.get(post_id)
                if replacement is None or post_id in seen:
                    continue
                merged_items.append(replacement)
            self._workspace_store.write_candidate_posts(
                session_id,
                CandidatePostsDocument(items=merged_items, updated_at=timestamp),
            )

        return {
            "session_id": session_id,
            "written_count": len(written_post_ids),
            "written_post_ids": written_post_ids,
            "failed_posts": failures,
        }

    def _persist_images(
        self,
        *,
        session_id: str,
        post_id: str,
        image_urls: list[str],
    ) -> tuple[list[str], list[str]]:
        if not image_urls:
            return [], []

        assets_root = self._workspace_store.get_post_assets_root(session_id, post_id)
        assets_root.mkdir(parents=True, exist_ok=True)
        relative_paths: list[str] = []
        failures: list[str] = []

        for index, image_url in enumerate(image_urls, start=1):
            target_name = f"image-{index:02d}.jpg"
            target_path = assets_root / target_name
            try:
                downloaded_path = Path(self._image_download_fn(image_url, assets_root))
                if downloaded_path.resolve() != target_path.resolve():
                    if target_path.exists():
                        target_path.unlink()
                    downloaded_path.replace(target_path)
                relative_paths.append(f"posts/{post_id}/assets/{target_name}")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"图片 {index} 下载失败: {exc}")

        return relative_paths, failures

    def _build_post_detail(
        self,
        *,
        payload: PersistPostInput,
        raw_detail: RawPostRecord | None,
        media_paths: list[str],
        captured_at: datetime,
    ) -> PostDetail:
        note = _extract_note(raw_detail)
        post_id = self._resolve_post_id(payload)
        title = (payload.title or _safe_str(note.get("title")) or post_id).strip()
        content_text = (
            payload.content_text
            or _safe_str(note.get("desc"))
            or title
        ).strip()
        author = self._resolve_author(payload, note)
        metrics = self._resolve_metrics(payload, note)
        published_at = payload.published_at or _format_published_at(note.get("time"))
        post_type = _safe_str(note.get("type")) or "image_text"
        url = payload.url or f"https://www.xiaohongshu.com/explore/{post_id}"
        media = [
            PostMediaAsset(
                asset_id=f"image-{index:02d}",
                kind="image",
                path=path,
                order=index,
            )
            for index, path in enumerate(media_paths, start=1)
        ]
        return PostDetail(
            post_id=post_id,
            title=title,
            post_type=post_type,
            url=url,
            published_at=published_at,
            author=author,
            content=PostContent(
                text=content_text,
                hashtags=_extract_hashtags(content_text),
            ),
            metrics=metrics,
            media=media,
            source=PostSource(
                platform="xiaohongshu",
                source_type="xhs_research_persist_loop",
                captured_at=captured_at,
            ),
            updated_at=captured_at,
        )

    def _build_candidate_record(
        self,
        *,
        payload: PersistPostInput,
        detail: PostDetail,
        media_paths: list[str],
        existing: CandidatePostRecord | None,
        updated_at: datetime,
    ) -> CandidatePostRecord:
        excerpt = _build_excerpt(detail.content.text)
        return CandidatePostRecord(
            post_id=detail.post_id,
            title=detail.title,
            excerpt=excerpt,
            author=(detail.author.name if detail.author is not None else None),
            source_url=detail.url,
            heat=PostHeat(
                likes=detail.metrics.likes,
                favorites=detail.metrics.favorites,
                comments=detail.metrics.comments,
            ),
            cover_image_path=(
                media_paths[0]
                if media_paths
                else (existing.cover_image_path if existing is not None else None)
            ),
            selected=existing.selected if existing is not None else False,
            manual_order=existing.manual_order if existing is not None else None,
            updated_at=updated_at,
        )

    def _resolve_post_id(self, payload: PersistPostInput) -> str:
        post_id = (payload.post_id or self._guess_note_id(payload.raw_detail)).strip()
        if post_id == "":
            raise ValueError("缺少 post_id，无法落盘帖子")
        return post_id

    def _resolve_raw_detail(self, payload: PersistPostInput) -> RawPostRecord | None:
        if not payload.raw_detail:
            return None
        return payload.raw_detail

    def _resolve_image_urls(
        self,
        payload: PersistPostInput,
        raw_detail: RawPostRecord | None,
    ) -> list[str]:
        if payload.image_urls:
            return [url for url in payload.image_urls if url.strip()]
        note = _extract_note(raw_detail)
        urls: list[str] = []
        for item in note.get("imageList", []) or []:
            if not isinstance(item, dict):
                continue
            url = _safe_str(item.get("urlDefault")) or _safe_str(item.get("urlPre"))
            if url:
                urls.append(url)
        return urls

    def _resolve_author(self, payload: PersistPostInput, note: dict[str, Any]) -> PostAuthor | None:
        note_user = note.get("user", {})
        author_name = None
        author_id = None
        if payload.author is not None:
            author_name = payload.author.name
            author_id = payload.author.author_id
        if author_name is None and isinstance(note_user, dict):
            author_name = _safe_str(note_user.get("nickname"))
        if author_id is None and isinstance(note_user, dict):
            author_id = _safe_str(note_user.get("userId"))
        if author_name is None and author_id is None:
            return None
        return PostAuthor(name=author_name, author_id=author_id)

    def _resolve_metrics(self, payload: PersistPostInput, note: dict[str, Any]) -> PostMetrics:
        note_metrics = note.get("interactInfo", {})
        likes = payload.metrics.likes if payload.metrics is not None else None
        favorites = payload.metrics.favorites if payload.metrics is not None else None
        comments = payload.metrics.comments if payload.metrics is not None else None
        if isinstance(note_metrics, dict):
            if likes is None:
                likes = _to_int(note_metrics.get("likedCount"))
            if favorites is None:
                favorites = _to_int(note_metrics.get("collectedCount"))
            if comments is None:
                comments = _to_int(note_metrics.get("commentCount"))
        return PostMetrics(likes=likes, favorites=favorites, comments=comments)

    def _guess_note_id(self, raw_detail: RawPostRecord) -> str:
        note = _extract_note(raw_detail)
        return _safe_str(note.get("noteId"))

    def _download_image_with_skill_script(self, image_url: str, save_dir: Path) -> str:
        downloader_class = _load_skill_image_downloader(
            self._project_root / "skills" / "xiaohongshu-skills" / "scripts" / "image_downloader.py"
        )
        downloader = downloader_class(str(save_dir))
        return str(downloader.download_image(image_url))


def _resolve_session_id(context: ToolExecutionContext) -> str:
    if context.allowed_dir is None:
        raise ValueError("persist_xhs_posts 缺少 session 上下文")
    session_id = context.allowed_dir.name.strip()
    if session_id == "":
        raise ValueError("无法从工具上下文解析 session_id")
    return session_id


def _extract_note(raw_detail: RawPostRecord | None) -> dict[str, Any]:
    if raw_detail is None:
        return {}
    note = raw_detail.get("note", {})
    if isinstance(note, dict):
        return note
    return {}


def _safe_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _format_published_at(value: Any) -> str | None:
    if value in (None, ""):
        return None
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


def _build_excerpt(content_text: str, *, max_length: int = 96) -> str:
    normalized = " ".join(content_text.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1] + "…"


@lru_cache(maxsize=1)
def _load_skill_image_downloader(script_path: Path) -> type[Any]:
    spec = importlib.util.spec_from_file_location("xhs_image_downloader", script_path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"无法加载图片下载器脚本: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    downloader_class = getattr(module, "ImageDownloader", None)
    if downloader_class is None:
        raise RuntimeError("图片下载器脚本中缺少 ImageDownloader")
    return downloader_class
