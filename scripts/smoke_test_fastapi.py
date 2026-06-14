"""Smoke test for the FastAPI triage endpoint.

Run from the repository root:

    python scripts/smoke_test_fastapi.py --provider mock
    python scripts/smoke_test_fastapi.py --provider openai
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the FastAPI triage endpoint.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="LLM provider to use. Defaults to mock to avoid token spend.",
    )
    args = parser.parse_args()

    client = TestClient(app)
    health_response = client.get("/health")
    triage_response = client.post(
        "/triage",
        json={
            "ticket_id": "BUG-FASTAPI-001",
            "title": "Firmware update fails validation on HW-B2 devices",
            "description": (
                "Devices in the OTA beta rollout download firmware 4.13.2 but fail "
                "with manifest hash mismatch and failed_integrity_check."
            ),
            "provider": args.provider,
            "require_approval": True,
        },
    )

    print("health")
    print(json.dumps(health_response.json(), indent=2))
    print()
    print("triage")
    print(json.dumps(triage_response.json(), indent=2))

    health_response.raise_for_status()
    triage_response.raise_for_status()


if __name__ == "__main__":
    main()

