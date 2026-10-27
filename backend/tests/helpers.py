from datetime import UTC, datetime

from app.core.config import Settings

# A fixed "now" for the demo mailbox, so the dates of the demo emails do not depend on the clock.
# 2026-10-26 is the latest day of mail: 8 emails, 5 of them with a draft.
DEMO_NOW = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)


def make_settings(demo_mode: bool, **overrides) -> Settings:
    """Settings that ignore the real .env, for tests. The scheduler is off unless asked for."""
    values = {
        "database_url": "sqlite://",
        "llm_provider": "fake",
        "llm_model": "fake",
        "demo_mode": demo_mode,
        "scheduler_enabled": False,
    }
    return Settings(_env_file=None, **(values | overrides))
