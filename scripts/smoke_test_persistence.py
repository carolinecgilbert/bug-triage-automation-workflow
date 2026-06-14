"""Smoke test for persisted FastAPI triage runs and feedback.

Run from the repository root:

    python scripts/smoke_test_persistence.py --provider mock
    python scripts/smoke_test_persistence.py --provider openai

If local Postgres is not running:

    docker compose up -d
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test triage persistence and feedback.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="LLM provider to use. Defaults to mock to avoid token spend.",
    )
    args = parser.parse_args()

    try:
        from src.api.main import app

        with TestClient(app) as client:
            triage_response = client.post(
                "/triage",
                json={
                    "ticket_id": "BUG-PERSIST-001",
                    "title": "Firmware OTA hash mismatch",
                    "description": "Firmware update manifest hash mismatch prevents OTA install.",
                    "provider": args.provider,
                    "require_approval": True,
                },
            )
            triage_response.raise_for_status()
            run_id = triage_response.json()["run_id"]

            stored_response = client.get(f"/triage/{run_id}")
            stored_response.raise_for_status()

            feedback_response = client.post(
                "/feedback",
                json={
                    "run_id": run_id,
                    "approved": True,
                    "correct_owner": True,
                    "useful_rca": True,
                    "useful_comment": True,
                    "notes": "Persistence smoke test feedback.",
                },
            )
            feedback_response.raise_for_status()
    except Exception as exc:
        raise SystemExit(
            "Could not connect to Postgres. Run: docker compose up -d. "
            f"Details: {exc}"
        ) from exc

    print("triage_run")
    print(json.dumps(triage_response.json(), indent=2))
    print()
    print("stored_run")
    print(json.dumps(stored_response.json(), indent=2))
    print()
    print("feedback")
    print(json.dumps(feedback_response.json(), indent=2))
    print()
    print(f"Persistence smoke test passed for run_id={run_id}")


if __name__ == "__main__":
    main()
