"""Repository helpers for triage persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.db.models import HumanFeedback, RetrievedSource, TriageRun


def create_triage_run(
    db: Session,
    *,
    run_id: str,
    ticket_id: str | None,
    provider: str,
    title: str,
    description: str,
    repo_name: str | None,
    status: str,
    started_at: datetime,
    completed_at: datetime | None,
    latency_ms: int | None,
    approval_required: bool,
    approval_reason: str | None,
    final_state: dict[str, Any],
    error_message: str | None = None,
) -> dict[str, Any]:
    """Create and return a triage run record."""
    run = TriageRun(
        run_id=run_id,
        ticket_id=ticket_id,
        provider=provider,
        title=title,
        description=description,
        repo_name=repo_name,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        latency_ms=latency_ms,
        approval_required=approval_required,
        approval_reason=approval_reason,
        final_state_json=final_state,
        error_message=error_message,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return triage_run_to_dict(run)


def get_triage_run(db: Session, run_id: str) -> dict[str, Any] | None:
    """Return one triage run with retrieved sources and feedback."""
    run = db.scalar(select(TriageRun).where(TriageRun.run_id == run_id))
    if run is None:
        return None

    result = triage_run_to_dict(run)
    result["retrieved_sources"] = get_retrieved_sources(db, run_id)
    result["feedback"] = get_feedback_for_run(db, run_id)
    return result


def list_triage_runs(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    """Return recent triage run summaries."""
    bounded_limit = min(max(limit, 1), 100)
    runs = db.scalars(
        select(TriageRun)
        .order_by(desc(TriageRun.started_at))
        .limit(bounded_limit)
    ).all()
    return [triage_run_summary_to_dict(run) for run in runs]


def create_retrieved_sources(
    db: Session,
    *,
    run_id: str,
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Persist retrieved RAG source metadata for a run."""
    rows = []
    for source in sources:
        metadata = dict(source.get("metadata") or {})
        row = RetrievedSource(
            run_id=run_id,
            source=source.get("source"),
            doc_type=source.get("doc_type"),
            distance=source.get("distance"),
            preview=source.get("preview"),
            metadata_json=metadata,
        )
        rows.append(row)

    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return [retrieved_source_to_dict(row) for row in rows]


def get_retrieved_sources(db: Session, run_id: str) -> list[dict[str, Any]]:
    """Return retrieved sources for a run."""
    rows = db.scalars(select(RetrievedSource).where(RetrievedSource.run_id == run_id)).all()
    return [retrieved_source_to_dict(row) for row in rows]


def create_feedback(
    db: Session,
    *,
    run_id: str,
    approved: bool,
    correct_owner: bool | None = None,
    useful_rca: bool | None = None,
    useful_comment: bool | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create and return human feedback for a run."""
    feedback = HumanFeedback(
        run_id=run_id,
        approved=approved,
        correct_owner=correct_owner,
        useful_rca=useful_rca,
        useful_comment=useful_comment,
        notes=notes,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback_to_dict(feedback)


def get_feedback_for_run(db: Session, run_id: str) -> list[dict[str, Any]]:
    """Return all feedback rows for a run."""
    rows = db.scalars(select(HumanFeedback).where(HumanFeedback.run_id == run_id)).all()
    return [feedback_to_dict(row) for row in rows]


def triage_run_to_dict(run: TriageRun) -> dict[str, Any]:
    """Serialize a triage run model."""
    return {
        "run_id": run.run_id,
        "ticket_id": run.ticket_id,
        "provider": run.provider,
        "title": run.title,
        "description": run.description,
        "repo_name": run.repo_name,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "latency_ms": run.latency_ms,
        "approval_required": run.approval_required,
        "approval_reason": run.approval_reason,
        "final_state": run.final_state_json,
        "error_message": run.error_message,
    }


def triage_run_summary_to_dict(run: TriageRun) -> dict[str, Any]:
    """Serialize a triage run summary."""
    return {
        "run_id": run.run_id,
        "ticket_id": run.ticket_id,
        "title": run.title,
        "status": run.status,
        "latency_ms": run.latency_ms,
        "approval_required": run.approval_required,
        "started_at": run.started_at,
    }


def retrieved_source_to_dict(source: RetrievedSource) -> dict[str, Any]:
    """Serialize a retrieved source model."""
    return {
        "id": source.id,
        "run_id": source.run_id,
        "source": source.source,
        "doc_type": source.doc_type,
        "distance": source.distance,
        "preview": source.preview,
        "metadata": source.metadata_json,
    }


def feedback_to_dict(feedback: HumanFeedback) -> dict[str, Any]:
    """Serialize a feedback model."""
    return {
        "id": feedback.id,
        "run_id": feedback.run_id,
        "approved": feedback.approved,
        "correct_owner": feedback.correct_owner,
        "useful_rca": feedback.useful_rca,
        "useful_comment": feedback.useful_comment,
        "notes": feedback.notes,
        "created_at": feedback.created_at,
    }

