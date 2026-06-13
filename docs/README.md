# Bug Triage Automation Workflow Docs

This directory explains the project as it exists after Step 3: RAG ingestion, retrieval, and MVP LLM reasoning scaffolding.

## Reading Order

1. [Architecture Overview](architecture.md)
2. [RAG Pipeline](rag_pipeline.md)
3. [Component Guide](component_guide.md)
4. [MVP vs Production](mvp_vs_production.md)
5. [Interview Talking Points](interview_talking_points.md)

## Current Scope

The project currently supports:

- A realistic fake knowledge base under `data/`
- Document loading and metadata tagging
- Character-based chunking
- Local vector generation with a dependency-free hash embedder
- Chroma vector storage
- Command-line retrieval
- A mock LLM reasoning layer behind an abstract base client
- Optional provider paths for OpenAI embeddings and OpenAI LLM reasoning

The project does not yet include:

- GitHub API ingestion
- FastAPI routes
- LangGraph orchestration
- Frontend UI
- Human approval persistence
- Automated GitHub comments, labels, or assignments

