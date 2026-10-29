"""Factory: the only place that decides which implementation backs each interface.

Services receive their providers through the constructor and never know which vendor is behind
them. Changing mailbox or model means changing this file and the settings, nothing else.
"""

from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.fake import FakeLLMProvider
from app.providers.llm.langchain_provider import LangChainLLMProvider, build_openrouter_model
from app.providers.mail.base import MailProvider
from app.providers.mail.demo import DemoMailProvider
from app.providers.mail.gmail import GmailMailProvider, build_gmail_service
from app.services.analysis import AnalysisService
from app.services.demo import DemoService
from app.services.digest import DigestService
from app.services.drafts import DraftService
from app.services.ingest import IngestService
from app.services.metrics import MetricsService
from app.services.pipeline import PipelineService


@dataclass(frozen=True)
class Services:
    """Every service, all sharing one database session."""

    ingest: IngestService
    analysis: AnalysisService
    pipeline: PipelineService
    digest: DigestService
    drafts: DraftService
    metrics: MetricsService
    demo: DemoService


def build_mail_provider(settings: Settings) -> MailProvider:
    """Return the demo mailbox in demo mode, and the real Gmail mailbox otherwise."""
    if settings.demo_mode:
        return DemoMailProvider()
    return GmailMailProvider(
        build_gmail_service(settings), settings.gmail_query, settings.gmail_max_emails
    )


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Return the fake model in demo mode or when LLM_PROVIDER=fake, else the real one.

    LLM_PROVIDER=fake lets a real mailbox be tried without spending anything on a model.
    """
    if settings.demo_mode or settings.llm_provider == "fake":
        return FakeLLMProvider()
    if settings.llm_provider == "openrouter":
        return LangChainLLMProvider(build_openrouter_model(settings))
    raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Use 'fake' or 'openrouter'.")


@lru_cache
def get_mail_provider() -> MailProvider:
    """Return the shared mail provider, built once. Demo drafts live in its memory."""
    return build_mail_provider(get_settings())


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the shared LLM provider, built once."""
    return build_llm_provider(get_settings())


def build_services(session: Session, mail: MailProvider, llm: LLMProvider) -> Services:
    """Build every service on top of one database session and the given providers."""
    ingest = IngestService(session, mail)
    analysis = AnalysisService(session, llm)
    pipeline = PipelineService(ingest, analysis)
    return Services(
        ingest=ingest,
        analysis=analysis,
        pipeline=pipeline,
        digest=DigestService(session),
        drafts=DraftService(session, mail),
        metrics=MetricsService(session),
        demo=DemoService(session, mail, pipeline),
    )
