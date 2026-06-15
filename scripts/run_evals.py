"""CLI for running offline bug triage evals."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from evals.runner import DEFAULT_CASES_PATH, DEFAULT_OUTPUT_PATH, run_evals


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline triage workflow evals.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="LLM provider to use. Defaults to mock to avoid token spend.",
    )
    parser.add_argument(
        "--cases",
        default=DEFAULT_CASES_PATH,
        help="Path to eval cases JSON.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help="Path for eval results JSON.",
    )
    args = parser.parse_args()

    output = run_evals(
        cases_path=args.cases,
        provider=args.provider,
        output_path=args.output,
    )
    summary = output["summary"]

    print("Offline eval summary")
    print(f"Provider: {output['provider']}")
    print(f"Total cases: {summary['total_cases']}")
    print(f"Passed cases: {summary['passed_cases']}")
    print(f"Pass rate: {summary['pass_rate']:.2%}")
    print(f"Component accuracy: {summary['component_accuracy']:.2%}")
    print(f"Owner accuracy: {summary['owner_accuracy']:.2%}")
    print(f"Issue type accuracy: {summary['issue_type_accuracy']:.2%}")
    print(f"Approval accuracy: {summary['approval_accuracy']:.2%}")
    print(f"Average retrieval hit rate: {summary['average_retrieval_hit_rate']:.2%}")
    print(f"Average latency ms: {summary['average_latency_ms']:.1f}")
    print(f"Results written to: {args.output}")

    if summary["average_retrieval_hit_rate"] == 0:
        print()
        print("Retrieval hit rate is 0. If Chroma has not been ingested, run:")
        print("python -m rag.ingest --provider hash")

    failed = [result for result in output["results"] if not result["metrics"]["passed"]]
    if failed:
        print()
        print("Failed cases:")
        for result in failed[:5]:
            reasons = failure_reasons(result["metrics"])
            print(f"- {result['case_id']} ({result['ticket_id']}): {', '.join(reasons)}")


def failure_reasons(metrics: dict) -> list[str]:
    """Create short human-readable failure reasons."""
    reasons = []
    if not metrics["component_correct"]:
        reasons.append("component")
    if not metrics["owner_correct"]:
        reasons.append("owner")
    if not metrics["issue_type_correct"]:
        reasons.append("issue_type")
    if not metrics["approval_correct"]:
        reasons.append("approval")
    if metrics["retrieval_hit_rate"] <= 0:
        reasons.append("retrieval")
    return reasons or ["unknown"]


if __name__ == "__main__":
    main()
