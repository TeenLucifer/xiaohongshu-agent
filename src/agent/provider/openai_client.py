"""OpenAI-compatible loop model client."""

from __future__ import annotations

import json
from typing import Any

from agent.errors import ProviderCallError
from agent.loop_runner import LoopModelClient, LoopModelResponse
from agent.models import PromptMessage, ToolCallPayload
from agent.provider.config import ProviderConfig
from agent.tools.base import ToolDefinition


class OpenAICompatibleModelClient(LoopModelClient):
    """Minimal OpenAI-compatible model client for the loop runner."""

    def __init__(
        self,
        *,
        config: ProviderConfig,
        sdk_client: object | None = None,
    ) -> None:
        self.config = config
        self._client: Any = sdk_client or _build_openai_client(config)

    def complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
        tool_choice: object | None = None,
    ) -> LoopModelResponse:
        payload = {
            "model": self.config.model,
            "messages": [_serialize_message(message) for message in messages],
        }
        if tool_definitions:
            payload["tools"] = [_serialize_tool_definition(item) for item in tool_definitions]
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        try:
            response = self._client.chat.completions.create(**payload)
        except Exception as exc:  # noqa: BLE001
            raise ProviderCallError(str(exc)) from exc
        return _parse_response(response)


def create_default_model_client(config: ProviderConfig | None = None) -> LoopModelClient:
    """Create the default OpenAI-compatible model client."""

    return OpenAICompatibleModelClient(config=config or ProviderConfig.load())


def _build_openai_client(config: ProviderConfig) -> object:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - covered by integration path
        raise RuntimeError("缺少 openai 依赖，请先安装项目依赖") from exc

    client_kwargs: dict[str, Any] = {"api_key": config.api_key}
    if config.base_url:
        client_kwargs["base_url"] = config.base_url
    return OpenAI(**client_kwargs)


def _serialize_message(message: PromptMessage) -> dict[str, object]:
    if message.role == "tool":
        payload: dict[str, object] = {
            "role": "tool",
            "content": message.content,
            "tool_call_id": message.tool_call_id,
        }
        if message.name:
            payload["name"] = message.name
        return payload

    payload = {"role": message.role, "content": message.content}
    if message.role == "assistant" and message.tool_calls:
        payload["content"] = message.content or None
        payload["tool_calls"] = [
            {
                "id": item.id,
                "type": "function",
                "function": {
                    "name": item.name,
                    "arguments": json.dumps(item.arguments, ensure_ascii=False),
                },
            }
            for item in message.tool_calls
        ]
    return payload


def _serialize_tool_definition(definition: ToolDefinition) -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": definition.name,
            "description": definition.description,
            "parameters": definition.input_schema,
        },
    }


def _parse_response(response: object) -> LoopModelResponse:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices:
        raise ProviderCallError("模型响应缺少 choices")
    message = getattr(choices[0], "message", None)
    if message is None:
        raise ProviderCallError("模型响应缺少 message")

    content = getattr(message, "content", "") or ""
    raw_tool_calls = getattr(message, "tool_calls", None) or []
    parsed_tool_calls = [_parse_tool_call(item) for item in raw_tool_calls]
    return LoopModelResponse(content=content, tool_calls=parsed_tool_calls)


def _parse_tool_call(raw_tool_call: object) -> ToolCallPayload:
    raw_id = getattr(raw_tool_call, "id", None)
    function = getattr(raw_tool_call, "function", None)
    if function is None:
        raise ProviderCallError("tool call 缺少 function")
    name = getattr(function, "name", None)
    raw_arguments = getattr(function, "arguments", "{}")
    if not isinstance(name, str) or name == "":
        raise ProviderCallError("tool call 缺少 name")
    try:
        parsed_arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ProviderCallError(f"tool call arguments 不是合法 JSON: {exc}") from exc
    if not isinstance(parsed_arguments, dict):
        raise ProviderCallError("tool call arguments 必须是 JSON object")
    return ToolCallPayload(id=raw_id, name=name, arguments=parsed_arguments)
