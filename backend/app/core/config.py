"""Application settings, read from environment variables and the project's .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> core -> app -> backend -> project root
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Typed settings. Real environment variables take precedence over the .env file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # the .env also holds POSTGRES_* variables used only by Docker Compose
        frozen=True,
    )

    database_url: SecretStr
    llm_provider: str
    llm_model: str
    anthropic_api_key: SecretStr = SecretStr("")
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    demo_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return the shared settings, built once on first use."""
    return Settings()
