from app.core.config import Settings


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
