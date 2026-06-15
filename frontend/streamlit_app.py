"""Streamlit demo UI for the bug triage workflow.

The frontend intentionally talks to FastAPI over HTTP. It does not import or
call LangGraph, RAG, or LLM code directly.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 20


def api_get(path: str) -> tuple[dict[str, Any] | list[dict[str, Any]] | None, str | None]:
    """Call a FastAPI GET endpoint and return JSON or an error string."""
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return parse_response(response)
    except requests.RequestException as exc:
        return None, f"FastAPI is not reachable. Run: uvicorn src.api.main:app --reload. Details: {exc}"


def api_post(path: str, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Call a FastAPI POST endpoint and return JSON or an error string."""
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        data, error = parse_response(response)
        if isinstance(data, list):
            return None, "Expected an object response but received a list."
        return data, error
    except requests.RequestException as exc:
        return None, f"FastAPI is not reachable. Run: uvicorn src.api.main:app --reload. Details: {exc}"


def parse_response(response: requests.Response) -> tuple[Any | None, str | None]:
    """Parse an HTTP response from the API."""
    try:
        data = response.json()
    except ValueError:
        data = None

    if not response.ok:
        detail = data.get("detail") if isinstance(data, dict) else response.text
        return None, f"API returned {response.status_code}: {detail}"

    if data is None:
        return None, "API returned a non-JSON response."

    return data, None


def check_api_health() -> None:
    """Show FastAPI reachability in the sidebar."""
    data, error = api_get("/health")
    st.sidebar.caption(f"API: `{API_BASE_URL}`")
    if error:
        st.sidebar.error("FastAPI unavailable")
        st.sidebar.caption("Run: `uvicorn src.api.main:app --reload`")
        return

    service = data.get("service", "unknown") if isinstance(data, dict) else "unknown"
    st.sidebar.success(f"API reachable: {service}")


def display_triage_result(result: dict[str, Any]) -> None:
    """Render a triage response or stored run detail."""
    final_state = result.get("final_state") or {}

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Status", str(result.get("status", "unknown")))
    col_b.metric("Approval Required", str(result.get("approval_required", "unknown")))
    col_c.metric("Latency ms", str(result.get("latency_ms", "n/a")))

    if result.get("run_id"):
        st.code(result["run_id"], language="text")

    approval_reason = result.get("approval_reason")
    if approval_reason:
        st.info(f"Approval reason: {approval_reason}")

    classification = final_state.get("classification")
    owner = final_state.get("owner_recommendation")
    rca = final_state.get("rca")
    draft_comment = final_state.get("draft_comment")
    retrieved_sources = final_state.get("retrieved_sources") or result.get("retrieved_sources") or []

    if classification:
        st.subheader("Classification")
        st.json(classification)

    if owner:
        st.subheader("Owner Recommendation")
        st.json(owner)

    if rca:
        st.subheader("Root Cause Hypothesis")
        st.json(rca)

    if draft_comment:
        st.subheader("Draft Comment")
        comment = draft_comment.get("comment") if isinstance(draft_comment, dict) else None
        if comment:
            st.markdown(comment)
        with st.expander("Draft comment JSON"):
            st.json(draft_comment)

    if retrieved_sources:
        st.subheader("Retrieved Sources")
        for index, source in enumerate(retrieved_sources, start=1):
            label = source.get("source") or source.get("filename") or f"Source {index}"
            doc_type = source.get("doc_type", "unknown")
            with st.expander(f"{index}. {label} ({doc_type})"):
                preview = source.get("preview")
                if preview:
                    st.write(preview)
                st.json(source)

    with st.expander("Raw final_state JSON"):
        st.json(final_state)


def submit_issue_page() -> None:
    """Submit a new issue for triage through FastAPI."""
    st.header("Submit Issue")
    st.caption("This demo shows a controlled agentic workflow for GitHub-style issue triage.")
    st.caption("The UI calls FastAPI, which invokes LangGraph and persists results to Postgres.")

    with st.form("submit_issue_form"):
        ticket_id = st.text_input("Ticket ID", value="BUG-DEMO-001")
        title = st.text_input("Title", value="Firmware update fails with hash mismatch")
        description = st.text_area(
            "Description",
            value=(
                "Devices download the OTA package but fail integrity validation before install. "
                "The logs mention manifest hash mismatch and failed_integrity_check."
            ),
            height=160,
        )
        provider = st.selectbox("Provider", options=["mock", "openai"], index=0)
        require_approval = st.checkbox("Require human approval", value=True)
        submitted = st.form_submit_button("Run triage")

    if not submitted:
        return

    payload = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
        "provider": provider,
        "require_approval": require_approval,
    }
    result, error = api_post("/triage", payload)
    if error:
        st.error(error)
        return

    run_id = result.get("run_id")
    if run_id:
        st.session_state["selected_run_id"] = run_id
    st.success("Triage run completed and persisted.")
    display_triage_result(result)


def run_history_page() -> None:
    """List persisted triage runs."""
    st.header("Run History")
    st.caption("Recent workflow runs persisted by FastAPI into Postgres.")

    data, error = api_get("/triage")
    if error:
        st.error(error)
        return

    runs = data if isinstance(data, list) else []
    if not runs:
        st.info("No persisted triage runs found yet.")
        return

    st.dataframe(
        runs,
        column_order=[
            "run_id",
            "ticket_id",
            "title",
            "status",
            "approval_required",
            "latency_ms",
            "started_at",
        ],
        use_container_width=True,
        hide_index=True,
    )

    run_ids = [run["run_id"] for run in runs if run.get("run_id")]
    selected = st.selectbox("Select a run ID", options=run_ids)
    manual_run_id = st.text_input("Or paste a run ID", value=selected or "")

    if st.button("Use selected run"):
        if not manual_run_id:
            st.warning("Choose or paste a run_id first.")
            return
        st.session_state["selected_run_id"] = manual_run_id
        st.success("Run selected. Open Run Details / Feedback to inspect it.")


def run_details_page() -> None:
    """Display one persisted run and submit feedback."""
    st.header("Run Details / Feedback")
    default_run_id = st.session_state.get("selected_run_id", "")
    run_id = st.text_input("Run ID", value=default_run_id)

    if st.button("Load run"):
        if not run_id.strip():
            st.warning("Enter a run_id to load.")
        else:
            st.session_state["selected_run_id"] = run_id.strip()

    selected_run_id = st.session_state.get("selected_run_id")
    if not selected_run_id:
        st.info("Select a run from Run History or paste a run_id.")
        return

    data, error = api_get(f"/triage/{selected_run_id}")
    if error:
        st.error(error)
        return

    if not isinstance(data, dict):
        st.error("Malformed response: expected a JSON object.")
        return

    st.subheader(data.get("title", "Untitled run"))
    if data.get("description"):
        st.write(data["description"])

    display_triage_result(data)
    display_existing_feedback(data.get("feedback") or [])
    feedback_form(selected_run_id)


def display_existing_feedback(feedback: list[dict[str, Any]]) -> None:
    """Render existing feedback rows for a run."""
    st.subheader("Existing Feedback")
    if not feedback:
        st.info("No feedback has been submitted for this run yet.")
        return

    st.dataframe(feedback, use_container_width=True, hide_index=True)


def feedback_form(run_id: str) -> None:
    """Submit human feedback for a run."""
    st.subheader("Submit Feedback")
    with st.form("feedback_form"):
        approved = st.checkbox("Approved", value=True)
        correct_owner = st.checkbox("Correct owner", value=True)
        useful_rca = st.checkbox("Useful RCA", value=True)
        useful_comment = st.checkbox("Useful comment", value=True)
        notes = st.text_area("Notes", value="", height=120)
        submitted = st.form_submit_button("Submit feedback")

    if not submitted:
        return

    payload = {
        "run_id": run_id,
        "approved": approved,
        "correct_owner": correct_owner,
        "useful_rca": useful_rca,
        "useful_comment": useful_comment,
        "notes": notes or None,
    }
    result, error = api_post("/feedback", payload)
    if error:
        st.error(error)
        return

    st.success(f"Feedback stored with id {result.get('feedback_id')}.")


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(
        page_title="Bug Triage Workflow",
        layout="wide",
    )
    st.title("Bug Triage Automation Workflow")
    st.caption("Customer-facing demo layer for the agentic issue triage workflow.")

    check_api_health()

    page = st.sidebar.radio(
        "Navigation",
        options=["Submit Issue", "Run History", "Run Details / Feedback"],
    )

    if page == "Submit Issue":
        submit_issue_page()
    elif page == "Run History":
        run_history_page()
    else:
        run_details_page()


if __name__ == "__main__":
    main()
