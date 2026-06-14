"""Tests for the LangGraph triage workflow."""

from __future__ import annotations

from agent.graph import run_triage_workflow
from llm.mock_client import MockTriageLLM
from llm.triage_service import TriageService


def build_mock_service() -> TriageService:
    return TriageService(llm_client=MockTriageLLM())


def test_firmware_issue_workflow_completes() -> None:
    result = run_triage_workflow(
        {
            "issue_title": "Firmware OTA hash mismatch",
            "issue_body": "Firmware update manifest hash mismatch prevents OTA install.",
            "labels": ["bug", "firmware_update"],
        },
        triage_service=build_mock_service(),
    )

    assert result.get("classification")
    assert result["classification"]["component"] == "firmware_update"
    assert result.get("owner_recommendation")
    assert result["owner_recommendation"]["recommended_owner"] == "firmware-update-team"
    assert result.get("rca")
    assert result.get("draft_comment")
    assert isinstance(result.get("approval_required"), bool)


def test_auth_issue_workflow_routes_to_platform_team() -> None:
    result = run_triage_workflow(
        {
            "issue_title": "Login redirect loop",
            "issue_body": "Auth callback succeeds but token expires and users enter a redirect loop.",
        },
        triage_service=build_mock_service(),
    )

    assert result["classification"]["component"] == "auth"
    assert result["owner_recommendation"]["recommended_owner"] == "platform-team"


def test_approval_required_is_boolean() -> None:
    result = run_triage_workflow(
        {
            "issue_title": "Bluetooth pairing timeout",
            "issue_body": "BLE pairing fails during GATT discovery.",
        },
        triage_service=build_mock_service(),
    )

    assert isinstance(result.get("approval_required"), bool)
    assert isinstance(result.get("approval_reason"), str)
    assert result["approval_reason"]

