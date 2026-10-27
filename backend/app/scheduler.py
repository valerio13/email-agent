"""Scheduler: runs the pipeline once a day in a background thread of the API process."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.domain.models import PipelineResult
from app.factory import build_services
from app.providers.llm.base import LLMProvider
from app.providers.mail.base import MailProvider

logger = logging.getLogger(__name__)

JOB_ID = "daily-pipeline"


def run_pipeline(
    session_factory: sessionmaker[Session], mail: MailProvider, llm: LLMProvider
) -> PipelineResult:
    """One scheduled run. It opens its own session because there is no HTTP request."""
    with session_factory() as session:
        result = build_services(session, mail, llm).pipeline.run()
    logger.info(
        "Daily run finished: %d new emails, %d analysed.", result.new_emails, result.analysed
    )
    return result


def create_scheduler(
    settings: Settings,
    session_factory: sessionmaker[Session],
    mail: MailProvider,
    llm: LLMProvider,
) -> BackgroundScheduler:
    """Return a scheduler with the daily job registered. The caller starts and stops it."""
    scheduler = BackgroundScheduler(timezone=settings.schedule_timezone)
    scheduler.add_job(
        run_pipeline,
        # The trigger needs the timezone itself: it does not inherit the scheduler's.
        CronTrigger(
            hour=settings.schedule_time.hour,
            minute=settings.schedule_time.minute,
            timezone=settings.schedule_timezone,
        ),
        args=[session_factory, mail, llm],
        id=JOB_ID,
        # If several runs pile up because the process was busy, run once, within the first hour.
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler
