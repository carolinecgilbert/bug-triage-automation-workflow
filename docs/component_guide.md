# Component Guide

## `rag/chunking.py`

Owns document splitting.

Main function:

```python
chunk_text(text, chunk_size=1000, chunk_overlap=150)
```

Role in the stack:

```text
large document -> smaller retrievable passages
```

Why it matters:

Good chunking improves retrieval quality. Bad chunking can hide relevant context or return noisy chunks.

## `rag/embeddings.py`

Owns embedding provider selection.

Main factory:

```python
create_embedding_client()
```

Available providers:

- `HashEmbeddingClient`: MVP default, no dependencies, no token cost
- `SentenceTransformersEmbeddingClient`: optional local semantic embeddings
- `OpenAIEmbeddingClient`: optional hosted embeddings

Role in the stack:

```text
text -> vector
```

Why it matters:

The vector representation determines what "similarity" means during retrieval. Production systems usually evaluate multiple embedding models because retrieval quality strongly affects final LLM quality.

## `rag/ingest.py`

Owns indexing source documents into Chroma.

Important functions:

- `load_documents()`
- `infer_doc_type()`
- `build_chunk_records()`
- `make_chunk_id()`
- `recreate_collection()`

Role in the stack:

```text
source files -> metadata -> chunks -> embeddings -> vector store
```

Why it matters:

This is the offline or batch indexing process. In production, this would likely run on a schedule, on document changes, or as part of a repository sync pipeline.

Run with:

```bash
python -m rag.ingest --provider hash
python -m rag.ingest --provider openai
```

## `rag/retriever.py`

Owns query-time retrieval.

Role in the stack:

```text
query -> query vector -> Chroma search -> relevant chunks
```

Why it matters:

This is the runtime path that gives the LLM private, current, task-specific context.

Run with the same provider used for ingestion:

```bash
python -m rag.retriever "firmware update hash mismatch" --provider hash
python -m rag.retriever "firmware update hash mismatch" --provider openai
```

## `llm/base_client.py`

Defines the abstract LLM interface.

Main class:

```python
BaseTriageLLM
```

Role in the stack:

```text
common contract for mock and real reasoning clients
```

Why it matters:

The workflow can depend on the interface instead of a specific provider. This makes it easy to use a mock client during development and switch to OpenAI later. It exposes the four structured operations: classify, recommend owner, generate RCA, and draft comment.

## `llm/schemas.py`

Defines Pydantic models for structured triage input and output.

Important models:

- `TriageContext`
- `ClassificationOutput`
- `OwnerRecommendationOutput`
- `RCAOutput`
- `DraftCommentOutput`

Role in the stack:

```text
raw issue data -> typed workflow state
```

Why it matters:

Typed schemas make LLM output explicit and testable. They also give future LangGraph nodes a clear state shape.

## `llm/triage_service.py`

Provides the application-facing structured triage service.

Main class:

```python
TriageService
```

Methods:

- `classify_issue()`
- `recommend_owner()`
- `generate_rca()`
- `draft_comment()`

Role in the stack:

```text
future graph node -> service method -> configured LLM client
```

Why it matters:

This service is the bridge between orchestration code and model-provider code. LangGraph can call these methods without knowing whether the implementation is mock or OpenAI.

## `llm/mock_client.py`

Provides deterministic triage output with no API call.

Role in the stack:

```text
TriageContext -> deterministic structured triage outputs
```

Why it matters:

The mock client lets you develop orchestration, data flow, and output handling without token cost or network dependency.

## `llm/openai_client.py`

Provides an optional hosted LLM implementation.

Role in the stack:

```text
TriageContext + prompt file -> OpenAI JSON -> Pydantic model
```

Why it matters:

This is the production-style reasoning path. It should be introduced after retrieval, output contracts, and human approval flows are stable.

## `prompts/`

Contains task-specific instructions for hosted LLM calls.

Prompt files:

- `classify_issue.md`
- `recommend_owner.md`
- `generate_rca.md`
- `draft_comment.md`

Role in the stack:

```text
structured task instruction -> hosted LLM response requirements
```

Why it matters:

Keeping prompts outside Python code makes them easier to inspect, revise, and eventually version.

## `scripts/smoke_test_structured_llm.py`

Manual smoke test for the structured LLM flow.

Role in the stack:

```text
sample TriageContext -> all four service methods -> printed JSON
```

Why it matters:

It gives a quick human-readable demo without needing pytest, OpenAI, LangGraph, or FastAPI.

Run with:

```bash
python scripts/smoke_test_structured_llm.py --provider mock
python scripts/smoke_test_structured_llm.py --provider openai
```

`mock` is the default and does not spend tokens. `openai` is an explicit API integration test.

## `tests/test_structured_llm.py`

Automated tests for Step 5 behavior.

Role in the stack:

```text
expected issue examples -> assertions on typed outputs
```

Why it matters:

The tests protect the structured contract while future orchestration code is added.

## `llm/factory.py`

Chooses the LLM provider from environment config.

Current default:

```env
LLM_PROVIDER=mock
```

Role in the stack:

```text
environment config -> concrete LLM client
```

Why it matters:

Provider factories keep the rest of the application clean. Workflow code should not need to know how to instantiate OpenAI or mock clients.

## `agent/state.py`

Defines `TriageState`, the serializable state object passed between LangGraph nodes.

Role in the stack:

```text
workflow input + intermediate outputs -> final API-ready dict
```

Why it matters:

The state uses plain dictionary/list/string/bool fields so it can be returned from FastAPI and stored in Postgres JSON columns without special conversion.

## `agent/nodes.py`

Defines the plain Python node functions used by LangGraph.

Important nodes:

- `prepare_context_node`
- `retrieve_context_node`
- `classify_issue_node`
- `recommend_owner_node`
- `generate_rca_node`
- `draft_comment_node`
- `approval_gate_node`

Role in the stack:

```text
TriageState -> one workflow step -> updated TriageState
```

Why it matters:

Each node does one clear job. Retrieval failures are captured in `state["errors"]` so the workflow can still complete and route to human approval.

## `agent/graph.py`

Builds and runs the LangGraph workflow.

Main functions:

- `build_triage_graph()`
- `run_triage_workflow()`

Role in the stack:

```text
input issue dict -> compiled graph -> final triage state
```

Why it matters:

This is the orchestration layer that Step 7 FastAPI can call directly. It keeps workflow order explicit while leaving business logic in `rag/` and `llm/`.

## `scripts/smoke_test_langgraph.py`

Manual smoke test for the graph workflow.

Role in the stack:

```text
sample issue -> LangGraph workflow -> printed final state sections
```

Why it matters:

It verifies the full controlled workflow from issue input through retrieval, structured triage, and approval gating.

Run with:

```bash
python scripts/smoke_test_langgraph.py --provider mock
python scripts/smoke_test_langgraph.py --provider openai
```

## `tests/test_langgraph_workflow.py`

Automated tests for the LangGraph workflow.

Role in the stack:

```text
issue examples -> graph invocation -> assertions on final state
```

Why it matters:

These tests protect the orchestration layer and ensure it stays mock-only, local, and network-free.

## `src/api/main.py`

Defines the FastAPI application and HTTP routes.

Endpoints:

- `GET /health`
- `POST /triage`
- `GET /triage`
- `GET /triage/{run_id}`
- `POST /feedback`

Role in the stack:

```text
HTTP request -> run_triage_workflow() -> persist result -> structured JSON response
```

Why it matters:

This is the first external interface for the workflow. It intentionally delegates to the existing LangGraph layer instead of duplicating triage logic inside route handlers.

## `src/api/schemas.py`

Defines API request and response models.

Important models:

- `TriageRequest`
- `TriageResponse`
- `TriageRunSummary`
- `StoredTriageRunResponse`
- `FeedbackRequest`
- `FeedbackResponse`
- `HealthResponse`

Role in the stack:

```text
external JSON payload -> validated API model -> graph input state
```

Why it matters:

The API contract is explicit and separate from internal graph state. This keeps future clients, tests, and docs aligned.

## `src/api/dependencies.py`

Creates the requested LLM client for API-triggered workflows.

Role in the stack:

```text
provider field -> MockTriageLLM or OpenAITriageLLM
```

Why it matters:

Provider selection is explicit. `mock` remains the default for safe local testing, while `openai` is available for intentional integration testing.

It also exposes the database session dependency used by FastAPI routes.

## `src/db/database.py`

Configures SQLAlchemy database access.

Role in the stack:

```text
DATABASE_URL -> SQLAlchemy engine -> session per API request
```

Why it matters:

The app defaults to local Docker Postgres but reads `DATABASE_URL`, so the same code can point at AWS RDS, GCP Cloud SQL, or temporary SQLite tests without rewriting the API layer. For the MVP, `init_db()` creates tables directly; production systems should use Alembic migrations.

## `src/db/models.py`

Defines the relational persistence schema.

Tables:

- `triage_runs`
- `retrieved_sources`
- `human_feedback`

Role in the stack:

```text
workflow output + evidence + feedback -> durable database rows
```

Why it matters:

The database becomes the system of record. It allows the project to keep an audit trail of what the agent saw, what it recommended, how long it took, and whether a human approved or corrected it.

## `src/db/repository.py`

Provides database helper functions.

Important functions:

- `create_triage_run()`
- `get_triage_run()`
- `list_triage_runs()`
- `create_retrieved_sources()`
- `create_feedback()`

Role in the stack:

```text
API route -> repository function -> SQLAlchemy model
```

Why it matters:

Repository helpers keep SQLAlchemy details out of the API routes. That makes the API easier to read and gives future UI or eval code a reusable persistence interface.

## `scripts/smoke_test_fastapi.py`

Manual smoke test for the FastAPI layer.

Role in the stack:

```text
TestClient -> /health and /triage -> printed JSON response
```

Why it matters:

It verifies the API contract without requiring a running server process.

Run with:

```bash
python scripts/smoke_test_fastapi.py --provider mock
python scripts/smoke_test_fastapi.py --provider openai
```

## `scripts/smoke_test_persistence.py`

Manual smoke test for stored triage runs and feedback.

Role in the stack:

```text
TestClient -> /triage -> /triage/{run_id} -> /feedback -> printed JSON
```

Why it matters:

It verifies that the HTTP layer, workflow layer, and database layer work together.

Run with:

```bash
docker compose up -d
python scripts/smoke_test_persistence.py --provider mock
python scripts/smoke_test_persistence.py --provider openai
```

## `frontend/streamlit_app.py`

Defines the Streamlit demo UI.

Pages:

- Submit Issue
- Run History
- Run Details / Feedback

Role in the stack:

```text
human demo user -> Streamlit form -> FastAPI HTTP endpoint -> persisted workflow result
```

Why it matters:

This is the customer-facing demo layer. It intentionally communicates only with FastAPI using `requests`; it does not call LangGraph, RAG, LLM, or SQLAlchemy directly. That preserves FastAPI as the backend contract and keeps the UI replaceable.

Run with:

```bash
streamlit run frontend/streamlit_app.py
```

## `scripts/smoke_test_streamlit_api.py`

Manual smoke test for the HTTP endpoints used by Streamlit.

Role in the stack:

```text
requests -> /health -> /triage -> /triage -> /triage/{run_id} -> /feedback
```

Why it matters:

It verifies the frontend's API contract without launching a browser.

Run after starting FastAPI:

```bash
python scripts/smoke_test_streamlit_api.py --provider mock
python scripts/smoke_test_streamlit_api.py --provider openai
```

## `tests/test_api.py`

Automated tests for the FastAPI app.

Role in the stack:

```text
TestClient request -> endpoint response assertions
```

Why it matters:

These tests verify `/health`, `/triage`, default provider behavior, and that the API returns the final triage state.
They also verify that triage runs are persisted, listed, fetched by `run_id`, and can receive human feedback.

## `docker-compose.yml`

Defines local Postgres for development.

Role in the stack:

```text
docker compose up -d -> local Postgres -> FastAPI persistence
```

Why it matters:

Using Postgres locally makes the MVP closer to a deployable application than storing everything in memory. The application still reads `DATABASE_URL`, so moving to managed Postgres later should mainly be a configuration change.

## `.env` And `.env.example`

`.env` contains local runtime configuration and secrets. It should not be committed.

`.env.example` documents expected environment variables and safe placeholder values. It should be committed.

Important current variables:

```env
CHROMA_DB_DIR=chroma_db
CHROMA_COLLECTION_NAME=bug_triage_rag
EMBEDDING_PROVIDER=hash
HASH_EMBEDDING_DIMENSIONS=384
LLM_PROVIDER=mock
API_BASE_URL=http://127.0.0.1:8000
DATABASE_URL=postgresql+psycopg://bugtriage:bugtriage@localhost:5432/bugtriage
```
