"""File-backed workspace store for session-scoped right-panel objects."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from backend.topic_truth_models import (
    CandidatePostsDocument,
    CopyDraftRecord,
    EditorImagesDocument,
    ImageResultsRecord,
    PatternSummaryRecord,
    PostDetail,
    RawPostRecord,
    SelectedPostsDocument,
    TopicMeta,
)

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class SessionWorkspaceStore:
    """Persist and read workspace objects under one session workspace root."""

    def __init__(self, data_root: Path) -> None:
        self._sessions_root = data_root / "sessions"

    def initialize_workspace(self, session_id: str) -> Path:
        root = self.get_workspace_root(session_id)
        self.get_posts_root(session_id).mkdir(parents=True, exist_ok=True)
        (root / "generated_images").mkdir(parents=True, exist_ok=True)
        return root

    def clear_workspace(self, session_id: str) -> None:
        root = self.get_workspace_root(session_id)
        if root.exists():
            shutil.rmtree(root)

    def get_workspace_root(self, session_id: str) -> Path:
        return self._sessions_root / session_id / "workspace"

    def get_posts_root(self, session_id: str) -> Path:
        return self.get_workspace_root(session_id) / "posts"

    def get_generated_images_root(self, session_id: str) -> Path:
        return self.get_workspace_root(session_id) / "generated_images"

    def get_post_root(self, session_id: str, post_id: str) -> Path:
        return self.get_posts_root(session_id) / post_id

    def get_post_assets_root(self, session_id: str, post_id: str) -> Path:
        return self.get_post_root(session_id, post_id) / "assets"

    def list_post_ids(self, session_id: str) -> list[str]:
        posts_root = self.get_posts_root(session_id)
        if not posts_root.exists():
            return []
        return sorted(path.name for path in posts_root.iterdir() if path.is_dir())

    def list_post_details(self, session_id: str) -> list[PostDetail]:
        details: list[PostDetail] = []
        for post_id in self.list_post_ids(session_id):
            detail = self.read_post_detail(session_id, post_id)
            if detail is not None:
                details.append(detail)
        return details

    def read_meta(self, session_id: str) -> TopicMeta | None:
        return self._read_model(self.get_workspace_root(session_id) / "meta.json", TopicMeta)

    def write_meta(self, session_id: str, record: TopicMeta) -> TopicMeta:
        self._write_model(self.get_workspace_root(session_id) / "meta.json", record)
        return record

    def read_candidate_posts(self, session_id: str) -> CandidatePostsDocument | None:
        return self._read_model(
            self.get_workspace_root(session_id) / "candidate_posts.json",
            CandidatePostsDocument,
        )

    def write_candidate_posts(
        self,
        session_id: str,
        document: CandidatePostsDocument,
    ) -> CandidatePostsDocument:
        self._write_model(self.get_workspace_root(session_id) / "candidate_posts.json", document)
        return document

    def read_selected_posts(self, session_id: str) -> SelectedPostsDocument | None:
        return self._read_model(
            self.get_workspace_root(session_id) / "selected_posts.json",
            SelectedPostsDocument,
        )

    def write_selected_posts(
        self,
        session_id: str,
        document: SelectedPostsDocument,
    ) -> SelectedPostsDocument:
        self._write_model(self.get_workspace_root(session_id) / "selected_posts.json", document)
        return document

    def read_pattern_summary(self, session_id: str) -> PatternSummaryRecord | None:
        return self._read_model(
            self.get_workspace_root(session_id) / "pattern_summary.json",
            PatternSummaryRecord,
        )

    def write_pattern_summary(
        self,
        session_id: str,
        record: PatternSummaryRecord,
    ) -> PatternSummaryRecord:
        self._write_model(self.get_workspace_root(session_id) / "pattern_summary.json", record)
        return record

    def read_copy_draft(self, session_id: str) -> CopyDraftRecord | None:
        return self._read_model(
            self.get_workspace_root(session_id) / "copy_draft.json",
            CopyDraftRecord,
        )

    def write_copy_draft(self, session_id: str, record: CopyDraftRecord) -> CopyDraftRecord:
        self._write_model(self.get_workspace_root(session_id) / "copy_draft.json", record)
        return record

    def read_editor_images(self, session_id: str) -> EditorImagesDocument | None:
        return self._read_model(
            self.get_workspace_root(session_id) / "editor_images.json",
            EditorImagesDocument,
        )

    def write_editor_images(
        self,
        session_id: str,
        document: EditorImagesDocument,
    ) -> EditorImagesDocument:
        self._write_model(self.get_workspace_root(session_id) / "editor_images.json", document)
        return document

    def read_image_results(self, session_id: str) -> ImageResultsRecord | None:
        return self._read_model(
            self.get_workspace_root(session_id) / "image_results.json",
            ImageResultsRecord,
        )

    def write_image_results(
        self,
        session_id: str,
        record: ImageResultsRecord,
    ) -> ImageResultsRecord:
        self._write_model(self.get_workspace_root(session_id) / "image_results.json", record)
        return record

    def read_post_detail(self, session_id: str, post_id: str) -> PostDetail | None:
        return self._read_model(self.get_post_root(session_id, post_id) / "post.json", PostDetail)

    def write_post_detail(self, session_id: str, post_id: str, record: PostDetail) -> PostDetail:
        self._write_model(self.get_post_root(session_id, post_id) / "post.json", record)
        return record

    def read_raw_post(self, session_id: str, post_id: str) -> RawPostRecord | None:
        path = self.get_post_root(session_id, post_id) / "raw.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load raw post %s/%s: %s", session_id, post_id, exc)
            return None
        if not isinstance(payload, dict):
            logger.warning("Raw post payload is not an object for %s/%s", session_id, post_id)
            return None
        return payload

    def write_raw_post(
        self,
        session_id: str,
        post_id: str,
        payload: RawPostRecord,
    ) -> RawPostRecord:
        path = self.get_post_root(session_id, post_id) / "raw.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return payload

    def copy_post_asset(
        self,
        session_id: str,
        post_id: str,
        source_path: Path,
        *,
        target_name: str | None = None,
    ) -> Path:
        destination_root = self.get_post_assets_root(session_id, post_id)
        destination_root.mkdir(parents=True, exist_ok=True)
        destination = destination_root / (target_name or source_path.name)
        shutil.copy2(source_path, destination)
        return Path("assets") / destination.name

    def _read_model(self, path: Path, model_type: type[ModelT]) -> ModelT | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return model_type.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load topic truth file %s: %s", path, exc)
            return None

    def _write_model(self, path: Path, record: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


TopicTruthStore = SessionWorkspaceStore
