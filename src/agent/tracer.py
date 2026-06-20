"""Overmind-compatible trace collector."""
import json
import time
import asyncio
import httpx
from .config import get_settings

settings = get_settings()

_traces: list[dict] = []


def record(role: str, content: str, tool_calls: list | None = None):
    _traces.append(
        {
            "timestamp": time.time(),
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
        }
    )


async def flush():
    """Push collected traces to Overmind endpoint (if enabled)."""
    if not settings.overmind_enabled or not _traces:
        return
    payload = {"agent": settings.agent_name, "traces": _traces.copy()}
    _traces.clear()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(settings.overmind_endpoint, json=payload)
    except Exception:
        pass  # never crash the agent over telemetry
