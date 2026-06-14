"""API request and response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ProviderName = Literal["mock", "openai"]


class TriageRequest(BaseModel):
    """Input payload for issue triage."""

    ticket_id: str
    title: str
    description: str
    provider: ProviderName = "mock"
    require_approval: bool = True


class TriageResponse(BaseModel):
    """Structured API response for triage workflow results."""

    ticket_id: str
    provider: ProviderName
    require_approval: bool
    final_state: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str

