"""Base interface for triage LLM clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


TriageContext = list[dict[str, str]]
TriageResponse = dict[str, Any]


class BaseTriageLLM(ABC):
    """Abstract interface for triage reasoning clients.

    This class should never be instantiated directly. Concrete clients, such as
    the mock client and OpenAI client, inherit from it and implement the same
    public contract.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the backing LLM provider."""

    @abstractmethod
    def generate_triage_response(
        self,
        issue_text: str,
        retrieved_context: TriageContext,
    ) -> TriageResponse:
        """Generate a structured triage response for an issue and its RAG context."""

