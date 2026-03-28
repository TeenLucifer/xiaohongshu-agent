"""Thin shared time helpers for runtime-local timestamps."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE_NAME = "Asia/Shanghai"
APP_TIMEZONE = ZoneInfo(APP_TIMEZONE_NAME)


def now_local() -> datetime:
    """Return the current aware datetime in the app timezone."""

    return datetime.now(APP_TIMEZONE)


def format_runtime_time(value: datetime | None = None) -> str:
    """Format a user-visible runtime timestamp in the app timezone."""

    current = value.astimezone(APP_TIMEZONE) if value is not None else now_local()
    return f"{current.strftime('%Y-%m-%d %H:%M:%S %z')} {APP_TIMEZONE_NAME}"
