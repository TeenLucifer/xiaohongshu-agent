"""Runtime error types."""

from __future__ import annotations


class AgentRuntimeError(Exception):
    """Base exception for runtime-level failures."""


class RuntimeInitializationError(AgentRuntimeError):
    """Raised when runtime initialization cannot complete."""


class SessionNotFoundError(AgentRuntimeError):
    """Raised when a requested session does not exist."""


class ProviderCallError(AgentRuntimeError):
    """Raised when the model provider fails in a non-recoverable way."""


class PromptConfigError(AgentRuntimeError):
    """Raised when internal prompt configuration is missing or invalid."""
