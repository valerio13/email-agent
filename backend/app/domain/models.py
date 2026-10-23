"""Domain models shared by every layer: enums, the received email and its analysis."""

from datetime import datetime
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

    id: str
    sender: str
    subject: str
    body: str
    received_at: datetime


class EmailAnalysis(BaseModel):
    """Structured analysis of one email, as returned by the LLM."""

    model_config = ConfigDict(str_strip_whitespace=True)

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
