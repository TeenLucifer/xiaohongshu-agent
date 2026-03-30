from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from agent.time_utils import now_local
from agent.tools.base import ToolExecutionContext
from agent.tools.xhs_persist import PersistXhsPostsTool
from backend.topic_truth_models import CandidatePostRecord, CandidatePostsDocument, PostHeat
from backend.topic_truth_store import SessionWorkspaceStore


def make_tool(tmp_path: Path) -> tuple[PersistXhsPostsTool, SessionWorkspaceStore]:
    data_root = tmp_path / "data"
    store = SessionWorkspaceStore(data_root)

    def fake_download(image_url: str, save_dir: Path) -> str:
        filename = image_url.rsplit("/", 1)[-1] or "downloaded.jpg"
        target = save_dir / filename
        target.write_bytes(f"downloaded:{image_url}".encode())
        return str(target)

    tool = PersistXhsPostsTool(
        project_root=tmp_path,
        data_root=data_root,
        workspace_store=store,
        image_download_fn=fake_download,
    )
    return tool, store


def make_context(tmp_path: Path, session_id: str = "sess-1") -> ToolExecutionContext:
    workspace_root = tmp_path / "data" / "sessions" / session_id
    workspace_root.mkdir(parents=True, exist_ok=True)
    return ToolExecutionContext(allowed_dir=workspace_root)


def test_persist_xhs_posts_writes_workspace_files(tmp_path: Path) -> None:
    tool, store = make_tool(tmp_path)
    context = make_context(tmp_path)

    result = tool.run(
        {
            "posts": [
                {
                    "post_id": "note-1",
                    "title": "通勤穿搭参考",
                    "url": "https://www.xiaohongshu.com/explore/note-1",
                    "content_text": "适合上班族的春季通勤穿搭 #通勤穿搭 #春季穿搭",
                    "metrics": {"likes": 12, "favorites": 18, "comments": 3},
                    "image_urls": [
                        "https://example.com/cover.jpg",
                        "https://example.com/detail.jpg",
                    ],
                    "raw_detail": {
                        "note": {
                            "noteId": "note-1",
                            "title": "通勤穿搭参考",
                            "desc": "适合上班族的春季通勤穿搭 #通勤穿搭 #春季穿搭",
                            "type": "normal",
                            "time": 1_711_777_600_000,
                            "user": {"userId": "user-1", "nickname": "搭配君"},
                            "interactInfo": {
                                "likedCount": 12,
                                "collectedCount": 18,
                                "commentCount": 3,
                            },
                        },
                        "comments": [],
                    },
                }
            ]
        },
        context,
    )

    payload = cast(dict[str, Any], result)
    assert payload["written_count"] == 1
    assert payload["written_post_ids"] == ["note-1"]

    detail = store.read_post_detail("sess-1", "note-1")
    assert detail is not None
    assert detail.title == "通勤穿搭参考"
    assert detail.media[0].path == "posts/note-1/assets/image-01.jpg"
    assert detail.media[1].path == "posts/note-1/assets/image-02.jpg"
    assert detail.content.hashtags == ["通勤穿搭", "春季穿搭"]

    raw = store.read_raw_post("sess-1", "note-1")
    assert raw is not None
    assert raw["note"]["noteId"] == "note-1"

    candidate = store.read_candidate_posts("sess-1")
    assert candidate is not None
    assert candidate.items[0].cover_image_path == "posts/note-1/assets/image-01.jpg"

    asset_1 = store.get_workspace_root("sess-1") / "posts" / "note-1" / "assets" / "image-01.jpg"
    asset_2 = store.get_workspace_root("sess-1") / "posts" / "note-1" / "assets" / "image-02.jpg"
    assert asset_1.exists()
    assert asset_2.exists()


def test_persist_xhs_posts_preserves_existing_selection_fields(tmp_path: Path) -> None:
    tool, store = make_tool(tmp_path)
    context = make_context(tmp_path)
    store.write_candidate_posts(
        "sess-1",
        CandidatePostsDocument(
            items=[
                CandidatePostRecord(
                    post_id="note-1",
                    title="旧标题",
                    excerpt="旧摘要",
                    author="旧作者",
                    source_url="https://example.com/old",
                    heat=PostHeat(likes=1, favorites=2, comments=3),
                    cover_image_path=None,
                    selected=True,
                    manual_order=2,
                    updated_at=now_local(),
                )
            ],
            updated_at=now_local(),
        ),
    )

    tool.run(
        {
            "posts": [
                {
                    "post_id": "note-1",
                    "title": "新标题",
                    "content_text": "新的正文",
                    "raw_detail": {
                        "note": {
                            "noteId": "note-1",
                            "title": "新标题",
                            "desc": "新的正文",
                        }
                    },
                }
            ]
        },
        context,
    )

    candidate = store.read_candidate_posts("sess-1")
    assert candidate is not None
    assert candidate.items[0].title == "新标题"
    assert candidate.items[0].selected is True
    assert candidate.items[0].manual_order == 2


def test_persist_xhs_posts_writes_without_raw_detail(tmp_path: Path) -> None:
    tool, store = make_tool(tmp_path)
    context = make_context(tmp_path)

    result = tool.run(
        {
            "posts": [
                {
                    "post_id": "note-2",
                    "title": "热门帖子",
                    "url": "https://www.xiaohongshu.com/explore/note-2",
                    "published_at": "2026-03-30",
                    "author": {"name": "测试作者", "author_id": "author-2"},
                    "content_text": "这是帖子正文 #热门 #测试",
                    "metrics": {"likes": 100, "favorites": 50, "comments": 10},
                    "image_urls": ["https://example.com/cover.jpg"],
                }
            ]
        },
        context,
    )

    payload = cast(dict[str, Any], result)
    assert payload["written_count"] == 1
    assert payload["written_post_ids"] == ["note-2"]
    assert payload["failed_posts"] == []

    detail = store.read_post_detail("sess-1", "note-2")
    assert detail is not None
    assert detail.title == "热门帖子"
    assert detail.content.text == "这是帖子正文 #热门 #测试"
    assert detail.metrics.likes == 100
    assert detail.media[0].path == "posts/note-2/assets/image-01.jpg"

    raw = store.read_raw_post("sess-1", "note-2")
    assert raw is None

    candidate = store.read_candidate_posts("sess-1")
    assert candidate is not None
    assert candidate.items[0].post_id == "note-2"
    assert candidate.items[0].cover_image_path == "posts/note-2/assets/image-01.jpg"

    asset = store.get_workspace_root("sess-1") / "posts" / "note-2" / "assets" / "image-01.jpg"
    assert asset.exists()
