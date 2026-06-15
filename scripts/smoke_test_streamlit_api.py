"""Smoke test the FastAPI endpoints used by the Streamlit UI.

Run from the repository root after starting FastAPI:

    python scripts/smoke_test_streamlit_api.py --provider mock

This script does not launch Streamlit. It verifies the HTTP contract that the
Streamlit app depends on.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 20


def request_json(method: str, url: str, **kwargs: Any) -> Any:
    """Send an HTTP request and return parsed JSON."""
    try:
        response = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
    except requests.RequestException as exc:
        raise SystemExit(
            "FastAPI is not reachable. Run: uvicorn src.api.main:app --reload. "
            f"Details: {exc}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise SystemExit(f"Expected JSON from {url}, received: {response.text}") from exc

    if not response.ok:
        raise SystemExit(f"{method} {url} failed with {response.status_code}: {data}")

    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the Streamlit/FastAPI contract.")
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
        help="FastAPI base URL. Defaults to API_BASE_URL or http://127.0.0.1:8000.",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="LLM provider to use. Defaults to mock to avoid token spend.",
    )
    args = parser.parse_args()
    api_base_url = args.api_base_url.rstrip("/")

    health = request_json("GET", f"{api_base_url}/health")
    triage = request_json(
        "POST",
        f"{api_base_url}/triage",
        json={
            "ticket_id": "BUG-STREAMLIT-001",
            "title": "Firmware update fails with hash mismatch",
            "description": (
                "Devices download the OTA package but fail integrity validation before install. "
                "The logs mention manifest hash mismatch and failed_integrity_check."
            ),
            "provider": args.provider,
            "require_approval": True,
        },
    )
    run_id = triage["run_id"]
    history = request_json("GET", f"{api_base_url}/triage")
    detail = request_json("GET", f"{api_base_url}/triage/{run_id}")
    feedback = request_json(
        "POST",
        f"{api_base_url}/feedback",
        json={
            "run_id": run_id,
            "approved": True,
            "correct_owner": True,
            "useful_rca": True,
            "useful_comment": True,
            "notes": "Streamlit API contract smoke test.",
        },
    )

    print("health")
    print(json.dumps(health, indent=2))
    print()
    print("triage")
    print(json.dumps(triage, indent=2))
    print()
    print("history_count")
    print(len(history))
    print()
    print("detail")
    print(json.dumps(detail, indent=2))
    print()
    print("feedback")
    print(json.dumps(feedback, indent=2))
    print()
    print(f"Streamlit API smoke test passed for run_id={run_id}")


if __name__ == "__main__":
    main()
