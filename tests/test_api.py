"""Tests for the FastAPI triage API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage_with_mock_provider_returns_final_state() -> None:
    response = client.post(
        "/triage",
        json={
            "ticket_id": "BUG-001",
            "title": "Firmware OTA hash mismatch",
            "description": "Firmware update manifest hash mismatch prevents OTA install.",
            "provider": "mock",
            "require_approval": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    final_state = payload["final_state"]

    assert payload["ticket_id"] == "BUG-001"
    assert payload["provider"] == "mock"
    assert final_state["classification"]["component"] == "firmware_update"
    assert final_state["owner_recommendation"]["recommended_owner"] == "firmware-update-team"
    assert isinstance(final_state["approval_required"], bool)


def test_triage_defaults_to_mock_provider() -> None:
    response = client.post(
        "/triage",
        json={
            "ticket_id": "BUG-002",
            "title": "Login redirect loop",
            "description": "Auth callback succeeds but token expires and users enter a redirect loop.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["final_state"]["owner_recommendation"]["recommended_owner"] == "platform-team"

