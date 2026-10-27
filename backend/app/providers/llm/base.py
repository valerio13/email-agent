"""LLM provider interface: the only way the app talks to a language model."""

from abc import ABC, abstractmethod

from app.domain.models import Email, EmailAnalysis


class LLMProvider(ABC):
    """A language model that analyses emails."""

    @abstractmethod
    def analyze_email(self, email: Email) -> EmailAnalysis:
        """Return the validated analysis of one email."""
