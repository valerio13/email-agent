"""Draft endpoints: the reviewer lists, edits, approves or discards reply drafts."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import ServicesDep
from app.domain.models import DigestItem, Draft

router = APIRouter(prefix="/drafts", tags=["drafts"])


class DraftUpdate(BaseModel):
    """New text for a draft."""

    model_config = ConfigDict(str_strip_whitespace=True)

    body: str = Field(min_length=1)


@router.get("")
def list_pending_drafts(services: ServicesDep) -> list[DigestItem]:
    """Drafts waiting for review, each with its email and analysis, most urgent first."""
    return services.drafts.list_pending()


@router.patch("/{draft_id}")
def edit_draft(draft_id: int, update: DraftUpdate, services: ServicesDep) -> Draft:
    """Replace the text of a pending draft."""
    return services.drafts.edit(draft_id, update.body)


@router.post("/{draft_id}/approve")
def approve_draft(draft_id: int, services: ServicesDep) -> Draft:
    """Create the draft in the mailbox and mark it approved. The email is never sent."""
    return services.drafts.approve(draft_id)


@router.post("/{draft_id}/discard")
def discard_draft(draft_id: int, services: ServicesDep) -> Draft:
    """Mark a pending draft as discarded."""
    return services.drafts.discard(draft_id)


@router.post("/{draft_id}/restore")
def restore_draft(draft_id: int, services: ServicesDep) -> Draft:
    """Undo a discard: the draft goes back to waiting for review. Approved ones cannot return."""
    return services.drafts.restore(draft_id)
