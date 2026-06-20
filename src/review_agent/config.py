"""Settings for the Raspberry Pi review-agent."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class ReviewSettings:
    webhook_secret: str = ""
    review_agent_host: str = "0.0.0.0"
    review_agent_port: int = 9102
    app_preview_port: int = 9101
    dashboard_port: int = 9103
    repo_path: str = "/home/git/repositories/team/project.git"
    checkout_path: str = "/tmp/app-preview"
    reviews_path: str = "/home/pi/reviews"
    preview_entrypoint: str = "demo-project/landing-page/index.html"
    vision_model: str = "moondream"
    code_review_model: str = "qwen2.5-coder:1.5b"
    ollama_base_url: str = "http://localhost:11434"
    overmind_enabled: bool = False
    overmind_endpoint: str = "http://localhost:9104/traces"
    gitea_event_path: str = "/webhook"
    review_route: str = "/review"


@lru_cache(maxsize=1)
def get_settings() -> ReviewSettings:
    return ReviewSettings(
        webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
        review_agent_host=os.getenv("REVIEW_AGENT_HOST", "0.0.0.0"),
        review_agent_port=int(os.getenv("REVIEW_AGENT_PORT", "9102")),
        app_preview_port=int(os.getenv("APP_PREVIEW_PORT", "9101")),
        dashboard_port=int(os.getenv("DASHBOARD_PORT", "9103")),
        repo_path=os.getenv("REPO_PATH", "/home/git/repositories/team/project.git"),
        checkout_path=os.getenv("CHECKOUT_PATH", "/tmp/app-preview"),
        reviews_path=os.getenv("REVIEWS_PATH", "/home/pi/reviews"),
        preview_entrypoint=os.getenv("PREVIEW_ENTRYPOINT", "demo-project/landing-page/index.html"),
        vision_model=os.getenv("VISION_MODEL", "moondream"),
        code_review_model=os.getenv("CODE_REVIEW_MODEL", "qwen2.5-coder:1.5b"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        overmind_enabled=_parse_bool(os.getenv("OVERMIND_ENABLED"), default=False),
        overmind_endpoint=os.getenv("OVERMIND_ENDPOINT", "http://localhost:9104/traces"),
        gitea_event_path=os.getenv("GITEA_EVENT_PATH", "/webhook"),
        review_route=os.getenv("REVIEW_ROUTE", "/review"),
    )

