"""FastAPI app for the bug triage workflow."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from agent.graph import run_triage_workflow
from llm.triage_service import TriageService
from src.api.dependencies import create_llm_client, get_db
from src.api.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    StoredTriageRunResponse,
    TriageRequest,
    TriageResponse,
    TriageRunSummary,
)
from src.db.database import init_db
from src.db.repository import (
    create_feedback,
    create_retrieved_sources,
    create_triage_run,
    get_triage_run,
    list_triage_runs,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize persistence tables on application startup."""
    init_db()
    yield


app = FastAPI(
    title="Bug Triage Automation Workflow",
    version="0.1.0",
    description="API wrapper around the LangGraph bug triage workflow.",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health."""
    return HealthResponse(status="ok", service="bug-triage-automation-workflow")


@app.post("/triage", response_model=TriageResponse)
def triage_issue(
    request: TriageRequest,
    db: Session = Depends(get_db),
) -> TriageResponse:
    """Run the existing LangGraph triage workflow for one issue."""
    run_id = f"run_{uuid4().hex}"
    started_at = datetime.now(timezone.utc)
    timer_start = perf_counter()
    input_state = {
        "run_id": run_id,
        "ticket_id": request.ticket_id,
        "issue_title": request.title,
        "issue_body": request.description,
        "issue_comments": [],
        "labels": [],
        "logs": [],
        "repo_name": None,
    }
    service = TriageService(llm_client=create_llm_client(request.provider))
    status = "completed"
    error_message = None

    try:
        final_state = run_triage_workflow(input_state, triage_service=service)
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        final_state = {
            **input_state,
            "errors": [f"workflow failed: {exc}"],
            "approval_required": True,
            "approval_reason": "workflow failed",
        }

    if request.require_approval and final_state.get("approval_required") is False:
        final_state["approval_required"] = True
        final_state["approval_reason"] = "API request requires human approval."

    if final_state.get("errors") and status != "failed":
        status = "completed_with_errors"

    completed_at = datetime.now(timezone.utc)
    latency_ms = int((perf_counter() - timer_start) * 1000)
    retrieved_sources = add_source_previews(final_state)

    create_triage_run(
        db,
        run_id=run_id,
        ticket_id=request.ticket_id,
        provider=request.provider,
        title=request.title,
        description=request.description,
        repo_name=final_state.get("repo_name"),
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        latency_ms=latency_ms,
        approval_required=bool(final_state.get("approval_required")),
        approval_reason=final_state.get("approval_reason"),
        final_state=final_state,
        error_message=error_message,
    )
    create_retrieved_sources(db, run_id=run_id, sources=retrieved_sources)

    return TriageResponse(
        run_id=run_id,
        status=status,
        approval_required=bool(final_state.get("approval_required")),
        approval_reason=final_state.get("approval_reason"),
        final_state=final_state,
        ticket_id=request.ticket_id,
        provider=request.provider,
        require_approval=request.require_approval,
    )


@app.get("/triage/{run_id}", response_model=StoredTriageRunResponse)
def get_stored_triage_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> StoredTriageRunResponse:
    """Return one persisted triage run."""
    run = get_triage_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="triage run not found")
    return StoredTriageRunResponse(**run)


@app.get("/triage", response_model=list[TriageRunSummary])
def list_stored_triage_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TriageRunSummary]:
    """Return recent persisted triage runs."""
    return [TriageRunSummary(**run) for run in list_triage_runs(db, limit=limit)]


@app.post("/feedback", response_model=FeedbackResponse)
def store_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """Store human feedback for a triage run."""
    if get_triage_run(db, request.run_id) is None:
        raise HTTPException(status_code=404, detail="triage run not found")

    feedback = create_feedback(
        db,
        run_id=request.run_id,
        approved=request.approved,
        correct_owner=request.correct_owner,
        useful_rca=request.useful_rca,
        useful_comment=request.useful_comment,
        notes=request.notes,
    )
    return FeedbackResponse(
        feedback_id=feedback["id"],
        run_id=request.run_id,
        stored=True,
    )


def add_source_previews(final_state: dict) -> list[dict]:
    """Attach text previews to retrieved source metadata for persistence."""
    sources = list(final_state.get("retrieved_sources") or [])
    contexts = list(final_state.get("retrieved_context") or [])
    enriched_sources = []

    for index, source in enumerate(sources):
        source_copy = dict(source)
        source_text = contexts[index] if index < len(contexts) else ""
        source_copy["preview"] = " ".join(str(source_text).split())[:300]
        enriched_sources.append(source_copy)

    return enriched_sources
