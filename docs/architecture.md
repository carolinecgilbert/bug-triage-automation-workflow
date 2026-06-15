# Architecture Overview

## Project Goal

`bug-triage-automation-workflow` is an Agentic Engineering Operations Assistant. The end-state system will analyze GitHub issues, retrieve relevant repository and operational context, recommend ownership, generate root cause hypotheses, suggest remediation steps, and require human approval before taking action.

The current implementation reaches Step 10: the data foundation, RAG ingestion/retrieval, structured LLM calls, LangGraph orchestration, FastAPI wrapper, Postgres persistence, Streamlit demo UI, and offline eval harness are in place.

## Current MVP Architecture

```text
Offline ingestion path:

data/
  docs, historical issues, code summaries, sample issues, logs, ownership
        |
        v
rag.ingest
  load files -> infer doc_type -> chunk text -> embed chunks
        |
        v
Chroma vector store
  chunk text + metadata + vectors

Runtime application path:

Streamlit frontend
  submit issue + view runs + submit feedback
        |
        v
src.api
  /health, /triage, /triage/{run_id}, /feedback
        |
        v
rag.retriever
  embed query -> nearest-neighbor search -> relevant context
        |
        v
agent.graph
  prepare context -> retrieve -> classify -> owner -> RCA -> comment -> approval gate
        |
        v
llm.TriageService
  classify -> recommend owner -> generate RCA -> draft comment
        |
        v
BaseTriageLLM implementation
  MockTriageLLM now, OpenAITriageLLM later
        |
        v
Postgres via SQLAlchemy
  triage runs + retrieved sources + human feedback

Offline evaluation path:

evals/test_cases.json
        |
        v
evals.runner
  run existing LangGraph workflow for each labeled case
        |
        v
evals.metrics
  score component, owner, issue type, approval, retrieval, latency
        |
        v
evals/results/latest_results.json
```

## Main Runtime Paths

### Ingestion Path

Run:

```bash
python -m rag.ingest --provider hash
```

This reads source data from `data/`, chunks it, generates vectors, and writes a Chroma collection.

### Retrieval Path

Run:

```bash
python -m rag.retriever "firmware update hash mismatch on hw-b2" --provider hash
```

This embeds the query using the same embedding provider, searches Chroma, and prints the top matching chunks.

### Structured Reasoning Path

Run:

```bash
python scripts/smoke_test_structured_llm.py
```

This runs the four structured triage calls with `MockTriageLLM`:

```text
classify_issue
  -> recommend_owner
  -> generate_rca
  -> draft_comment
```

Each step returns a Pydantic model, which is the shape future LangGraph nodes will pass through graph state.

### LangGraph Workflow Path

Run:

```bash
python scripts/smoke_test_langgraph.py --provider mock
```

This runs the current controlled workflow:

```text
START
  -> prepare_context
  -> retrieve_context
  -> classify_issue
  -> recommend_owner
  -> generate_rca
  -> draft_comment
  -> approval_gate
  -> END
```

The approval gate only sets `approval_required` and `approval_reason`. Actual human approval persistence and UI handling are intentionally deferred.

### FastAPI Path

Run an in-process smoke test:

```bash
python scripts/smoke_test_fastapi.py --provider mock
```

Start a local server:

```bash
uvicorn src.api.main:app --reload
```

Endpoints:

```text
GET /health
POST /triage
GET /triage
GET /triage/{run_id}
POST /feedback
```

`POST /triage` accepts a ticket ID, title, description, provider, and approval preference. It calls the existing LangGraph workflow and returns the final state as JSON.

### Streamlit Path

Start the demo UI:

```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit app calls FastAPI over HTTP using `API_BASE_URL`. It does not import LangGraph, RAG, LLM, or database modules directly.

Pages:

- Submit Issue
- Run History
- Run Details / Feedback

This keeps the frontend as a replaceable client layer. A future React app, Slack bot, or internal portal could use the same FastAPI endpoints.

### Persistence Path

Run local Postgres:

```bash
docker compose up -d
```

Run a persistence smoke test:

```bash
python scripts/smoke_test_persistence.py --provider mock
```

The persistence layer stores:

- issue input and generated `run_id`
- final triage state from LangGraph
- provider, status, latency, and approval fields
- retrieved RAG source metadata and short previews
- human feedback submitted after review

Chroma and Postgres serve different jobs. Chroma is the vector store for retrieval. Postgres is the application system of record for workflow history, auditability, and future UI views.

Inspect the database:

```bash
docker compose exec postgres psql -U bugtriage -d bugtriage
```

Core tables:

```text
triage_runs       one row per agent workflow run
retrieved_sources RAG evidence retrieved for a run
human_feedback    reviewer feedback attached to a run
```

### Eval Path

Run:

```bash
python scripts/run_evals.py --provider mock
```

This loads labeled cases from `evals/test_cases.json`, runs each case through the same LangGraph workflow used by the API, scores the final state, prints summary metrics, and writes JSON results to `evals/results/latest_results.json`.

Current metrics:

- component accuracy
- owner recommendation accuracy
- issue type accuracy
- approval routing accuracy
- retrieval hit rate
- latency

Classification and ownership policy:

- Classification outputs are constrained to known values: `bug` or `unknown` for issue type, and known component names or `unknown` for component.
- If evidence is weak, the workflow should prefer `unknown` and route ownership to `needs-human-triage`.
- If multiple components are plausible, the workflow should choose a primary component only when one direct failure signal is clearly strongest and confidence is at least `0.75`.
- Otherwise, ambiguous issues should route to human triage.

The eval harness does not use LLM-as-judge yet. RCA and comment quality are intentionally left for a later production-grade eval step.

## Separation Of Concerns

`data/` is the knowledge base. It contains the raw text that retrieval should search.

`rag/` owns retrieval infrastructure. It does not decide final triage answers; it prepares context.

`agent/` owns workflow orchestration. It uses LangGraph to pass serializable state through clear nodes.

`llm/` owns structured reasoning. It defines schemas, a service layer, a base client interface, and provider implementations.

`prompts/` owns hosted LLM task instructions for classification, owner recommendation, RCA generation, and comment drafting.

`src/api/` owns HTTP transport. It validates API payloads and delegates workflow execution to `agent.graph`.

`src/db/` owns relational persistence. It stores runs, retrieved evidence, and human feedback using SQLAlchemy.

`frontend/` owns the demo UI. It is intentionally a thin HTTP client over FastAPI.

`evals/` owns offline quality checks. It uses labeled examples and the existing graph runner to measure workflow behavior.

`docs/` explains how the system works and how to discuss the architecture.

## Why This Design Matters

The system separates retrieval from reasoning. Retrieval finds relevant evidence. The LLM uses that evidence to form recommendations. This mirrors production RAG systems, where the LLM does not permanently know private company context; the application fetches that context at runtime and injects it into the prompt.

The system also separates orchestration from model calls. LangGraph coordinates state transitions, while `TriageService` owns model-facing business logic. This keeps the graph explicit without turning the project into a complex multi-agent system.

The system separates retrieval storage from application storage. Chroma stores vectorized chunks optimized for similarity search. Postgres stores durable workflow records optimized for querying, audit, feedback, and future product surfaces.

The system separates frontend UX from backend workflow execution. Streamlit demonstrates the product experience, while FastAPI remains the stable service boundary for running triage and storing feedback.

The system separates demos from evaluation. The Streamlit app shows the workflow, while the offline eval harness measures whether workflow changes improve or regress labeled behavior.
