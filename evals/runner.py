"""Offline eval runner for the existing LangGraph triage workflow."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from agent.graph import run_triage_workflow
from evals.metrics import score_case, summarize_results
from llm.base_client import BaseTriageLLM
from llm.mock_client import MockTriageLLM
from llm.openai_client import create_openai_triage_llm
from llm.triage_service import TriageService


DEFAULT_CASES_PATH = "evals/test_cases.json"
DEFAULT_OUTPUT_PATH = "evals/results/latest_results.json"


def load_eval_cases(path: str) -> list[dict]:
    """Load eval cases from a JSON file."""
    cases_path = Path(path)
    with cases_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError(f"Expected eval cases list in {path}.")

    return cases


def run_eval_case(eval_case: dict, provider: str = "mock") -> dict:
    """Run one eval case through the existing LangGraph workflow."""
    input_state = {
        "ticket_id": eval_case.get("ticket_id"),
        "issue_title": eval_case.get("title", ""),
        "issue_body": eval_case.get("description", ""),
        "issue_comments": eval_case.get("comments", []),
        "labels": eval_case.get("labels", []),
        "logs": eval_case.get("logs", []),
        "repo_name": eval_case.get("repo_name"),
    }
    service = TriageService(llm_client=create_llm_client(provider))

    timer_start = perf_counter()
    final_state = run_triage_workflow(input_state, triage_service=service)
    latency_ms = int((perf_counter() - timer_start) * 1000)
    metrics = score_case(final_state, eval_case, latency_ms=latency_ms)

    return {
        "case_id": eval_case.get("id"),
        "ticket_id": eval_case.get("ticket_id"),
        "final_state": final_state,
        "metrics": metrics,
        "expected": {
            "component": eval_case.get("expected_component"),
            "owner": eval_case.get("expected_owner"),
            "issue_type": eval_case.get("expected_issue_type"),
            "approval_required": eval_case.get("expected_approval_required"),
            "retrieved_sources": eval_case.get("expected_retrieved_sources", []),
        },
        "latency_ms": latency_ms,
    }


def run_evals(
    cases_path: str = DEFAULT_CASES_PATH,
    provider: str = "mock",
    output_path: str | None = DEFAULT_OUTPUT_PATH,
) -> dict:
    """Run all eval cases and optionally write results to JSON."""
    cases = load_eval_cases(cases_path)
    case_results = [run_eval_case(eval_case, provider=provider) for eval_case in cases]
    summary = summarize_results(case_results)
    output = {
        "provider": provider,
        "summary": summary,
        "results": case_results,
    }

    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(output, indent=2), encoding="utf-8")

    return output


def create_llm_client(provider: str) -> BaseTriageLLM:
    """Create the LLM provider used by the eval run."""
    normalized_provider = provider.strip().lower()
    if normalized_provider == "mock":
        return MockTriageLLM()
    if normalized_provider == "openai":
        return create_openai_triage_llm()
    raise ValueError("provider must be either 'mock' or 'openai'.")
