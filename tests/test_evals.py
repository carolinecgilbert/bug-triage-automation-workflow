from __future__ import annotations

from evals.metrics import score_case, source_hit_rate, summarize_results
from evals.runner import run_eval_case


def test_score_case_exact_matches() -> None:
    final_state = {
        "classification": {
            "component": "firmware_update",
            "issue_type": "bug",
        },
        "owner_recommendation": {
            "recommended_owner": "firmware-update-team",
        },
        "approval_required": True,
        "retrieved_sources": [
            {
                "source": "data/docs/firmware_update_troubleshooting.md",
                "metadata": {"filename": "firmware_update_troubleshooting.md"},
            }
        ],
    }
    eval_case = {
        "expected_component": "firmware_update",
        "expected_owner": "firmware-update-team",
        "expected_issue_type": "bug",
        "expected_approval_required": True,
        "expected_retrieved_sources": ["firmware_update_troubleshooting.md"],
    }

    metrics = score_case(final_state, eval_case, latency_ms=12)

    assert metrics["component_correct"] is True
    assert metrics["owner_correct"] is True
    assert metrics["issue_type_correct"] is True
    assert metrics["approval_correct"] is True
    assert metrics["retrieval_hit_rate"] == 1.0
    assert metrics["latency_ms"] == 12
    assert metrics["passed"] is True


def test_source_hit_rate() -> None:
    retrieved_sources = [
        {
            "source": "data/docs/auth_troubleshooting.md",
            "metadata": {"filename": "auth_troubleshooting.md"},
        },
        {
            "source": "data/code_summaries/auth_service.md",
            "metadata": {"filename": "auth_service.md"},
        },
    ]

    assert source_hit_rate(
        retrieved_sources,
        ["auth_troubleshooting.md", "missing.md"],
    ) == 0.5


def test_summarize_results() -> None:
    case_results = [
        {
            "metrics": {
                "component_correct": True,
                "owner_correct": True,
                "issue_type_correct": True,
                "approval_correct": True,
                "retrieval_hit_rate": 1.0,
                "latency_ms": 10,
                "passed": True,
            }
        },
        {
            "metrics": {
                "component_correct": False,
                "owner_correct": True,
                "issue_type_correct": True,
                "approval_correct": True,
                "retrieval_hit_rate": 0.0,
                "latency_ms": 30,
                "passed": False,
            }
        },
    ]

    summary = summarize_results(case_results)

    assert summary["total_cases"] == 2
    assert summary["passed_cases"] == 1
    assert summary["pass_rate"] == 0.5
    assert summary["component_accuracy"] == 0.5
    assert summary["owner_accuracy"] == 1.0
    assert summary["average_retrieval_hit_rate"] == 0.5
    assert summary["average_latency_ms"] == 20


def test_run_single_eval_case_mock(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    eval_case = {
        "id": "TEST-EVAL-001",
        "ticket_id": "TEST-EVAL-001",
        "title": "Firmware OTA hash mismatch",
        "description": "Firmware package fails validation because the manifest hash does not match.",
        "labels": ["bug", "firmware"],
        "logs": ["ERROR manifest hash mismatch"],
        "expected_component": "firmware_update",
        "expected_owner": "firmware-update-team",
        "expected_issue_type": "bug",
        "expected_approval_required": True,
        "expected_retrieved_sources": [],
    }

    result = run_eval_case(eval_case, provider="mock")

    assert result["case_id"] == "TEST-EVAL-001"
    assert result["metrics"]["component_correct"] is True
    assert result["metrics"]["owner_correct"] is True
    assert result["metrics"]["issue_type_correct"] is True
    assert result["metrics"]["approval_correct"] is True
    assert "final_state" in result
