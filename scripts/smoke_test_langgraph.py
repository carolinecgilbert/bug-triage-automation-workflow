"""Smoke test for the LangGraph triage workflow.

Run from the repository root:

    python scripts/smoke_test_langgraph.py --provider mock
    python scripts/smoke_test_langgraph.py --provider openai
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent.graph import run_triage_workflow
from llm.mock_client import MockTriageLLM
from llm.openai_client import create_openai_triage_llm
from llm.triage_service import TriageService


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the LangGraph triage workflow.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="LLM provider to use. Defaults to mock to avoid token spend.",
    )
    args = parser.parse_args()

    input_state = {
        "repo_name": "bug-triage-automation-workflow",
        "issue_title": "Firmware update fails validation on HW-B2 devices",
        "issue_body": (
            "Devices in the OTA beta rollout download firmware 4.13.2 but fail "
            "with manifest hash mismatch and failed_integrity_check."
        ),
        "labels": ["bug", "firmware_update", "needs-triage"],
        "logs": [
            "ERROR device-updater state=failed_integrity_check expected_sha256=abc actual_sha256=def"
        ],
    }
    service = TriageService(llm_client=create_llm_client(args.provider))
    result = run_triage_workflow(input_state, triage_service=service)

    print_section("provider", args.provider)
    print_section("retrieved_sources", result.get("retrieved_sources", []))
    print_section("classification", result.get("classification", {}))
    print_section("owner_recommendation", result.get("owner_recommendation", {}))
    print_section("rca", result.get("rca", {}))
    print_section("draft_comment", result.get("draft_comment", {}))
    print_section("approval_required", result.get("approval_required"))
    print_section("approval_reason", result.get("approval_reason"))
    if result.get("errors"):
        print_section("errors", result["errors"])


def create_llm_client(provider: str):
    """Create the requested LLM client for the smoke test."""
    if provider == "mock":
        return MockTriageLLM()
    if provider == "openai":
        return create_openai_triage_llm()
    raise ValueError(f"Unsupported provider: {provider}")


def print_section(title: str, value: object) -> None:
    """Print a JSON-formatted output section."""
    print(title)
    print(json.dumps(value, indent=2))
    print()


if __name__ == "__main__":
    main()
