"""Small CLI demo for the token-free mock triage LLM."""

from __future__ import annotations

import argparse
import json

from dotenv import load_dotenv

from llm.factory import create_triage_llm


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mock triage reasoning without an API call.")
    parser.add_argument("issue", help="Issue text to triage.")
    args = parser.parse_args()

    load_dotenv()

    llm = create_triage_llm()
    result = llm.generate_triage_response(issue_text=args.issue, retrieved_context=[])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

