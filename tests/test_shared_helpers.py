import asyncio

from src.agent import memory, tracer
from src.agent.config import Settings


def test_memory_helpers_noop_without_cognee(monkeypatch):
    monkeypatch.setattr(memory, "cognee", None)
    monkeypatch.setattr(memory, "SearchType", None)
    monkeypatch.setattr(memory, "_initialized", False)

    async def run_checks():
        await memory.init_memory()
        await memory.remember("hello")
        assert await memory.recall("hello") == []
        assert await memory.recall_chunks("hello") == []

    asyncio.run(run_checks())


def test_tracer_flush_noop_without_httpx(monkeypatch):
    monkeypatch.setattr(tracer, "httpx", None)
    monkeypatch.setattr(tracer, "settings", Settings(overmind_enabled=True))
    tracer._traces.clear()

    async def run_checks():
        tracer.record("user", "hello")
        await tracer.flush()

    asyncio.run(run_checks())

    assert len(tracer._traces) == 1
