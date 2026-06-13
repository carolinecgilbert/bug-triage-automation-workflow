"""Factory for selecting mock or hosted LLM reasoning."""

from __future__ import annotations

import os

from llm.base_client import BaseTriageLLM
from llm.mock_client import MockTriageLLM


def create_triage_llm() -> BaseTriageLLM:
    """Create the configured triage LLM.

    LLM_PROVIDER defaults to mock so the MVP workflow can be built without
    spending tokens. The OpenAI implementation is imported lazily so local-only
    development stays lightweight.
    """
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()

    if provider == "mock":
        return MockTriageLLM()

    if provider == "openai":
        from llm.openai_client import create_openai_triage_llm

        return create_openai_triage_llm()

    raise RuntimeError("LLM_PROVIDER must be either 'mock' or 'openai'.")
