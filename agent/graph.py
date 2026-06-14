"""LangGraph workflow for issue triage."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.nodes import build_nodes
from agent.state import TriageState
from llm.triage_service import TriageService


def build_triage_graph(triage_service: TriageService | None = None):
    """Build and compile the linear triage workflow graph."""
    nodes = build_nodes(triage_service=triage_service)
    graph = StateGraph(TriageState)

    graph.add_node("prepare_context", nodes["prepare_context"])
    graph.add_node("retrieve_context", nodes["retrieve_context"])
    graph.add_node("classify_issue", nodes["classify_issue"])
    graph.add_node("recommend_owner", nodes["recommend_owner"])
    graph.add_node("generate_rca", nodes["generate_rca"])
    graph.add_node("draft_comment", nodes["draft_comment"])
    graph.add_node("approval_gate", nodes["approval_gate"])

    graph.add_edge(START, "prepare_context")
    graph.add_edge("prepare_context", "retrieve_context")
    graph.add_edge("retrieve_context", "classify_issue")
    graph.add_edge("classify_issue", "recommend_owner")
    graph.add_edge("recommend_owner", "generate_rca")
    graph.add_edge("generate_rca", "draft_comment")
    graph.add_edge("draft_comment", "approval_gate")
    graph.add_edge("approval_gate", END)

    return graph.compile()


def run_triage_workflow(
    input_state: dict,
    triage_service: TriageService | None = None,
) -> dict:
    """Run the compiled triage workflow and return a plain dict state."""
    graph = build_triage_graph(triage_service=triage_service)
    final_state = graph.invoke(input_state)
    return dict(final_state)

