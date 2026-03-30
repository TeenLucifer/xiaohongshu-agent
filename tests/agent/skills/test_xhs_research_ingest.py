from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_SCRIPTS_ROOT = REPO_ROOT / "skills" / "xiaohongshu-skills" / "scripts"
RESEARCH_INGEST_PATH = SKILL_SCRIPTS_ROOT / "xhs" / "research_ingest.py"

spec = importlib.util.spec_from_file_location("xhs_research_ingest", RESEARCH_INGEST_PATH)
assert spec is not None
assert spec.loader is not None
research_ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research_ingest)
ingest_posts_into_posts_dir = research_ingest.ingest_posts_into_posts_dir
load_posts_payload = research_ingest.load_posts_payload


class FakePage:
    def navigate(self, url: str) -> None:
        self.last_url = url

    def wait_for_load(self, timeout: float = 60.0) -> None:
        self.last_timeout = timeout

    def evaluate(self, expression: str, timeout: float = 30.0):  # noqa: ANN201
        return None

    def _send_session(self, method: str, params: dict | None = None) -> dict:  # noqa: ARG002
        return {}


def _fake_save_image(_page: FakePage, image_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(f"saved:{image_url}".encode())


def test_load_posts_payload_requires_posts_array(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"posts": [{"post_id": "note-1"}]}), encoding="utf-8")

    posts = load_posts_payload(payload_path)

    assert len(posts) == 1
    assert posts[0]["post_id"] == "note-1"


def test_ingest_posts_into_posts_dir_writes_post_and_assets(tmp_path: Path) -> None:
    posts_dir = tmp_path / "workspace" / "posts"
    page = FakePage()

    result = ingest_posts_into_posts_dir(
        posts_dir=posts_dir,
        posts=[
            {
                "post_id": "note-1",
                "title": "通勤穿搭",
                "url": "https://www.xiaohongshu.com/explore/note-1",
                "content_text": "适合通勤的春季穿搭 #通勤 #春季",
                "metrics": {"likes": 12, "favorites": 8, "comments": 2},
                "image_urls": [
                    "https://example.com/1.jpg",
                    "https://example.com/2.jpg",
                ],
                "raw_detail": {
                    "note": {
                        "noteId": "note-1",
                        "type": "normal",
                        "user": {"nickname": "搭配君", "userId": "user-1"},
                    }
                },
            }
        ],
        page=page,
        save_image_fn=_fake_save_image,
    )

    assert result["written_count"] == 1
    assert result["written_post_ids"] == ["note-1"]
    assert result["failed_posts"] == []
    assert result["skipped_video_post_ids"] == []

    detail = json.loads(
        (posts_dir / "note-1" / "post.json").read_text(encoding="utf-8")
    )
    assert detail["media"][0]["path"] == "posts/note-1/assets/image-01.jpg"
    assert detail["media"][1]["path"] == "posts/note-1/assets/image-02.jpg"

    raw = json.loads((posts_dir / "note-1" / "raw.json").read_text(encoding="utf-8"))
    assert raw["note"]["noteId"] == "note-1"

    assert (posts_dir / "note-1" / "assets" / "image-01.jpg").exists()
    assert (posts_dir / "note-1" / "assets" / "image-02.jpg").exists()


def test_ingest_posts_into_posts_dir_skips_video_posts(tmp_path: Path) -> None:
    posts_dir = tmp_path / "workspace" / "posts"
    page = FakePage()

    result = ingest_posts_into_posts_dir(
        posts_dir=posts_dir,
        posts=[
            {
                "post_id": "video-1",
                "title": "视频帖子",
                "raw_detail": {
                    "note": {
                        "noteId": "video-1",
                        "type": "video",
                    }
                },
            }
        ],
        page=page,
        save_image_fn=_fake_save_image,
    )

    assert result["written_count"] == 0
    assert result["written_post_ids"] == []
    assert result["skipped_video_post_ids"] == ["video-1"]
    assert not (posts_dir / "video-1").exists()


def test_ingest_posts_into_posts_dir_does_not_write_candidate_posts(tmp_path: Path) -> None:
    posts_dir = tmp_path / "workspace" / "posts"

    ingest_posts_into_posts_dir(
        posts_dir=posts_dir,
        posts=[
            {
                "post_id": "note-2",
                "title": "新标题",
                "content_text": "新的正文",
                "image_urls": ["https://example.com/cover.jpg"],
            }
        ],
        page=FakePage(),
        save_image_fn=_fake_save_image,
    )

    assert not (tmp_path / "workspace" / "candidate_posts.json").exists()
    detail = json.loads((posts_dir / "note-2" / "post.json").read_text(encoding="utf-8"))
    assert detail["title"] == "新标题"
