"""Thin runtime host for agent foundation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from agent.context_builder import ContextBuilder
from agent.errors import RuntimeInitializationError
from agent.loop_runner import LoopModelClient, LoopRunner
from agent.memory import DefaultMemoryConsolidationAgent, RuntimeMemoryConsolidator
from agent.models import RunRequest, RunResult
from agent.provider import ProviderConfig, create_default_model_client
from agent.session.manager import SessionManager
from agent.session.models import SessionSnapshot
from agent.skills.loader import SkillsLoader
from agent.tools.registry import ToolsRegistry
from agent.trace import TraceSink


class AgentRuntime:
    """Thin runtime host that coordinates core runtime components."""

    _DEFAULT_CONTEXT_WINDOW_TOKENS = 65_536
    _DEFAULT_MAX_COMPLETION_TOKENS = 4_096

    def __init__(
        self,
        *,
        project_root: Path,
        data_root: Path | None = None,
        session_manager: SessionManager | None = None,
        context_builder: ContextBuilder | None = None,
        skills_loader: SkillsLoader | None = None,
        tools_registry: ToolsRegistry | None = None,
        model_client: LoopModelClient | None = None,
        provider_config: ProviderConfig | None = None,
        loop_runner: LoopRunner | None = None,
    ) -> None:
        self.project_root = project_root
        self.data_root = data_root or (project_root / "data")
        self.session_manager = session_manager or SessionManager(self.data_root)
        self.context_builder = context_builder or ContextBuilder(project_root)
        self.skills_loader = skills_loader or SkillsLoader()
        self.tools_registry = tools_registry or ToolsRegistry()
        self.provider_config = provider_config
        self.model_client = model_client
        self.loop_runner = loop_runner or LoopRunner(model_client=model_client)
        self._trace_sink: TraceSink | None = None

    def create_session(
        self,
        topic: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionSnapshot:
        session = self.session_manager.create(topic=topic, metadata=metadata)
        return session.snapshot()

    def get_session_snapshot(self, session_id: str) -> SessionSnapshot:
        return self.session_manager.snapshot(session_id)

    def reset_session(self, session_id: str) -> SessionSnapshot:
        session = self.session_manager.require(session_id)
        session.clear()
        self.session_manager.save(session)
        return session.snapshot()

    def run(self, request: RunRequest) -> RunResult:
        session = self.session_manager.require(request.session_id)
        self._ensure_model_client()
        self._ensure_memory_consolidator()
        if isinstance(self.loop_runner, LoopRunner):
            self.loop_runner.trace_sink = self._trace_sink
        extra_allowed_dirs = [session.workspace_path / "tmp"]
        metadata_extra_dirs = request.metadata.get("extra_allowed_dirs", [])
        if isinstance(metadata_extra_dirs, list):
            string_paths = [Path(value) for value in metadata_extra_dirs if isinstance(value, str)]
            extra_allowed_dirs.extend(string_paths)
        tools_registry = self.tools_registry.for_context(
            allowed_dir=session.workspace_path,
            extra_allowed_dirs=extra_allowed_dirs,
        )
        return self.loop_runner.run(
            session=session,
            request=request,
            context_builder=self.context_builder,
            skills_loader=self.skills_loader,
            tools_registry=tools_registry,
            save_session=self.session_manager.save,
        )

    def _ensure_model_client(self) -> None:
        if not isinstance(self.loop_runner, LoopRunner):
            return
        if not hasattr(self.loop_runner, "model_client"):
            return
        if self.loop_runner.model_client is not None:
            return
        if self.model_client is not None:
            self.loop_runner.model_client = self.model_client
            return
        try:
            config = self.provider_config or ProviderConfig.load()
            self.provider_config = config
            self.model_client = create_default_model_client(config)
            self.loop_runner.model_client = self.model_client
        except RuntimeInitializationError:
            raise

    def _ensure_memory_consolidator(self) -> None:
        if not isinstance(self.loop_runner, LoopRunner):
            return
        if not hasattr(self.loop_runner, "memory_consolidator"):
            return
        if self.loop_runner.memory_consolidator is not None:
            existing_hook: Any = self.loop_runner.memory_consolidator
            if hasattr(existing_hook, "trace_sink"):
                cast(Any, existing_hook).trace_sink = self._trace_sink
            return
        if self.model_client is None:
            return
        self.loop_runner.memory_consolidator = RuntimeMemoryConsolidator(
            agent=DefaultMemoryConsolidationAgent(model_client=self.model_client),
            context_window_tokens=self._DEFAULT_CONTEXT_WINDOW_TOKENS,
            max_completion_tokens=self._DEFAULT_MAX_COMPLETION_TOKENS,
            trace_sink=self._trace_sink,
        )
