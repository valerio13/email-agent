"""Scheduler tests: the job is registered for the right time and a run does the whole pipeline."""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy.orm import sessionmaker

from app.domain.models import PipelineResult
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.demo import DemoMailProvider
from app.scheduler import JOB_ID, create_scheduler, run_pipeline
from tests.helpers import make_settings


def test_daily_job_is_registered_at_the_configured_local_time(session):
    settings = make_settings(
        demo_mode=True, schedule_time=time(7, 30), schedule_timezone="Europe/Madrid"
    )
    scheduler = create_scheduler(
        settings, sessionmaker(bind=session.get_bind()), DemoMailProvider(), FakeLLMProvider()
    )
    job = scheduler.get_job(JOB_ID)

    midnight_utc = datetime(2026, 10, 27, 0, 0, tzinfo=UTC)
    next_run = job.trigger.get_next_fire_time(None, midnight_utc)
    # 07:30 in Madrid (UTC+1 on that date), not 07:30 UTC.
    assert next_run == datetime(2026, 10, 27, 7, 30, tzinfo=ZoneInfo("Europe/Madrid"))


def test_scheduled_run_ingests_and_analyses_once(session):
    factory = sessionmaker(bind=session.get_bind())
    mail, llm = DemoMailProvider(), FakeLLMProvider()
    assert run_pipeline(factory, mail, llm) == PipelineResult(new_emails=36, analysed=36)
    assert run_pipeline(factory, mail, llm) == PipelineResult(new_emails=0, analysed=0)
