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
from app.providers.mail.base import MailProvider
from app.providers.mail.demo import DemoMailProvider
from app.services.analysis import AnalysisService
from app.services.digest import DigestService
from app.services.drafts import DraftService
from app.services.ingest import IngestService


@dataclass(frozen=True)
class Services:
    """Every service, all sharing one database session."""

    ingest: IngestService
    analysis: AnalysisService
    digest: DigestService
    drafts: DraftService


def build_mail_provider(settings: Settings) -> MailProvider:
    """Return the demo mailbox in demo mode. The Gmail provider comes later."""
    if settings.demo_mode:
        return DemoMailProvider()
    raise NotImplementedError("The Gmail provider is not implemented yet.")


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Return the fake model in demo mode. The LangChain provider comes later."""
    if settings.demo_mode:
        return FakeLLMProvider()
    raise NotImplementedError("The LangChain provider is not implemented yet.")


@lru_cache
def get_mail_provider() -> MailProvider:
    """Return the shared mail provider, built once. Demo drafts live in its memory."""
    return build_mail_provider(get_settings())


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the shared LLM provider, built once."""
    return build_llm_provider(get_settings())


def build_services(session: Session) -> Services:
    """Build every service on top of one database session."""
    mail = get_mail_provider()
    llm = get_llm_provider()
    return Services(
        ingest=IngestService(session, mail),
        analysis=AnalysisService(session, llm),
        digest=DigestService(session),
        drafts=DraftService(session, mail),
    )
