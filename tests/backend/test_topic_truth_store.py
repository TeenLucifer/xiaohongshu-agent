from __future__ import annotations

from pathlib import Path

from agent.time_utils import now_local
from backend.topic_truth_models import (
    CandidatePostRecord,
    CandidatePostsDocument,
    CopyDraftRecord,
    ImageCandidateRecord,
    ImageResultsRecord,
    ImageTaskGroupRecord,
    PatternSummaryRecord,
    PostAuthor,
    PostContent,
    PostDetail,
    PostHeat,
    PostMediaAsset,
    PostMetrics,
    PostSource,
    SelectedPostRecord,
    SelectedPostsDocument,
    TopicMeta,
)
from backend.topic_truth_store import SessionWorkspaceStore


def test_initialize_workspace_creates_workspace_root_and_posts_root(tmp_path: Path) -> None:
    store = SessionWorkspaceStore(tmp_path / "data")

    root = store.initialize_workspace("session-demo")

    assert root == tmp_path / "data" / "sessions" / "session-demo" / "workspace"
    assert root.exists()
    assert (root / "posts").exists()


def test_meta_round_trip(tmp_path: Path) -> None:
    store = SessionWorkspaceStore(tmp_path / "data")
    meta = TopicMeta(
        topic_id="topic-demo",
        title="OpenClaw 热门帖子",
        description="测试 topic",
        updated_at=now_local(),
    )

    store.write_meta("session-demo", meta)

    loaded = store.read_meta("session-demo")
    assert loaded == meta


def test_candidate_and_selected_posts_round_trip(tmp_path: Path) -> None:
    store = SessionWorkspaceStore(tmp_path / "data")
    now = now_local()
    candidate = CandidatePostRecord(
        post_id="xhs-1",
        title="CLI 正在回归",
        excerpt="这是一条摘要",
        author="璟礼",
        source_url="https://example.com/post",
        heat=PostHeat(likes=10, favorites=20, comments=3),
        cover_image_path="posts/xhs-1/assets/image-01.jpg",
        selected=False,
        manual_order=None,
        updated_at=now,
    )
    candidate_doc = CandidatePostsDocument(items=[candidate], updated_at=now)
    selected_doc = SelectedPostsDocument(
        items=[SelectedPostRecord(post_id="xhs-1", manual_order=1)],
        updated_at=now,
    )

    store.write_candidate_posts("session-demo", candidate_doc)
    store.write_selected_posts("session-demo", selected_doc)

    assert store.read_candidate_posts("session-demo") == candidate_doc
    assert store.read_selected_posts("session-demo") == selected_doc


def test_pattern_summary_copy_draft_and_image_results_round_trip(tmp_path: Path) -> None:
    store = SessionWorkspaceStore(tmp_path / "data")
    now = now_local()

    summary = PatternSummaryRecord(
        title_patterns=["场景 + 结论"],
        body_patterns=["问题", "拆解", "结尾"],
        keywords=["Agent", "CLI"],
        summary_text="整体偏趋势解读。",
        source_post_ids=["xhs-1"],
        updated_at=now,
    )
    draft = CopyDraftRecord(
        title="Agent 时代，CLI 正在成为新入口",
        body="最近越来越强烈的一个感受是……",
        source_summary_version=now.isoformat(),
        updated_at=now,
    )
    images = ImageResultsRecord(
        groups=[
            ImageTaskGroupRecord(
                id="task-1",
                mode="text-to-image",
                title="文生图",
                summary="封面图候选",
                images=[
                    ImageCandidateRecord(
                        id="cover-1",
                        kind="cover",
                        alt="封面候选图",
                        image_path="generated/cover-1.png",
                    )
                ],
            )
        ],
        updated_at=now,
    )

    store.write_pattern_summary("session-demo", summary)
    store.write_copy_draft("session-demo", draft)
    store.write_image_results("session-demo", images)

    assert store.read_pattern_summary("session-demo") == summary
    assert store.read_copy_draft("session-demo") == draft
    assert store.read_image_results("session-demo") == images


def test_post_detail_raw_and_assets_round_trip(tmp_path: Path) -> None:
    store = SessionWorkspaceStore(tmp_path / "data")
    now = now_local()
    detail = PostDetail(
        post_id="xhs-69c279dc000000001a024c6b",
        title="GUI将死、CLI当立：Agent时代软件入口革命",
        post_type="image_text",
        url="https://www.xiaohongshu.com/explore/69c279dc000000001a024c6b",
        published_at="2026-03-25",
        author=PostAuthor(name="璟礼", author_id=None),
        content=PostContent(
            text="Agent 要干活，最需要的不是美观的界面。",
            hashtags=["AI教程", "Agent", "CLI"],
        ),
        metrics=PostMetrics(likes=332, favorites=493, comments=45),
        media=[
            PostMediaAsset(
                asset_id="image-01",
                kind="image",
                path="assets/image-01.jpg",
                order=1,
            )
        ],
        source=PostSource(
            platform="xiaohongshu",
            source_type="manual_download",
            captured_at=now,
        ),
        updated_at=now,
    )
    raw = {
        "类型": "图文",
        "标题": "GUI将死、CLI当立：Agent时代软件入口革命",
        "点赞数": 332,
    }
    source_asset = tmp_path / "source.jpg"
    source_asset.write_bytes(b"fake-image")

    store.write_post_detail("session-demo", detail.post_id, detail)
    store.write_raw_post("session-demo", detail.post_id, raw)
    relative_asset_path = store.copy_post_asset("session-demo", detail.post_id, source_asset)

    assert store.read_post_detail("session-demo", detail.post_id) == detail
    assert store.read_raw_post("session-demo", detail.post_id) == raw
    assert relative_asset_path == Path("assets") / "source.jpg"
    assert (
        tmp_path
        / "data"
        / "sessions"
        / "session-demo"
        / "workspace"
        / "posts"
        / detail.post_id
        / relative_asset_path
    ).read_bytes() == b"fake-image"


def test_invalid_json_returns_none_without_breaking_other_reads(tmp_path: Path) -> None:
    store = SessionWorkspaceStore(tmp_path / "data")
    workspace_root = store.initialize_workspace("session-demo")
    (workspace_root / "meta.json").write_text("{invalid", encoding="utf-8")
    valid_summary = PatternSummaryRecord(
        title_patterns=["结构"],
        body_patterns=["正文"],
        keywords=["Agent"],
        updated_at=now_local(),
    )
    store.write_pattern_summary("session-demo", valid_summary)

    assert store.read_meta("session-demo") is None
    assert store.read_pattern_summary("session-demo") == valid_summary
