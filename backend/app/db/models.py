"""Database models: email records, analysis records, and draft records."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.models import DraftStatus


class Base(DeclarativeBase):
    """Base class for all database models."""

    # Every Mapped[datetime] column is stored timezone-aware.
    type_annotation_map = {datetime: DateTime(timezone=True)}


class EmailRecord(Base):
    """A received email, as stored in the database."""

    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(primary_key=True)
    sender: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(1000))
    body: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    analysis: Mapped["AnalysisRecord | None"] = relationship(
        back_populates="email", cascade="all, delete-orphan"
    )
    drafts: Mapped[list["DraftRecord"]] = relationship(
        back_populates="email", cascade="all, delete-orphan"
    )


class AnalysisRecord(Base):
    """Structured analysis of one email, as stored in the database."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True: an email has at most one analysis.
    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), unique=True)
    category: Mapped[str] = mapped_column(String(20))
    priority: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(Text)
    needs_reply: Mapped[bool] = mapped_column(Boolean)
    draft_reply: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    email: Mapped["EmailRecord"] = relationship(back_populates="analysis")


class DraftRecord(Base):
    """A draft reply to an email, as stored in the database."""

    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # index=True: Postgres does not index foreign keys on its own.
    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=DraftStatus.PROPOSED)
    gmail_draft_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    email: Mapped["EmailRecord"] = relationship(back_populates="drafts")
