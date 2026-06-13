"""Deterministic mock LLM client for token-free MVP workflow development."""

from __future__ import annotations

from llm.base_client import BaseTriageLLM, TriageContext, TriageResponse


class MockTriageLLM(BaseTriageLLM):
    """Return a stable triage response without calling a hosted LLM."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def generate_triage_response(
        self,
        issue_text: str,
        retrieved_context: TriageContext,
    ) -> TriageResponse:
        """Generate a predictable response shaped like a future LLM result."""
        combined_text = " ".join(
            [issue_text, *[item.get("text", "") for item in retrieved_context]]
        ).lower()

        component, owner_team = infer_component_and_owner(combined_text)

        return {
            "provider": self.provider_name,
            "component": component,
            "recommended_owner": owner_team,
            "confidence": "medium",
            "root_cause_hypotheses": [
                f"Likely related to the {component} component based on issue terms and retrieved context.",
                "Compare the new report against similar historical issues before assigning final severity.",
            ],
            "recommended_next_steps": [
                "Review the top retrieved troubleshooting document and matching historical issue.",
                "Attach relevant logs, affected version, environment, and reproduction details.",
                f"Route to {owner_team} for human approval before remediation work starts.",
            ],
            "human_approval_required": True,
        }


def infer_component_and_owner(text: str) -> tuple[str, str]:
    """Small keyword router used only by the mock LLM."""
    if any(keyword in text for keyword in ["firmware", "ota", "manifest", "hash"]):
        return "firmware_update", "firmware-update-team"
    if any(keyword in text for keyword in ["auth", "login", "session", "oauth", "token"]):
        return "auth", "platform-team"
    if any(keyword in text for keyword in ["bluetooth", "ble", "pairing", "gatt"]):
        return "bluetooth", "device-connectivity-team"
    if any(keyword in text for keyword in ["dns", "network", "tls", "proxy"]):
        return "networking", "networking-team"
    if any(keyword in text for keyword in ["release", "pipeline", "deployment"]):
        return "release_pipeline", "build-systems-team"

    return "unknown", "needs-human-triage"
