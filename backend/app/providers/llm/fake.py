"""Deterministic LLM provider for tests and demo mode. It needs no API key."""

from email.utils import parseaddr

from app.domain.models import Category, Email, EmailAnalysis, Priority
from app.providers.llm.base import LLMProvider

URGENT_WORDS = ("urgent", "asap", "outage", "overdue", "deadline", "immediately")
REPLY_WORDS = ("?", "please", "could you", "can you", "quote", "meeting")


class FakeLLMProvider(LLMProvider):
    """Classifies an email with simple keyword rules instead of calling a model."""

    def analyze_email(self, email: Email) -> EmailAnalysis:
        text = f"{email.subject} {email.body}".lower()
        if any(word in text for word in URGENT_WORDS):
            category, priority = Category.URGENT, Priority.HIGH
        elif any(word in text for word in REPLY_WORDS):
            category, priority = Category.NEEDS_REPLY, Priority.MEDIUM
        else:
            category, priority = Category.INFORMATIONAL, Priority.LOW

        needs_reply = category != Category.INFORMATIONAL
        return EmailAnalysis(
            category=category,
            priority=priority,
            summary=self._summary(email),
            needs_reply=needs_reply,
            draft_reply=self._draft(email) if needs_reply else None,
        )

    @staticmethod
    def _summary(email: Email) -> str:
        """Subject plus the first sentence of the body, cut to the maximum length."""
        first_sentence = email.body.strip().split(".")[0].strip()
        return f"{email.subject}: {first_sentence}"[:300].strip(": ")

    @staticmethod
    def _draft(email: Email) -> str:
        """A short generic reply that greets the sender by first name."""
        display_name = parseaddr(email.sender)[0]
        first_name = display_name.split()[0] if display_name else "there"
        return (
            f"Hi {first_name},\n\n"
            f'Thanks for your message about "{email.subject}". '
            "I will review it and get back to you shortly.\n\n"
            "Best regards"
        )
