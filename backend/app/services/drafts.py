"""Draft service: the human review of reply drafts (edit, approve, discard)."""

from sqlalchemy.orm import Session

from app.db.repositories import DraftRepository, EmailRepository
from app.domain.models import DigestItem, Draft, DraftStatus
from app.providers.mail.base import MailProvider
from app.services.digest import sort_for_review


class DraftNotFoundError(Exception):
    """There is no draft with the given id."""


class DraftNotPendingError(Exception):
    """The draft was already approved or discarded, so it can no longer change."""


class DraftNotDiscardedError(Exception):
    """The draft was not discarded, so there is nothing to restore."""


class DraftService:
    """Applies the reviewer's decisions. Approving creates the draft in the mailbox, never sends."""

    def __init__(self, session: Session, mail: MailProvider) -> None:
        self._session = session
        self._mail = mail
        self._emails = EmailRepository(session)
        self._drafts = DraftRepository(session)

    def list_pending(self) -> list[DigestItem]:
        """Return the drafts waiting for review with their email and analysis, most urgent first."""
        return sort_for_review(
            [
                DigestItem(email=email, analysis=analysis, draft=draft)
                for draft, email, analysis in self._drafts.list_with_context(DraftStatus.PROPOSED)
            ]
        )

    def edit(self, draft_id: int, body: str) -> Draft:
        """Replace the text of a pending draft."""
        if not body.strip():
            raise ValueError("The draft cannot be empty.")
        self._get_pending(draft_id)
        draft = self._drafts.update_body(draft_id, body)
        self._session.commit()
        return draft

    def approve(self, draft_id: int) -> Draft:
        """Create the draft in the mailbox and mark it approved. The email is not sent."""
        draft = self._get_pending(draft_id)
        email = self._emails.get(draft.email_id)
        # The mailbox call comes first: if it fails, nothing has changed in our database.
        gmail_draft_id = self._mail.create_draft(email, draft.body)
        approved = self._drafts.set_status(draft_id, DraftStatus.APPROVED, gmail_draft_id)
        self._session.commit()
        return approved

    def discard(self, draft_id: int) -> Draft:
        """Mark a pending draft as discarded."""
        self._get_pending(draft_id)
        discarded = self._drafts.set_status(draft_id, DraftStatus.DISCARDED)
        self._session.commit()
        return discarded

    def restore(self, draft_id: int) -> Draft:
        """Put a discarded draft back in the review list, with its text as it was.

        An approved draft cannot be restored: it already exists in the mailbox.
        """
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise DraftNotFoundError(f"Draft {draft_id} does not exist.")
        if draft.status != DraftStatus.DISCARDED:
            raise DraftNotDiscardedError(
                f"Draft {draft_id} is not discarded (it is {draft.status})."
            )
        restored = self._drafts.set_status(draft_id, DraftStatus.PROPOSED)
        self._session.commit()
        return restored

    def _get_pending(self, draft_id: int) -> Draft:
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise DraftNotFoundError(f"Draft {draft_id} does not exist.")
        if draft.status != DraftStatus.PROPOSED:
            raise DraftNotPendingError(f"Draft {draft_id} is already {draft.status}.")
        return draft
