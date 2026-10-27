from app.core.config import Settings


def make_settings(demo_mode: bool) -> Settings:
    """Settings that ignore the real .env, for tests."""
    return Settings(
        _env_file=None,
        database_url="sqlite://",
        llm_provider="fake",
        llm_model="fake",
        demo_mode=demo_mode,
    )
