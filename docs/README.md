# Bug Triage Automation Workflow Docs

This directory explains the project as it exists after Step 10: RAG ingestion, retrieval, structured LLM calls, LangGraph orchestration, FastAPI, Postgres persistence, Streamlit UI, and offline evals.

## Reading Order

1. [Project Progress](project_progress.md)
2. [Architecture Overview](architecture.md)
3. [RAG Pipeline](rag_pipeline.md)
4. [Running The App](running_the_app.md)
5. [Structured LLM Calls](structured_llm_calls.md)
6. [Component Guide](component_guide.md)
7. [MVP vs Production](mvp_vs_production.md)
8. [Interview Talking Points](interview_talking_points.md)

## Current Scope

The project currently supports:

- A realistic fake knowledge base under `data/`
- Document loading and metadata tagging
- Character-based chunking
- Local vector generation with a dependency-free hash embedder
- Chroma vector storage
- Command-line retrieval
- Pydantic schemas for structured issue triage outputs
- A `TriageService` with `classify_issue`, `recommend_owner`, `generate_rca`, and `draft_comment`
- A mock LLM reasoning layer behind an abstract base client
- Optional provider paths for OpenAI embeddings and OpenAI LLM reasoning
- Prompt files for hosted structured LLM calls
- LangGraph workflow orchestration with an approval gate
- FastAPI endpoints for health checks, triage, run lookup, run listing, and feedback
- Postgres persistence through SQLAlchemy
- Streamlit demo UI over the FastAPI API
- Offline eval harness with labeled cases and metrics
- Smoke scripts and pytest coverage for structured LLM, LangGraph, FastAPI, persistence, frontend API contract, and eval paths
- A local runbook for starting Postgres, exercising the API, and inspecting persisted tables

The project does not yet include:

- GitHub API ingestion
- Automated GitHub comments, labels, or assignments
