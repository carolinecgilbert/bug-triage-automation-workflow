"""Smoke test for the full current flow: RAG retrieval -> structured triage.

Run from the repository root:

    python scripts/smoke_test_rag_to_llm.py --provider mock
    python scripts/smoke_test_rag_to_llm.py --provider openai

If the Chroma collection does not exist yet, run:

    python -m rag.ingest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from llm.mock_client import MockTriageLLM
from llm.openai_client import create_openai_triage_llm
from llm.schemas import TriageContext
from llm.triage_service import TriageService
from rag.retriever import make_preview, retrieve_chunks


SAMPLE_ISSUE_PATH = PROJECT_ROOT / "data" / "sample_issues" / "sample_issue_001.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test RAG retrieval plus structured triage.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="LLM provider to use. Defaults to mock to avoid token spend.",
    )
    args = parser.parse_args()

    load_dotenv()

    issue_text = SAMPLE_ISSUE_PATH.read_text(encoding="utf-8")
    issue_title = extract_markdown_title(issue_text)

    try:
        retrieved_chunks = retrieve_chunks(issue_text, top_k=5)
    except Exception as exc:
        raise SystemExit(
            "Could not retrieve from Chroma. Run `python -m rag.ingest` first, "
            "then retry `python scripts/smoke_test_rag_to_llm.py`."
        ) from exc

    context = TriageContext(
        repo_name="bug-triage-automation-workflow",
        issue_title=issue_title,
        issue_body=issue_text,
        labels=["bug", "firmware_update", "device", "needs-triage"],
        retrieved_context=[str(chunk["text"]) for chunk in retrieved_chunks],
    )

    service = TriageService(llm_client=create_llm_client(args.provider))
    classification = service.classify_issue(context)
    owner = service.recommend_owner(context, classification)
    rca = service.generate_rca(context, classification, owner)
    comment = service.draft_comment(context, classification, owner, rca)

    print("provider")
    print(json.dumps(args.provider, indent=2))
    print()
    print("retrieved_chunks")
    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk["metadata"]
        print(
            f"{index}. {metadata.get('source')} "
            f"[{metadata.get('doc_type')}] distance={float(chunk['distance']):.4f}"
        )
        print(f"   {make_preview(str(chunk['text']), max_length=180)}")
    print()

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


def create_llm_client(provider: str):
    """Create the requested LLM client for the smoke test."""
    if provider == "mock":
        return MockTriageLLM()
    if provider == "openai":
        return create_openai_triage_llm()
    raise ValueError(f"Unsupported provider: {provider}")


def extract_markdown_title(markdown_text: str) -> str:
    """Extract the first H1 from a Markdown document."""
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return "Untitled issue"


if __name__ == "__main__":
    main()
