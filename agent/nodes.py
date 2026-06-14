"""Plain Python node functions for the LangGraph triage workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from llm.mock_client import MockTriageLLM
from llm.schemas import (
    ClassificationOutput,
    OwnerRecommendationOutput,
    RCAOutput,
    TriageContext,
)
from llm.triage_service import TriageService
from rag.retriever import retrieve_chunks

from agent.state import TriageState


NodeFunction = Callable[[TriageState], TriageState]


def build_nodes(triage_service: TriageService | None = None) -> dict[str, NodeFunction]:
    """Build graph node callables bound to a triage service.

    The default uses `MockTriageLLM` so local workflow runs never spend tokens
    unless a caller explicitly passes a different service.
    """
    service = triage_service or TriageService(llm_client=MockTriageLLM())

    return {
        "prepare_context": prepare_context_node,
        "retrieve_context": retrieve_context_node,
        "classify_issue": lambda state: classify_issue_node(state, service),
        "recommend_owner": lambda state: recommend_owner_node(state, service),
        "generate_rca": lambda state: generate_rca_node(state, service),
        "draft_comment": lambda state: draft_comment_node(state, service),
        "approval_gate": approval_gate_node,
    }


def prepare_context_node(state: TriageState) -> TriageState:
    """Normalize optional fields and build the retrieval query."""
    updated = dict(state)
    ensure_list_fields(updated)

    query_parts = [
        updated.get("issue_title", ""),
        updated.get("issue_body", ""),
        " ".join(updated["labels"]),
        " ".join(updated["issue_comments"]),
        " ".join(updated["logs"]),
    ]
    updated["retrieval_query"] = "\n\n".join(part for part in query_parts if part)
    return updated


def retrieve_context_node(state: TriageState) -> TriageState:
    """Retrieve relevant Chroma chunks and store text plus source metadata."""
    updated = dict(state)
    ensure_list_fields(updated)

    query = updated.get("retrieval_query") or updated.get("issue_body") or updated.get("issue_title", "")

    try:
        chunks = retrieve_chunks(query, top_k=5)
    except Exception as exc:
        updated["retrieved_context"] = []
        updated["retrieved_sources"] = []
        updated["errors"].append(f"retrieval failed: {exc}")
        return updated

    updated["retrieved_context"] = [str(chunk.get("text", "")) for chunk in chunks]
    updated["retrieved_sources"] = [
        {
            "source": metadata.get("source"),
            "doc_type": metadata.get("doc_type"),
            "distance": chunk.get("distance"),
            "metadata": metadata,
        }
        for chunk in chunks
        for metadata in [dict(chunk.get("metadata") or {})]
    ]
    return updated


def classify_issue_node(state: TriageState, triage_service: TriageService | None = None) -> TriageState:
    """Classify the issue and store a serializable result."""
    updated = dict(state)
    ensure_list_fields(updated)
    service = triage_service or TriageService(llm_client=MockTriageLLM())

    try:
        result = service.classify_issue(build_triage_context(updated))
        updated["classification"] = result.model_dump()
    except Exception as exc:
        updated["errors"].append(f"classification failed: {exc}")

    return updated


def recommend_owner_node(state: TriageState, triage_service: TriageService | None = None) -> TriageState:
    """Recommend an owning team and store a serializable result."""
    updated = dict(state)
    ensure_list_fields(updated)
    service = triage_service or TriageService(llm_client=MockTriageLLM())

    try:
        classification = ClassificationOutput.model_validate(updated.get("classification", {}))
        result = service.recommend_owner(build_triage_context(updated), classification)
        updated["owner_recommendation"] = result.model_dump()
    except Exception as exc:
        updated["errors"].append(f"owner recommendation failed: {exc}")

    return updated


def generate_rca_node(state: TriageState, triage_service: TriageService | None = None) -> TriageState:
    """Generate RCA output and store a serializable result."""
    updated = dict(state)
    ensure_list_fields(updated)
    service = triage_service or TriageService(llm_client=MockTriageLLM())

    try:
        classification = ClassificationOutput.model_validate(updated.get("classification", {}))
        owner = OwnerRecommendationOutput.model_validate(updated.get("owner_recommendation", {}))
        result = service.generate_rca(build_triage_context(updated), classification, owner)
        updated["rca"] = result.model_dump()
    except Exception as exc:
        updated["errors"].append(f"RCA generation failed: {exc}")

    return updated


def draft_comment_node(state: TriageState, triage_service: TriageService | None = None) -> TriageState:
    """Draft a GitHub comment and store a serializable result."""
    updated = dict(state)
    ensure_list_fields(updated)
    service = triage_service or TriageService(llm_client=MockTriageLLM())

    try:
        classification = ClassificationOutput.model_validate(updated.get("classification", {}))
        owner = OwnerRecommendationOutput.model_validate(updated.get("owner_recommendation", {}))
        rca = RCAOutput.model_validate(updated.get("rca", {}))
        result = service.draft_comment(build_triage_context(updated), classification, owner, rca)
        updated["draft_comment"] = result.model_dump()
    except Exception as exc:
        updated["errors"].append(f"draft comment failed: {exc}")

    return updated


def approval_gate_node(state: TriageState) -> TriageState:
    """Set approval fields based on confidence, severity, comment, and errors."""
    updated = dict(state)
    ensure_list_fields(updated)

    classification = dict(updated.get("classification") or {})
    owner = dict(updated.get("owner_recommendation") or {})
    rca = dict(updated.get("rca") or {})
    draft_comment = dict(updated.get("draft_comment") or {})

    reasons: list[str] = []
    if draft_comment.get("approval_required") is True:
        reasons.append("draft comment requires human approval")
    if str(classification.get("severity", "")).lower() in {"high", "sev1"}:
        reasons.append("classification severity is high")
    if float_or_default(classification.get("confidence"), 0.0) < 0.75:
        reasons.append("classification confidence is below 0.75")
    if float_or_default(owner.get("confidence"), 0.0) < 0.75:
        reasons.append("owner confidence is below 0.75")
    if float_or_default(rca.get("confidence"), 0.0) < 0.70:
        reasons.append("RCA confidence is below 0.70")
    if updated["errors"]:
        reasons.append("workflow errors are present")

    updated["approval_required"] = bool(reasons)
    updated["approval_reason"] = "; ".join(reasons) if reasons else "No approval gate conditions were triggered."
    return updated


def build_triage_context(state: TriageState) -> TriageContext:
    """Build the Pydantic triage context from graph state."""
    return TriageContext(
        issue_title=state.get("issue_title", ""),
        issue_body=state.get("issue_body", ""),
        issue_comments=list(state.get("issue_comments", [])),
        labels=list(state.get("labels", [])),
        retrieved_context=list(state.get("retrieved_context", [])),
        logs=list(state.get("logs", [])),
        repo_name=state.get("repo_name"),
    )


def ensure_list_fields(state: dict[str, Any]) -> None:
    """Ensure optional list fields exist in state."""
    for field in [
        "issue_comments",
        "labels",
        "logs",
        "retrieved_context",
        "retrieved_sources",
        "errors",
    ]:
        state.setdefault(field, [])


def float_or_default(value: object, default: float) -> float:
    """Convert a value to float without letting approval logic crash."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

