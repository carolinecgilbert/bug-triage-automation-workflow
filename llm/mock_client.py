"""Deterministic mock LLM client for token-free MVP workflow development."""

from __future__ import annotations

from llm.base_client import BaseTriageLLM
from llm.schemas import (
    ClassificationOutput,
    DraftCommentOutput,
    OwnerRecommendationOutput,
    RCAOutput,
    TriageContext,
)


class MockTriageLLM(BaseTriageLLM):
    """Return a stable triage response without calling a hosted LLM."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def classify_issue(self, context: TriageContext) -> ClassificationOutput:
        """Classify using deterministic keyword rules."""
        combined_text = context_to_text(context)
        component, owner_team, confidence = infer_component_owner_and_confidence(combined_text)

        severity = "sev3"
        if any(keyword in combined_text for keyword in ["sev1", "outage", "all users", "data loss"]):
            severity = "sev1"
        elif any(keyword in combined_text for keyword in ["sev2", "production", "rollout", "many users"]):
            severity = "sev2"

        issue_type = "bug" if component != "unknown" else "unknown"
        return ClassificationOutput(
            issue_type=issue_type,
            component=component,
            severity=severity,
            confidence=confidence,
            reasoning_summary=(
                f"Matched issue language to {component} using deterministic MVP keyword rules."
                if component != "unknown"
                else "No strong component keywords were found, so classification confidence is low."
            ),
        )

    def recommend_owner(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
    ) -> OwnerRecommendationOutput:
        """Recommend an owner using the classified component."""
        owner = OWNER_BY_COMPONENT.get(classification.component, "needs-human-triage")
        evidence = [
            f"Classified component: {classification.component}",
            classification.reasoning_summary,
        ]
        if context.retrieved_context:
            evidence.append(f"Retrieved context snippets available: {len(context.retrieved_context)}")

        return OwnerRecommendationOutput(
            recommended_owner=owner,
            confidence=classification.confidence,
            supporting_evidence=evidence,
        )

    def generate_rca(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
    ) -> RCAOutput:
        """Generate a deterministic RCA-style hypothesis for local testing."""
        component = classification.component
        hypothesis = RCA_BY_COMPONENT.get(
            component,
            "The issue needs more evidence before a credible root-cause hypothesis can be formed.",
        )

        risk_level = "medium" if classification.severity == "sev2" else "low"
        if classification.severity == "sev1":
            risk_level = "high"

        return RCAOutput(
            root_cause_hypothesis=hypothesis,
            suggested_next_steps=[
                "Review the top retrieved context and compare against similar historical issues.",
                "Collect affected version, environment, reproduction steps, and relevant logs.",
                f"Route to {owner.recommended_owner} for human review before taking action.",
            ],
            risk_level=risk_level,
            confidence=round(max(classification.confidence - 0.05, 0.0), 2),
        )

    def draft_comment(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
        rca: RCAOutput,
    ) -> DraftCommentOutput:
        """Draft a concise human-reviewable GitHub issue comment."""
        comment = (
            "### Automated triage draft\n\n"
            f"- Component: `{classification.component}`\n"
            f"- Severity: `{classification.severity}`\n"
            f"- Recommended owner: `{owner.recommended_owner}`\n"
            f"- Confidence: `{classification.confidence:.2f}`\n\n"
            f"Root-cause hypothesis: {rca.root_cause_hypothesis}\n\n"
            "Suggested next steps:\n"
            + "\n".join(f"- {step}" for step in rca.suggested_next_steps)
            + "\n\nHuman approval is required before applying labels, assignments, or remediation."
        )

        return DraftCommentOutput(
            comment=comment,
            approval_required=True,
            tone="professional",
        )


def infer_component_and_owner(text: str) -> tuple[str, str]:
    """Small keyword router used only by the mock LLM."""
    component, owner, _confidence = infer_component_owner_and_confidence(text)
    return component, owner


def infer_component_owner_and_confidence(text: str) -> tuple[str, str, float]:
    """Map issue text to a component, owner, and confidence score."""
    normalized = text.lower()
    for component, keywords in KEYWORDS_BY_COMPONENT.items():
        if any(keyword in normalized for keyword in keywords):
            return component, OWNER_BY_COMPONENT[component], 0.85
    return "unknown", "needs-human-triage", 0.35


def context_to_text(context: TriageContext) -> str:
    """Flatten context fields for deterministic keyword matching."""
    parts = [
        context.issue_title,
        context.issue_body,
        *context.issue_comments,
        *context.labels,
        *context.retrieved_context,
        *context.logs,
        context.repo_name or "",
    ]
    return " ".join(parts).lower()


OWNER_BY_COMPONENT = {
    "firmware_update": "firmware-update-team",
    "auth": "platform-team",
    "bluetooth": "device-connectivity-team",
    "networking": "networking-team",
    "release_pipeline": "build-systems-team",
}


KEYWORDS_BY_COMPONENT = {
    "firmware_update": ["firmware", "ota", "manifest", "hash mismatch", "hash"],
    "auth": ["auth", "login", "redirect", "token", "session", "oauth"],
    "bluetooth": ["bluetooth", "pairing", "ble", "gatt"],
    "networking": ["dns", "network", "wifi", "tls", "proxy"],
    "release_pipeline": ["release", "build", "artifact", "ci", "pipeline"],
}


RCA_BY_COMPONENT = {
    "firmware_update": (
        "The update package or manifest likely has an integrity mismatch, stale artifact, "
        "or hardware-specific rollout metadata issue."
    ),
    "auth": (
        "The authentication failure likely involves session validation, token refresh, "
        "redirect handling, or inconsistent signing configuration."
    ),
    "bluetooth": (
        "The pairing failure likely involves stale bonding state, BLE advertising metadata, "
        "or GATT discovery timing."
    ),
    "networking": (
        "The connectivity failure likely involves DNS resolution, retry policy, TLS, "
        "or network environment handling."
    ),
    "release_pipeline": (
        "The release issue likely involves missing artifact metadata, build configuration, "
        "or promotion pipeline validation."
    ),
}
