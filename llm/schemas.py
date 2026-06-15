"""Pydantic schemas for structured issue triage."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from pydantic import model_validator


IssueType = Literal["bug", "unknown"]
ComponentName = Literal[
    "firmware_update",
    "auth",
    "bluetooth",
    "networking",
    "release_pipeline",
    "unknown",
]
OwnerTeam = Literal[
    "platform-team",
    "firmware-update-team",
    "device-connectivity-team",
    "networking-team",
    "build-systems-team",
    "needs-human-triage",
]


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

    issue_type: IssueType
    component: ComponentName
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str


class OwnerRecommendationOutput(BaseModel):
    """Structured team ownership recommendation."""

    recommended_owner: OwnerTeam
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str]

    @model_validator(mode="after")
    def unknown_owner_requires_human_triage(self) -> "OwnerRecommendationOutput":
        """Keep low-confidence/unknown ownership routed to humans."""
        if self.recommended_owner == "needs-human-triage" and self.confidence > 0.75:
            self.confidence = 0.75
        return self


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
