"""Application settings, read from environment variables and the project's .env file."""

from datetime import time
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
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
    # Printed once by `python -m app.cli authorize-gmail`. Gmail mode needs all three Google values.
    google_refresh_token: SecretStr = SecretStr("")
    # Which mail the real mailbox returns: a Gmail search, and the most emails per run.
    gmail_query: str = "in:inbox newer_than:2d"
    gmail_max_emails: int = Field(default=50, ge=1, le=500)
    demo_mode: bool = True
    scheduler_enabled: bool = True
    schedule_time: time = time(7, 0)
    schedule_timezone: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    """Return the shared settings, built once on first use."""
    return Settings()
