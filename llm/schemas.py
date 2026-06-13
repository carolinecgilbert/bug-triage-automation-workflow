"""Pydantic schemas for structured issue triage."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TriageContext(BaseModel):
    """Normalized issue context passed through triage steps."""

    issue_title: str
    issue_body: str
    issue_comments: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    retrieved_context: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    repo_name: str | None = None


class ClassificationOutput(BaseModel):
    """Structured classification result for a bug report."""

    issue_type: str
    component: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str


class OwnerRecommendationOutput(BaseModel):
    """Structured team ownership recommendation."""

    recommended_owner: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str]


class RCAOutput(BaseModel):
    """Structured root-cause analysis hypothesis."""

    root_cause_hypothesis: str
    suggested_next_steps: list[str]
    risk_level: str
    confidence: float = Field(ge=0.0, le=1.0)


class DraftCommentOutput(BaseModel):
    """Human-reviewable GitHub comment draft."""

    comment: str
    approval_required: bool
    tone: str

