"""Overmind-compatible trace collector."""

from __future__ import annotations

import time

from .config import get_settings

settings = get_settings()

try:  # pragma: no cover - optional dependency in the trimmed repo.
    import httpx
except Exception:  # pragma: no cover - exercised in local test runs without httpx.
    httpx = None

_traces: list[dict] = []


def record(role: str, content: str, tool_calls: list | None = None) -> None:
    _traces.append(
        {
            "timestamp": time.time(),
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
        }
    )


async def flush() -> None:
    """Push collected traces to the Overmind endpoint when enabled."""

    if not settings.overmind_enabled or not _traces or httpx is None:
        return

    payload = {"agent": settings.agent_name, "traces": _traces.copy()}
    _traces.clear()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(settings.overmind_endpoint, json=payload)
    except Exception:
        pass
