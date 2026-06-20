"""Cognee-backed persistent memory helpers."""

from __future__ import annotations

from .config import get_settings

settings = get_settings()

try:  # pragma: no cover - exercised indirectly in environments with Cognee installed.
    import cognee
    from cognee.api.v1.search import SearchType
except Exception:  # pragma: no cover - optional dependency in local test runs.
    cognee = None
    SearchType = None

_initialized = False


async def init_memory() -> None:
    """Configure Cognee once if the dependency is available."""

    global _initialized
    if _initialized or cognee is None:
        return

    cognee.config.set_llm_config(
        {
            "provider": settings.cognee_llm_provider,
            "model": settings.ollama_model,
            "endpoint": f"{settings.ollama_base_url}/v1",
        }
    )
    cognee.config.set_embedding_config(
        {
            "provider": settings.cognee_embedding_provider,
            "model": settings.cognee_embedding_model,
            "endpoint": f"{settings.ollama_base_url}/v1",
        }
    )
    await cognee.prune.prune_system(metadata=False)
    _initialized = True


async def remember(text: str, dataset: str = "conversations") -> None:
    """Store a piece of text in the knowledge graph when available."""

    if cognee is None:
        return

    await cognee.add(text, dataset_name=dataset)
    await cognee.cognify()


async def recall(query: str) -> list[str]:
    """Search memory for relevant context."""

    if cognee is None or SearchType is None:
        return []

    results = await cognee.search(SearchType.INSIGHTS, query_text=query)
    return [str(result) for result in results] if results else []


async def recall_chunks(query: str) -> list[str]:
    """Search memory for raw text chunks."""

    if cognee is None or SearchType is None:
        return []

    results = await cognee.search(SearchType.CHUNKS, query_text=query)
    return [str(result) for result in results] if results else []
