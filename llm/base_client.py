"""Base interface for triage LLM clients."""

from __future__ import annotations

from abc import ABC, abstractmethod

from llm.schemas import (
    ClassificationOutput,
    DraftCommentOutput,
    OwnerRecommendationOutput,
    RCAOutput,
    TriageContext,
)


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
    def classify_issue(self, context: TriageContext) -> ClassificationOutput:
        """Classify an issue into type, component, severity, and confidence."""

    @abstractmethod
    def recommend_owner(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
    ) -> OwnerRecommendationOutput:
        """Recommend the owner team for the issue."""

    @abstractmethod
    def generate_rca(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
    ) -> RCAOutput:
        """Generate a grounded root-cause hypothesis and next steps."""

    @abstractmethod
    def draft_comment(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
        rca: RCAOutput,
    ) -> DraftCommentOutput:
        """Draft a human-reviewable GitHub issue comment."""

    def generate_triage_response(
        self,
        issue_text: str,
        retrieved_context: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        """Compatibility helper that runs the four structured triage steps.

        New workflow code should call the explicit methods instead. This helper
        keeps older demos working while returning the same structured content.
        """
        context = TriageContext(
            issue_title=issue_text[:120],
            issue_body=issue_text,
            retrieved_context=[
                item.get("text", "") for item in retrieved_context or []
            ],
        )
        classification = self.classify_issue(context)
        owner = self.recommend_owner(context, classification)
        rca = self.generate_rca(context, classification, owner)
        comment = self.draft_comment(context, classification, owner, rca)

        return {
            "provider": self.provider_name,
            "classification": classification.model_dump(),
            "owner": owner.model_dump(),
            "rca": rca.model_dump(),
            "comment": comment.model_dump(),
        }
