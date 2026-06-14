"""FastAPI app for the bug triage workflow."""

from __future__ import annotations

from fastapi import FastAPI

from agent.graph import run_triage_workflow
from llm.triage_service import TriageService
from src.api.dependencies import create_llm_client
from src.api.schemas import HealthResponse, TriageRequest, TriageResponse


app = FastAPI(
    title="Bug Triage Automation Workflow",
    version="0.1.0",
    description="API wrapper around the LangGraph bug triage workflow.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health."""
    return HealthResponse(status="ok", service="bug-triage-automation-workflow")


@app.post("/triage", response_model=TriageResponse)
def triage_issue(request: TriageRequest) -> TriageResponse:
    """Run the existing LangGraph triage workflow for one issue."""
    input_state = {
        "ticket_id": request.ticket_id,
        "issue_title": request.title,
        "issue_body": request.description,
        "issue_comments": [],
        "labels": [],
        "logs": [],
        "repo_name": None,
    }
    service = TriageService(llm_client=create_llm_client(request.provider))
    final_state = run_triage_workflow(input_state, triage_service=service)

    if request.require_approval and final_state.get("approval_required") is False:
        final_state["approval_required"] = True
        final_state["approval_reason"] = "API request requires human approval."

    return TriageResponse(
        ticket_id=request.ticket_id,
        provider=request.provider,
        require_approval=request.require_approval,
        final_state=final_state,
    )

