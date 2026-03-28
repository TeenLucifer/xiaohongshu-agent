"""Agent loop runner."""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Protocol

from pydantic import BaseModel, Field

from agent.context_builder import ContextBuilder
from agent.errors import ProviderCallError
from agent.memory.store import MemoryStore
from agent.models import PromptMessage, RunRequest, RunResult, ToolCallPayload, ToolCallSummary
from agent.session.models import Session, SessionMessage
from agent.skills.loader import SkillsLoader
from agent.tools.registry import ToolDefinition, ToolsRegistry

MAX_ITERATIONS = 20
MAX_ITERATIONS_FALLBACK_TEXT = "已达到最大工具调用轮数（20），任务仍未完成。建议将任务拆分后重试。"
SUMMARY_MAX_LENGTH = 200


class LoopModelResponse(BaseModel):
    """Structured model response consumed by the loop runner."""

    content: str = ""
    tool_calls: list[ToolCallPayload] = Field(default_factory=list)


class LoopModelClient(Protocol):
    """Model client used by the loop runner."""

    def complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
        tool_choice: object | None = None,
    ) -> LoopModelResponse:
        """Produce the next assistant turn."""
        ...


class MemoryHook(Protocol):
    """Memory consolidation hook used by the loop runner."""

    def run_pre_check(self, session: Session) -> bool:
        """Run one pre-loop consolidation check."""
        ...

    def schedule_post_check(
        self,
        session: Session,
        on_complete: Callable[[bool], None] | None = None,
    ) -> object:
        """Schedule one post-loop consolidation check."""
        ...


class LoopRunner:
    """Loop runner with nanobot-style tool-calling semantics."""

    def __init__(
        self,
        *,
        model_client: LoopModelClient | None = None,
        memory_consolidator: MemoryHook | None = None,
        max_iterations: int = MAX_ITERATIONS,
    ) -> None:
        self.model_client = model_client
        self.memory_consolidator = memory_consolidator
        self.max_iterations = max_iterations

    def run(
        self,
        *,
        session: Session,
        request: RunRequest,
        context_builder: ContextBuilder,
        skills_loader: SkillsLoader,
        tools_registry: ToolsRegistry,
        save_session: Callable[[Session], None],
    ) -> RunResult:
        if self.model_client is None:
            raise ProviderCallError("LoopRunner requires a model client")

        if self.memory_consolidator is not None:
            self.memory_consolidator.run_pre_check(session)

        messages = self._build_messages(
            session=session,
            request=request,
            context_builder=context_builder,
            skills_loader=skills_loader,
        )
        tool_definitions = tools_registry.list_tool_definitions()
        tool_summaries: list[ToolCallSummary] = []

        for _ in range(self.max_iterations):
            response = self._complete(messages=messages, tool_definitions=tool_definitions)
            assistant_prompt = PromptMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            assistant_session = SessionMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            messages.append(assistant_prompt)
            session.add_message(assistant_session)

            if not response.tool_calls:
                save_session(session)
                self._schedule_post_check(session)
                return RunResult(
                    session_id=session.session_id,
                    final_text=response.content,
                    tool_calls=tool_summaries,
                    artifacts=[],
                )

            tool_results = self._execute_tool_calls(
                tool_calls=response.tool_calls,
                tools_registry=tools_registry,
            )
            for tool_call, result_text in tool_results:
                tool_prompt = PromptMessage(
                    role="tool",
                    content=result_text,
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                )
                tool_session = SessionMessage(
                    role="tool",
                    content=result_text,
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                )
                messages.append(tool_prompt)
                session.add_message(tool_session)
                tool_summaries.append(
                    ToolCallSummary(
                        name=tool_call.name,
                        arguments_summary=_summarize_arguments(tool_call.arguments),
                        result_summary=_summarize_result(result_text),
                    )
                )

        fallback_message = SessionMessage(role="assistant", content=MAX_ITERATIONS_FALLBACK_TEXT)
        session.add_message(fallback_message)
        save_session(session)
        self._schedule_post_check(session)
        return RunResult(
            session_id=session.session_id,
            final_text=MAX_ITERATIONS_FALLBACK_TEXT,
            tool_calls=tool_summaries,
            artifacts=[],
        )

    def _build_messages(
        self,
        *,
        session: Session,
        request: RunRequest,
        context_builder: ContextBuilder,
        skills_loader: SkillsLoader,
    ) -> list[PromptMessage]:
        memory_context = MemoryStore(session.workspace_path).get_memory_context()
        system_prompt = context_builder.build_system_prompt(
            memory_context=memory_context,
            always_skills=skills_loader.load_always_skills_for_context(
                workspace_path=session.workspace_path
            ),
            skills_summary=skills_loader.build_skills_summary(
                workspace_path=session.workspace_path
            ),
        )
        return context_builder.build_messages(
            system_prompt=system_prompt,
            session_history=session.get_history(),
            request=request,
            workspace_path=session.workspace_path,
        )

    def _complete(
        self,
        *,
        messages: list[PromptMessage],
        tool_definitions: list[ToolDefinition],
    ) -> LoopModelResponse:
        if self.model_client is None:
            raise ProviderCallError("LoopRunner requires a model client")
        try:
            response = self.model_client.complete(
                messages=messages,
                tool_definitions=tool_definitions,
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderCallError(str(exc)) from exc
        return response

    def _execute_tool_calls(
        self,
        *,
        tool_calls: list[ToolCallPayload],
        tools_registry: ToolsRegistry,
    ) -> list[tuple[ToolCallPayload, str]]:
        def run_one(tool_call: ToolCallPayload) -> str:
            try:
                result = tools_registry.execute_tool(tool_call.name, tool_call.arguments)
            except Exception as exc:  # noqa: BLE001
                return f"Error: {exc.__class__.__name__}: {exc}"
            return _stringify_result(result)

        indexed_results: dict[int, str] = {}
        with ThreadPoolExecutor(max_workers=max(1, len(tool_calls))) as executor:
            future_map = {
                executor.submit(run_one, tool_call): index
                for index, tool_call in enumerate(tool_calls)
            }
            for future in as_completed(future_map):
                indexed_results[future_map[future]] = future.result()

        return [(tool_calls[index], indexed_results[index]) for index in range(len(tool_calls))]

    def _schedule_post_check(self, session: Session) -> None:
        if self.memory_consolidator is None:
            return
        self.memory_consolidator.schedule_post_check(session)


def _stringify_result(result: object) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False)


def _summarize_arguments(arguments: dict[str, Any]) -> str:
    if not arguments:
        return "{}"
    return _truncate_text(json.dumps(arguments, ensure_ascii=False, sort_keys=True))


def _summarize_result(result: str) -> str:
    return _truncate_text(result)


def _truncate_text(value: str, *, max_length: int = SUMMARY_MAX_LENGTH) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."
