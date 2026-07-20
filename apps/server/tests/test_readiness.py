import pytest
from katha_core.config import settings
from katha_server.readiness import capabilities

_ALL = (
    "ANTHROPIC_API_KEY", "SARVAM_API_KEY", "LIVEKIT_URL", "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET", "SIP_TRUNK_ID", "R2_ENDPOINT", "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY", "LLM_BACKEND",
)


@pytest.fixture()
def clean_env(tmp_path, monkeypatch):
    # Run in a dir without a .env so only explicitly-set vars are read.
    monkeypatch.chdir(tmp_path)
    for var in _ALL:
        monkeypatch.delenv(var, raising=False)
    settings.cache_clear()
    yield monkeypatch
    settings.cache_clear()


def test_cli_backend_makes_pipeline_ready_without_api_key(clean_env):
    clean_env.setenv("LLM_BACKEND", "claude-cli")
    settings.cache_clear()
    caps = capabilities()
    assert caps["brain"]["ready"] is True
    assert caps["_summary"]["pipeline"] is True
    # ...but a live call still needs the API brain + voice + telephony.
    assert caps["_summary"]["live_call"] is False


def test_live_call_requires_full_stack(clean_env):
    for var in ("ANTHROPIC_API_KEY", "SARVAM_API_KEY", "LIVEKIT_URL",
                "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SIP_TRUNK_ID"):
        clean_env.setenv(var, "x")
    settings.cache_clear()
    caps = capabilities()
    assert caps["_summary"]["live_call"] is True
    assert caps["telephony"]["ready"] is True


def test_nothing_configured_is_honest(clean_env):
    settings.cache_clear()
    caps = capabilities()
    assert caps["_summary"]["pipeline"] is False
    assert caps["_summary"]["live_call"] is False
    assert caps["audio_storage"]["ready"] is False
    assert caps["brain"]["ready"] is False
