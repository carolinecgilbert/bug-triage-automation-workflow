# Bug Triage Automation Workflow Docs

This directory explains the project as it exists after Step 5: RAG ingestion, retrieval, and structured LLM calls.

## Reading Order

1. [Project Progress](project_progress.md)
2. [Architecture Overview](architecture.md)
3. [RAG Pipeline](rag_pipeline.md)
4. [Structured LLM Calls](structured_llm_calls.md)
5. [Component Guide](component_guide.md)
6. [MVP vs Production](mvp_vs_production.md)
7. [Interview Talking Points](interview_talking_points.md)

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
- A smoke script and pytest coverage for the structured LLM flow

The project does not yet include:

- GitHub API ingestion
- FastAPI routes
- LangGraph orchestration
- Frontend UI
- Human approval persistence
- Automated GitHub comments, labels, or assignments
