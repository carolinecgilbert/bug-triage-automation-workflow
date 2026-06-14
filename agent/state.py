"""Serializable workflow state for the triage graph."""

from __future__ import annotations

from typing import Any, TypedDict


class TriageState(TypedDict, total=False):
    """State passed between LangGraph nodes.

    Values are kept JSON-serializable so the final state can later be returned
    from FastAPI and stored in SQLite without special conversion.
    """

    issue_title: str
    issue_body: str
    issue_comments: list[str]
    labels: list[str]
    logs: list[str]
    repo_name: str | None
    retrieval_query: str
    retrieved_context: list[str]
    retrieved_sources: list[dict[str, Any]]
    classification: dict[str, Any]
    owner_recommendation: dict[str, Any]
    rca: dict[str, Any]
    draft_comment: dict[str, Any]
    approval_required: bool
    approval_reason: str
    errors: list[str]

