"""Cognee-backed persistent memory for LocalMind."""
import cognee
from cognee.api.v1.search import SearchType
from .config import get_settings

settings = get_settings()

_initialized = False


async def init_memory():
    global _initialized
    if _initialized:
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


async def remember(text: str, dataset: str = "conversations"):
    """Store a piece of text in the knowledge graph."""
    await cognee.add(text, dataset_name=dataset)
    await cognee.cognify()


async def recall(query: str) -> list[str]:
    """Search memory for relevant context."""
    results = await cognee.search(SearchType.INSIGHTS, query_text=query)
    return [str(r) for r in results] if results else []


async def recall_chunks(query: str) -> list[str]:
    """Search memory for raw text chunks."""
    results = await cognee.search(SearchType.CHUNKS, query_text=query)
    return [str(r) for r in results] if results else []
