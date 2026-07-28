from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    katha_env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./katha.db"

    anthropic_api_key: str = ""
    sarvam_api_key: str = ""

    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    sip_trunk_id: str = ""

    r2_endpoint: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "katha-audio"

    # Local audio backend (dev): point at a directory of real recordings and
    # the API serves them via short-lived HMAC-signed links — no R2 needed.
    # Never a substitute for real recordings; it just avoids the cloud in dev.
    local_audio_dir: str = ""
    public_base_url: str = "http://localhost:8000"
    audio_sign_secret: str = "dev-local-audio"

    # Interviewer brain. Opus-tier: warmth + judgment are the product.
    interviewer_model: str = "claude-opus-4-8"
    # Cheap fast model for pipeline classification/verification passes.
    utility_model: str = "claude-haiku-4-5"

    # "api" (Anthropic SDK, needs credits; required for live calls) or
    # "claude-cli" (headless Claude Code on the dev's subscription — free,
    # slower; pipeline/evals only).
    llm_backend: str = ""
    cli_model: str = "sonnet"  # conserve subscription quota on background work


@lru_cache
def settings() -> Settings:
    return Settings()
