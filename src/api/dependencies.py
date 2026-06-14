"""FastAPI dependency helpers."""

from __future__ import annotations

from llm.base_client import BaseTriageLLM
from llm.mock_client import MockTriageLLM
from llm.openai_client import create_openai_triage_llm
from sqlalchemy.orm import Session

from src.api.schemas import ProviderName
from src.db.database import get_db


def create_llm_client(provider: ProviderName) -> BaseTriageLLM:
    """Create the requested LLM client for API-triggered workflows."""
    if provider == "mock":
        return MockTriageLLM()
    if provider == "openai":
        return create_openai_triage_llm()
    raise ValueError(f"Unsupported provider: {provider}")


DbSession = Session

