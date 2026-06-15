"""Tests for structured LLM triage behavior."""

from __future__ import annotations

from llm.mock_client import MockTriageLLM
from pydantic import ValidationError
from llm.schemas import (
    ClassificationOutput,
    DraftCommentOutput,
    OwnerRecommendationOutput,
    RCAOutput,
    TriageContext,
)
from llm.triage_service import TriageService


def test_firmware_issue_maps_to_firmware_owner() -> None:
    context = TriageContext(
        issue_title="Firmware update fails with hash mismatch",
        issue_body="The OTA manifest hash does not match the downloaded firmware artifact.",
    )
    service = TriageService(llm_client=MockTriageLLM())

    classification = service.classify_issue(context)
    owner = service.recommend_owner(context, classification)

    assert classification.component == "firmware_update"
    assert owner.recommended_owner == "firmware-update-team"


def test_auth_issue_maps_to_platform_owner() -> None:
    context = TriageContext(
        issue_title="Users stuck in login redirect loop",
        issue_body="Auth callback succeeds but the session token is rejected after dashboard refresh.",
    )
    service = TriageService(llm_client=MockTriageLLM())

    classification = service.classify_issue(context)
    owner = service.recommend_owner(context, classification)

    assert classification.component == "auth"
    assert owner.recommended_owner == "platform-team"


def test_outputs_are_valid_pydantic_models() -> None:
    context = TriageContext(
        issue_title="DNS failure during startup",
        issue_body="Client reports network DNS failures and startup retries are exhausted.",
    )
    service = TriageService(llm_client=MockTriageLLM())

    classification = service.classify_issue(context)
    owner = service.recommend_owner(context, classification)
    rca = service.generate_rca(context, classification, owner)
    comment = service.draft_comment(context, classification, owner, rca)

    assert isinstance(classification, ClassificationOutput)
    assert isinstance(owner, OwnerRecommendationOutput)
    assert isinstance(rca, RCAOutput)
    assert isinstance(comment, DraftCommentOutput)


def test_confidence_values_are_between_zero_and_one() -> None:
    context = TriageContext(
        issue_title="Bluetooth pairing timeout",
        issue_body="BLE pairing fails during GATT discovery.",
    )
    service = TriageService(llm_client=MockTriageLLM())

    classification = service.classify_issue(context)
    owner = service.recommend_owner(context, classification)
    rca = service.generate_rca(context, classification, owner)

    assert 0.0 <= classification.confidence <= 1.0
    assert 0.0 <= owner.confidence <= 1.0
    assert 0.0 <= rca.confidence <= 1.0


def test_classification_rejects_unsupported_issue_type() -> None:
    try:
        ClassificationOutput(
            issue_type="authentication failure",
            component="auth",
            severity="high",
            confidence=0.9,
            reasoning_summary="Invalid issue_type should not pass schema validation.",
        )
    except ValidationError:
        return

    raise AssertionError("ClassificationOutput accepted unsupported issue_type")


def test_owner_recommendation_rejects_unsupported_owner() -> None:
    try:
        OwnerRecommendationOutput(
            recommended_owner="auth-squad",
            confidence=0.9,
            supporting_evidence=["Invalid owner should not pass schema validation."],
        )
    except ValidationError:
        return

    raise AssertionError("OwnerRecommendationOutput accepted unsupported owner")
