"""Service layer for structured issue triage calls."""

from __future__ import annotations

from llm.base_client import BaseTriageLLM
from llm.factory import create_triage_llm
from llm.schemas import (
    ClassificationOutput,
    DraftCommentOutput,
    OwnerRecommendationOutput,
    RCAOutput,
    TriageContext,
)


class TriageService:
    """Thin application service that future LangGraph nodes can call.

    The service owns call ordering and delegates model-specific behavior to a
    `BaseTriageLLM` implementation. This keeps LangGraph nodes simple later:
    each node can call one method and pass typed state forward.
    """

    def __init__(self, llm_client: BaseTriageLLM | None = None) -> None:
        self.llm_client = llm_client or create_triage_llm()

    def classify_issue(self, context: TriageContext) -> ClassificationOutput:
        """Classify the issue into type, component, severity, and confidence."""
        return self.llm_client.classify_issue(context)

    def recommend_owner(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
    ) -> OwnerRecommendationOutput:
        """Recommend an owner team using issue context and classification."""
        return self.llm_client.recommend_owner(context, classification)

    def generate_rca(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
    ) -> RCAOutput:
        """Generate a root-cause hypothesis and suggested next steps."""
        return self.llm_client.generate_rca(context, classification, owner)

    def draft_comment(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
        rca: RCAOutput,
    ) -> DraftCommentOutput:
        """Draft a human-reviewable GitHub issue comment."""
        return self.llm_client.draft_comment(context, classification, owner, rca)

