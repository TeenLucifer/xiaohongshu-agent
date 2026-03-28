from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.errors import ProviderCallError, RuntimeInitializationError
from agent.loop_runner import LoopModelResponse
from agent.models import PromptMessage, RunRequest
from agent.provider.config import ProviderConfig
from agent.provider.openai_client import OpenAICompatibleModelClient
from agent.runtime import AgentRuntime
from agent.tools.base import ToolDefinition


def test_provider_config_reads_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=dotenv-key\n"
        "OPENAI_MODEL=dotenv-model\n"
        "OPENAI_BASE_URL=https://dotenv.example/v1\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config = ProviderConfig.load()

    assert config.api_key == "dotenv-key"
    assert config.model == "dotenv-model"
    assert config.base_url == "https://dotenv.example/v1"


def test_provider_config_prefers_environment_over_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=dotenv-key\nOPENAI_MODEL=dotenv-model\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    config = ProviderConfig.load()

    assert config.api_key == "env-key"
    assert config.model == "env-model"


def test_provider_config_missing_required_values_raises_clear_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(RuntimeInitializationError) as exc_info:
        ProviderConfig.load()

    message = str(exc_info.value)
    assert "OPENAI_API_KEY" in message
    assert "OPENAI_MODEL" in message


def test_openai_client_parses_text_response() -> None:
    captured_payload: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            captured_payload.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="done",
                            tool_calls=None,
                        )
                    )
                ]
            )

    sdk_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    client = OpenAICompatibleModelClient(
        config=ProviderConfig.load(
            OPENAI_API_KEY="key",
            OPENAI_MODEL="model",
        ),
        sdk_client=sdk_client,
    )

    response = client.complete(
        messages=[PromptMessage(role="user", content="hello")],
        tool_definitions=[],
    )

    assert response == LoopModelResponse(content="done", tool_calls=[])
    assert captured_payload["model"] == "model"
    assert captured_payload["messages"] == [{"role": "user", "content": "hello"}]


def test_openai_client_parses_tool_calls_response() -> None:
    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="",
                            tool_calls=[
                                SimpleNamespace(
                                    id="call-1",
                                    function=SimpleNamespace(
                                        name="read_file",
                                        arguments='{"path":"notes.md"}',
                                    ),
                                )
                            ],
                        )
                    )
                ]
            )

    sdk_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    client = OpenAICompatibleModelClient(
        config=ProviderConfig.load(
            OPENAI_API_KEY="key",
            OPENAI_MODEL="model",
        ),
        sdk_client=sdk_client,
    )

    response = client.complete(
        messages=[PromptMessage(role="user", content="hello")],
        tool_definitions=[
            ToolDefinition(
                name="read_file",
                description="read file",
                input_schema={"type": "object"},
            )
        ],
    )

    assert response.content == ""
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "read_file"
    assert response.tool_calls[0].arguments == {"path": "notes.md"}


def test_openai_client_rejects_invalid_tool_arguments() -> None:
    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="",
                            tool_calls=[
                                SimpleNamespace(
                                    id="call-1",
                                    function=SimpleNamespace(
                                        name="read_file",
                                        arguments="{bad json}",
                                    ),
                                )
                            ],
                        )
                    )
                ]
            )

    sdk_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    client = OpenAICompatibleModelClient(
        config=ProviderConfig.load(
            OPENAI_API_KEY="key",
            OPENAI_MODEL="model",
        ),
        sdk_client=sdk_client,
    )

    with pytest.raises(ProviderCallError):
        client.complete(
            messages=[PromptMessage(role="user", content="hello")],
            tool_definitions=[],
        )


def test_runtime_builds_default_provider_when_loop_runner_needs_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StubModelClient:
        def complete(
            self,
            *,
            messages: list[PromptMessage],
            tool_definitions: list[ToolDefinition],
        ) -> LoopModelResponse:
            return LoopModelResponse(content="provider ok", tool_calls=[])

    monkeypatch.setattr(
        "agent.runtime.create_default_model_client",
        lambda config=None: StubModelClient(),
    )
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_MODEL", "model")

    runtime = AgentRuntime(project_root=tmp_path)
    snapshot = runtime.create_session(topic="provider")

    result = runtime.run(RunRequest(session_id=snapshot.session_id, user_input="执行"))

    assert result.final_text == "provider ok"


def test_runtime_missing_provider_config_raises_initialization_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    runtime = AgentRuntime(project_root=tmp_path)
    snapshot = runtime.create_session(topic="provider")

    with pytest.raises(RuntimeInitializationError):
        runtime.run(RunRequest(session_id=snapshot.session_id, user_input="执行"))
