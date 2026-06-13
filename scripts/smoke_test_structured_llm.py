"""Smoke test for structured LLM triage calls.

Run from the repository root:

    python scripts/smoke_test_structured_llm.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from llm.mock_client import MockTriageLLM
from llm.schemas import TriageContext
from llm.triage_service import TriageService


def main() -> None:
    context = TriageContext(
        repo_name="bug-triage-automation-workflow",
        issue_title="Firmware update 4.13.2 fails validation on HW-B2 devices",
        issue_body=(
            "Beta customers report that firmware 4.13.2 downloads successfully "
            "but fails installation with a hash mismatch and failed_integrity_check."
        ),
        labels=["bug", "firmware_update", "needs-triage"],
        retrieved_context=[
            "Firmware update troubleshooting: compare manifest hash, artifact registry hash, and device-computed hash.",
            "Historical issue: firmware artifact was republished after manifest generation, causing hash mismatch.",
        ],
        logs=[
            "ERROR device-updater state=failed_integrity_check expected_sha256=abc actual_sha256=def",
        ],
    )

    service = TriageService(llm_client=MockTriageLLM())

    classification = service.classify_issue(context)
    owner = service.recommend_owner(context, classification)
    rca = service.generate_rca(context, classification, owner)
    comment = service.draft_comment(context, classification, owner, rca)

    print("classification")
    print(json.dumps(classification.model_dump(), indent=2))
    print()
    print("owner")
    print(json.dumps(owner.model_dump(), indent=2))
    print()
    print("rca")
    print(json.dumps(rca.model_dump(), indent=2))
    print()
    print("comment")
    print(json.dumps(comment.model_dump(), indent=2))


if __name__ == "__main__":
    main()
