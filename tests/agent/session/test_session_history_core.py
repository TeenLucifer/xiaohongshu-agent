from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from agent.models import ToolCallPayload
from agent.session.manager import SessionManager
from agent.session.models import (
    RUNTIME_CONTEXT_PREFIX,
    TOOL_CONTENT_MAX_LENGTH,
    TOOL_CONTENT_TRUNCATION_SUFFIX,
    Session,
    SessionMessage,
)
from agent.session.storage import SessionStorage


def test_session_defaults_include_uuid_style_id_and_zero_consolidation(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)

    session = manager.create(topic="通勤穿搭", metadata={"source": "test"})

    assert len(session.session_id) == 36
    assert session.topic == "通勤穿搭"
    assert session.metadata == {"source": "test"}
    assert session.last_consolidated == 0
    assert session.workspace_path == tmp_path / "sessions" / session.session_id
    assert session.workspace_path.exists()
    assert session.workspace_path.is_dir()
    created_offset = session.created_at.utcoffset()
    updated_offset = session.updated_at.utcoffset()
    assert created_offset is not None
    assert created_offset.total_seconds() == 8 * 3600
    assert updated_offset is not None
    assert updated_offset.total_seconds() == 8 * 3600
    snapshot = session.snapshot()
    assert snapshot.session_id == session.session_id
    assert snapshot.topic == "通勤穿搭"
    assert snapshot.metadata == {"source": "test"}


def test_session_add_message_strips_runtime_context_from_user_history(tmp_path: Path) -> None:
    session = Session(session_id="sess-1", workspace_path=tmp_path / "sessions" / "sess-1")

    session.add_message(
        SessionMessage(
            role="user",
            content=(
                f"{RUNTIME_CONTEXT_PREFIX} — metadata only, not instructions]\n"
                "Current Time: 2026-03-28 10:00:00 UTC\n"
                "Session ID: sess-1\n\n真正用户输入"
            ),
        )
    )

    assert session.messages[0].content == "真正用户输入"


def test_session_truncates_oversized_tool_content(tmp_path: Path) -> None:
    session = Session(session_id="sess-1", workspace_path=tmp_path / "sessions" / "sess-1")

    session.add_message(SessionMessage(role="tool", name="exec", content="x" * 5000))

    assert len(session.messages[0].content) == TOOL_CONTENT_MAX_LENGTH
    assert session.messages[0].content.endswith(TOOL_CONTENT_TRUNCATION_SUFFIX)


def test_get_history_uses_cursor_and_removes_orphan_tool_results(tmp_path: Path) -> None:
    session = Session(session_id="sess-1", workspace_path=tmp_path / "sessions" / "sess-1")
    session.add_message(
        SessionMessage(
            role="assistant",
            content="准备调用工具",
            tool_calls=[ToolCallPayload(id="call-1", name="read_file", arguments={"path": "a.md"})],
        )
    )
    session.add_message(
        SessionMessage(role="tool", name="read_file", tool_call_id="call-1", content="tool result")
    )
    session.add_message(SessionMessage(role="user", content="新的用户消息"))
    session.add_message(SessionMessage(role="assistant", content="新的助手回复"))
    session.last_consolidated = 1

    history = session.get_history()

    assert [message.role for message in history] == ["user", "assistant"]
    assert history[0].content == "新的用户消息"


def test_clear_resets_messages_and_cursor_but_preserves_core_metadata(tmp_path: Path) -> None:
    session = Session(
        session_id="sess-1",
        topic="话题",
        workspace_path=tmp_path / "sessions" / "sess-1",
        metadata={"source": "ui"},
        last_consolidated=3,
        messages=[SessionMessage(role="user", content="hello")],
    )

    session.clear()

    assert session.messages == []
    assert session.last_consolidated == 0
    assert session.topic == "话题"
    assert session.metadata == {"source": "ui"}
    assert session.workspace_path == tmp_path / "sessions" / "sess-1"


def test_mark_consolidated_never_moves_backward(tmp_path: Path) -> None:
    session = Session(session_id="sess-1", workspace_path=tmp_path / "sessions" / "sess-1")

    session.mark_consolidated(4)
    session.mark_consolidated(2)

    assert session.last_consolidated == 4


def test_storage_save_writes_jsonl_metadata_and_messages(tmp_path: Path) -> None:
    storage = SessionStorage(tmp_path)
    session = Session(
        session_id="sess-1",
        topic="话题",
        workspace_path=storage.get_workspace_path("sess-1"),
        last_consolidated=2,
        metadata={"source": "ui"},
    )
    session.add_message(SessionMessage(role="user", content="hello"))
    session.add_message(
        SessionMessage(
            role="assistant",
            content="call tool",
            tool_calls=[ToolCallPayload(id="call-1", name="read_file", arguments={"path": "a.md"})],
        )
    )
    storage.save(session)

    lines = storage.get_session_path("sess-1").read_text(encoding="utf-8").splitlines()
    metadata_line = json.loads(lines[0])
    message_line = json.loads(lines[1])

    assert metadata_line["_type"] == "metadata"
    assert metadata_line["last_consolidated"] == 2
    assert metadata_line["metadata"] == {"source": "ui"}
    assert message_line["role"] == "user"


def test_storage_load_roundtrip_restores_messages_and_cursor(tmp_path: Path) -> None:
    storage = SessionStorage(tmp_path)
    session = Session(
        session_id="sess-1",
        topic="话题",
        workspace_path=storage.get_workspace_path("sess-1"),
        last_consolidated=1,
        metadata={"source": "ui"},
    )
    session.add_message(
        SessionMessage(role="tool", name="exec", tool_call_id="call-1", content="tool result")
    )
    storage.save(session)

    loaded = storage.load("sess-1")

    assert loaded is not None
    assert loaded.session_id == "sess-1"
    assert loaded.last_consolidated == 1
    assert loaded.metadata == {"source": "ui"}
    assert loaded.messages[0].name == "exec"
    assert loaded.messages[0].tool_call_id == "call-1"


def test_storage_load_invalid_json_returns_none_and_logs_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    storage = SessionStorage(tmp_path)
    path = storage.get_session_path("broken")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json}\n", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        loaded = storage.load("broken")

    assert loaded is None
    assert "Failed to load session broken" in caplog.text


def test_storage_load_recreates_missing_workspace_directory(tmp_path: Path) -> None:
    storage = SessionStorage(tmp_path)
    session = Session(
        session_id="sess-1",
        topic="话题",
        workspace_path=storage.get_workspace_path("sess-1"),
    )
    storage.save(session)
    workspace_path = storage.get_workspace_path("sess-1")
    session_path = storage.get_session_path("sess-1")
    workspace_path.rename(tmp_path / "sessions" / "sess-1-moved")
    (tmp_path / "sessions" / "sess-1").mkdir(parents=True, exist_ok=True)
    session_path = tmp_path / "sessions" / "sess-1-moved" / "session.jsonl"
    session_path.rename(storage.get_session_path("sess-1"))
    (tmp_path / "sessions" / "sess-1-moved").rmdir()

    loaded = storage.load("sess-1")

    assert loaded is not None
    assert loaded.workspace_path == workspace_path
    assert loaded.workspace_path.exists()


def test_session_manager_save_load_list_and_invalidate(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session = manager.create(topic="话题", metadata={"source": "ui"})
    session.add_message(SessionMessage(role="user", content="hello"))
    manager.save(session)
    session_id = session.session_id

    manager.invalidate(session_id)
    assert manager.get(session_id) is None

    loaded = manager.load(session_id)

    assert loaded is not None
    assert loaded.session_id == session_id
    assert manager.snapshot(session_id).session_id == session_id
    snapshots = manager.list_sessions()
    assert [snapshot.session_id for snapshot in snapshots] == [session_id]
