from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
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

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
