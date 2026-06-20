from src.agent import config


def test_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "exo")
    monkeypatch.setenv("OVERMIND_ENABLED", "yes")
    monkeypatch.setenv("AGENT_NAME", "ReviewBot")
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.llm_provider == "exo"
    assert settings.overmind_enabled is True
    assert settings.agent_name == "ReviewBot"


def test_settings_uses_defaults(monkeypatch):
    for key in [
        "LLM_PROVIDER",
        "OVERMIND_ENABLED",
        "AGENT_NAME",
    ]:
        monkeypatch.delenv(key, raising=False)
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.llm_provider == "ollama"
    assert settings.overmind_enabled is False
    assert settings.agent_name == "LocalMind"
