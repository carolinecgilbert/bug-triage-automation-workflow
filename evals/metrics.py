"""Pure metric helpers for offline workflow evaluation."""

from __future__ import annotations

from statistics import mean
from typing import Any


def normalize_text(value: str) -> str:
    """Normalize text for simple exact-match metrics."""
    return " ".join(str(value or "").strip().lower().split())


def exact_match(actual: object, expected: object) -> bool:
    """Return whether two values match after text normalization."""
    return normalize_text(str(actual)) == normalize_text(str(expected))


def safe_get_nested(data: dict, path: list[str], default=None):
    """Safely retrieve a nested value from a dictionary."""
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def source_hit_rate(retrieved_sources: list[dict], expected_sources: list[str]) -> float:
    """Score how many expected source filenames appear in retrieved sources."""
    if not expected_sources:
        return 1.0

    retrieved_text = []
    for source in retrieved_sources or []:
        metadata = source.get("metadata") or {}
        retrieved_text.extend(
            [
                str(source.get("source", "")),
                str(source.get("filename", "")),
                str(metadata.get("source", "")),
                str(metadata.get("filename", "")),
            ]
        )
    normalized_retrieved = "\n".join(normalize_text(value) for value in retrieved_text)
    hits = 0

    for expected_source in expected_sources:
        if normalize_text(expected_source) in normalized_retrieved:
            hits += 1

    return hits / len(expected_sources)


def score_case(
    final_state: dict,
    eval_case: dict,
    latency_ms: int | None = None,
) -> dict:
    """Score one final workflow state against one labeled eval case."""
    component_correct = exact_match(
        safe_get_nested(final_state, ["classification", "component"], ""),
        eval_case.get("expected_component", ""),
    )
    owner_correct = exact_match(
        safe_get_nested(final_state, ["owner_recommendation", "recommended_owner"], ""),
        eval_case.get("expected_owner", ""),
    )
    issue_type_correct = exact_match(
        safe_get_nested(final_state, ["classification", "issue_type"], ""),
        eval_case.get("expected_issue_type", ""),
    )
    approval_correct = bool(final_state.get("approval_required")) == bool(
        eval_case.get("expected_approval_required")
    )
    retrieval_hit_rate = source_hit_rate(
        list(final_state.get("retrieved_sources") or []),
        list(eval_case.get("expected_retrieved_sources") or []),
    )

    passed = bool(
        component_correct
        and owner_correct
        and approval_correct
        and retrieval_hit_rate > 0
    )

    return {
        "component_correct": component_correct,
        "owner_correct": owner_correct,
        "issue_type_correct": issue_type_correct,
        "approval_correct": approval_correct,
        "retrieval_hit_rate": retrieval_hit_rate,
        "latency_ms": latency_ms,
        "passed": passed,
    }


def summarize_results(case_results: list[dict]) -> dict:
    """Aggregate per-case metric dictionaries into summary metrics."""
    total_cases = len(case_results)
    if total_cases == 0:
        return {
            "total_cases": 0,
            "passed_cases": 0,
            "pass_rate": 0.0,
            "component_accuracy": 0.0,
            "owner_accuracy": 0.0,
            "issue_type_accuracy": 0.0,
            "approval_accuracy": 0.0,
            "average_retrieval_hit_rate": 0.0,
            "average_latency_ms": 0.0,
        }

    metrics = [result["metrics"] for result in case_results]
    latencies = [
        metric["latency_ms"]
        for metric in metrics
        if metric.get("latency_ms") is not None
    ]

    return {
        "total_cases": total_cases,
        "passed_cases": sum(1 for metric in metrics if metric["passed"]),
        "pass_rate": mean_bool(metric["passed"] for metric in metrics),
        "component_accuracy": mean_bool(metric["component_correct"] for metric in metrics),
        "owner_accuracy": mean_bool(metric["owner_correct"] for metric in metrics),
        "issue_type_accuracy": mean_bool(metric["issue_type_correct"] for metric in metrics),
        "approval_accuracy": mean_bool(metric["approval_correct"] for metric in metrics),
        "average_retrieval_hit_rate": mean(
            metric["retrieval_hit_rate"] for metric in metrics
        ),
        "average_latency_ms": mean(latencies) if latencies else 0.0,
    }


def mean_bool(values) -> float:
    """Return the average of boolean-like values as a float."""
    values = list(values)
    if not values:
        return 0.0
    return sum(1 for value in values if value) / len(values)
