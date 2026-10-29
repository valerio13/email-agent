"""Domain models shared by every layer: enums, the received email and its analysis."""

from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Category(StrEnum):
    URGENT = "urgent"
    NEEDS_REPLY = "needs_reply"
    INFORMATIONAL = "informational"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DraftStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    DISCARDED = "discarded"


class Email(BaseModel):
    """A received email, as returned by a mail provider."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    sender: str
    subject: str
    body: str
    received_at: datetime


class EmailAnalysis(BaseModel):
    """Structured analysis of one email, as returned by the LLM."""

    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    category: Category = Field(description="Main category of the email.")
    priority: Priority = Field(description="How soon the email should be handled.")
    summary: str = Field(
        min_length=1,
        max_length=300,
        description="Summary of the email in one or two sentences.",
    )
    needs_reply: bool = Field(description="True if the sender expects an answer.")
    draft_reply: str | None = Field(
        default=None,
        description="Suggested reply in the language of the email. Null if no reply is needed.",
    )

    @model_validator(mode="after")
    def check_draft_rule(self) -> Self:
        if self.needs_reply and not self.draft_reply:
            raise ValueError("A draft reply is required when the email needs a reply.")
        if self.draft_reply and not self.needs_reply:
            raise ValueError("No draft reply is allowed when the email does not need a reply.")
        return self


class Draft(BaseModel):
    """A reply draft waiting for human review."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email_id: str
    body: str
    status: DraftStatus
    gmail_draft_id: str | None = None
    created_at: datetime
    updated_at: datetime


class DigestItem(BaseModel):
    """One line of the digest: an email with its analysis and its reply draft, if it has one."""

    email: Email
    analysis: EmailAnalysis
    draft: Draft | None = None


class PipelineResult(BaseModel):
    """What one run of the pipeline did."""

    new_emails: int
    analysed: int


class Digest(BaseModel):
    """The prioritized summary of one day of mail, shown at the top of the dashboard."""

    # The UTC day the digest covers. None when there is no analysed email yet.
    day: date | None
    # The closest days with analysed mail before and after `day`, to move between days.
    previous_day: date | None
    next_day: date | None
    total: int
    counts: dict[Category, int]
    # Drafts waiting for review, whatever day their email came from.
    pending_drafts: int
    items: list[DigestItem]


class DailyCount(BaseModel):
    """How many emails arrived on one day."""

    day: date
    emails: int


class Metrics(BaseModel):
    """What the agent did over the last seven days of mail, with an estimate of the time saved."""

    # One entry per day, oldest first, ending on the day of the newest email. Empty without mail.
    days: list[DailyCount]
    emails_processed: int
    drafts_created: int
    # Drafts waiting for review, whatever day their email came from.
    waiting_for_review: int
    minutes_saved: int
    minutes_per_email: int
    minutes_per_draft: int
