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

    # Interviewer brain. Opus-tier: warmth + judgment are the product.
    interviewer_model: str = "claude-opus-4-8"
    # Cheap fast model for pipeline classification/verification passes.
    utility_model: str = "claude-haiku-4-5"


@lru_cache
def settings() -> Settings:
    return Settings()
