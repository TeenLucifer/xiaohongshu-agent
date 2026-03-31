"""Runtime run-event support for streaming UI updates."""

from __future__ import annotations

from typing import Any, Protocol


class RunEventSink(Protocol):
    """Minimal sink for runtime run events."""

    def emit(self, *, event: str, payload: dict[str, Any]) -> None:
        """Emit one run event."""
