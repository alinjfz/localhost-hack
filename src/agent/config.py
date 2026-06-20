"""Runtime settings for the shared agent helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


def _parse_bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    exo_base_url: str = "http://localhost:52415"
    cognee_llm_provider: str = "ollama"
    cognee_embedding_provider: str = "ollama"
    cognee_embedding_model: str = "nomic-embed-text"
    overmind_enabled: bool = False
    overmind_endpoint: str = "http://localhost:8080/traces"
    agent_name: str = "LocalMind"
    agent_data_dir: str = "./data"
    webhook_secret: str = ""
    app_preview_port: int = 9101
    review_agent_port: int = 9102
    dashboard_port: int = 9103
    overmind_port: int = 9104
    repo_path: str = "/home/git/repositories/team/project.git"
    checkout_path: str = "/tmp/app-preview"
    reviews_path: str = "/home/pi/reviews"
    vision_model: str = "moondream"
    code_review_url_primary: str = "http://mac2_ip:9200/v1"
    code_review_url_fallback: str = "http://mac1_ip:9200/v1"
    code_review_model: str = "mlx-community/Qwen3.5-9B-MLX-8bit"
    captur_api_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from environment variables once per process."""

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        exo_base_url=os.getenv("EXO_BASE_URL", "http://localhost:52415"),
        cognee_llm_provider=os.getenv("COGNEE_LLM_PROVIDER", "ollama"),
        cognee_embedding_provider=os.getenv("COGNEE_EMBEDDING_PROVIDER", "ollama"),
        cognee_embedding_model=os.getenv("COGNEE_EMBEDDING_MODEL", "nomic-embed-text"),
        overmind_enabled=_parse_bool(os.getenv("OVERMIND_ENABLED"), default=False),
        overmind_endpoint=os.getenv("OVERMIND_ENDPOINT", "http://localhost:8080/traces"),
        agent_name=os.getenv("AGENT_NAME", "LocalMind"),
        agent_data_dir=os.getenv("AGENT_DATA_DIR", "./data"),
        webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
        app_preview_port=int(os.getenv("APP_PREVIEW_PORT", "9101")),
        review_agent_port=int(os.getenv("REVIEW_AGENT_PORT", "9102")),
        dashboard_port=int(os.getenv("DASHBOARD_PORT", "9103")),
        overmind_port=int(os.getenv("OVERMIND_PORT", "9104")),
        repo_path=os.getenv("REPO_PATH", "/home/git/repositories/team/project.git"),
        checkout_path=os.getenv("CHECKOUT_PATH", "/tmp/app-preview"),
        reviews_path=os.getenv("REVIEWS_PATH", "/home/pi/reviews"),
        vision_model=os.getenv("VISION_MODEL", "moondream"),
        code_review_url_primary=os.getenv("CODE_REVIEW_URL_PRIMARY", "http://mac2_ip:9200/v1"),
        code_review_url_fallback=os.getenv("CODE_REVIEW_URL_FALLBACK", "http://mac1_ip:9200/v1"),
        code_review_model=os.getenv("CODE_REVIEW_MODEL", "mlx-community/Qwen3.5-9B-MLX-8bit"),
        captur_api_key=os.getenv("CAPTUR_API_KEY", ""),
    )
