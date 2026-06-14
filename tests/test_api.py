"""Tests for the FastAPI triage API."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"bugtriage_test_{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from fastapi.testclient import TestClient

from src.api.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage_with_mock_provider_returns_final_state() -> None:
    with TestClient(app) as client:
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

    assert payload["run_id"].startswith("run_")
    assert payload["status"] in {"completed", "completed_with_errors"}
    assert payload["ticket_id"] == "BUG-001"
    assert payload["provider"] == "mock"
    assert final_state["classification"]["component"] == "firmware_update"
    assert final_state["owner_recommendation"]["recommended_owner"] == "firmware-update-team"
    assert isinstance(final_state["approval_required"], bool)


def test_triage_defaults_to_mock_provider() -> None:
    with TestClient(app) as client:
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


def test_triage_persists_run() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/triage",
            json={
                "ticket_id": "BUG-003",
                "title": "Firmware artifact hash mismatch",
                "description": "OTA update fails because manifest hash differs from downloaded artifact.",
                "provider": "mock",
            },
        )
        run_id = create_response.json()["run_id"]
        get_response = client.get(f"/triage/{run_id}")

    assert get_response.status_code == 200
    stored = get_response.json()
    assert stored["run_id"] == run_id
    assert stored["ticket_id"] == "BUG-003"
    assert stored["retrieved_sources"]


def test_list_triage_runs() -> None:
    with TestClient(app) as client:
        client.post(
            "/triage",
            json={
                "ticket_id": "BUG-004",
                "title": "Auth redirect loop",
                "description": "Login redirect loop after expired token.",
                "provider": "mock",
            },
        )
        response = client.get("/triage?limit=5")

    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)
    assert runs


def test_feedback_persists() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/triage",
            json={
                "ticket_id": "BUG-005",
                "title": "Firmware OTA hash mismatch",
                "description": "Firmware update manifest hash mismatch prevents OTA install.",
                "provider": "mock",
            },
        )
        run_id = create_response.json()["run_id"]
        feedback_response = client.post(
            "/feedback",
            json={
                "run_id": run_id,
                "approved": True,
                "correct_owner": True,
                "useful_rca": True,
                "useful_comment": True,
                "notes": "Looks good for MVP.",
            },
        )
        stored_response = client.get(f"/triage/{run_id}")

    assert feedback_response.status_code == 200
    assert feedback_response.json()["stored"] is True
    assert stored_response.json()["feedback"]


def test_missing_run_returns_404() -> None:
    with TestClient(app) as client:
        get_response = client.get("/triage/run_missing")
        feedback_response = client.post(
            "/feedback",
            json={"run_id": "run_missing", "approved": False},
        )

    assert get_response.status_code == 404
    assert feedback_response.status_code == 404
