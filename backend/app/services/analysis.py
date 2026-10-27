"""Analysis service: asks the LLM to analyse each stored email and keeps the result."""

import logging

from sqlalchemy.orm import Session

from app.db.repositories import AnalysisRepository, DraftRepository, EmailRepository
from app.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class AnalysisService:
    """Analyses the emails that have no analysis yet and creates their reply drafts."""

    def __init__(self, session: Session, llm: LLMProvider) -> None:
        self._session = session
        self._llm = llm
        self._emails = EmailRepository(session)
        self._analyses = AnalysisRepository(session)
        self._drafts = DraftRepository(session)

    def run(self) -> int:
        """Analyse every pending email and return how many were analysed.

        Each email is saved in its own transaction. If the model fails on one, that email stays
        unanalysed, so the next run retries it, and the others are not affected.
        """
        analysed = 0
        for email in self._emails.list_without_analysis():
            try:
                analysis = self._llm.analyze_email(email)
                self._analyses.save(email.id, analysis)
                if analysis.draft_reply:
                    self._drafts.create(email.id, analysis.draft_reply)
                self._session.commit()
            except Exception:
                self._session.rollback()
                logger.exception("Could not analyse email %s", email.id)
                continue
            analysed += 1
        return analysed
