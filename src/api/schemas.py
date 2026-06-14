"""API request and response schemas."""

from __future__ import annotations

from datetime import datetime
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

    run_id: str
    status: str
    approval_required: bool
    approval_reason: str | None = None
    final_state: dict[str, Any] = Field(default_factory=dict)
    ticket_id: str
    provider: ProviderName
    require_approval: bool


class TriageRunSummary(BaseModel):
    """Summary of a stored triage run."""

    run_id: str
    ticket_id: str | None = None
    title: str
    status: str
    latency_ms: int | None = None
    approval_required: bool
    started_at: datetime


class StoredTriageRunResponse(BaseModel):
    """Stored triage run including evidence and feedback."""

    run_id: str
    ticket_id: str | None = None
    provider: str
    title: str
    description: str
    repo_name: str | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    latency_ms: int | None = None
    approval_required: bool
    approval_reason: str | None = None
    final_state: dict[str, Any] = Field(default_factory=dict)
    retrieved_sources: list[dict[str, Any]] = Field(default_factory=list)
    feedback: list[dict[str, Any]] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    """Human feedback payload for a triage run."""

    run_id: str
    approved: bool
    correct_owner: bool | None = None
    useful_rca: bool | None = None
    useful_comment: bool | None = None
    notes: str | None = None


class FeedbackResponse(BaseModel):
    """Response after storing human feedback."""

    feedback_id: int
    run_id: str
    stored: bool


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
