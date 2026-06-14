# Architecture Overview

## Project Goal

`bug-triage-automation-workflow` is an Agentic Engineering Operations Assistant. The end-state system will analyze GitHub issues, retrieve relevant repository and operational context, recommend ownership, generate root cause hypotheses, suggest remediation steps, and require human approval before taking action.

The current implementation reaches Step 7: the data foundation, RAG ingestion/retrieval, structured LLM calls, LangGraph orchestration, and FastAPI wrapper are in place.

## Current MVP Architecture

```text
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
src.api
  /health and /triage
```

## Main Runtime Paths

### Ingestion Path

Run:

```bash
python -m rag.ingest
```

This reads source data from `data/`, chunks it, generates vectors, and writes a Chroma collection.

### Retrieval Path

Run:

```bash
python -m rag.retriever "firmware update hash mismatch on hw-b2"
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
```

`POST /triage` accepts a ticket ID, title, description, provider, and approval preference. It calls the existing LangGraph workflow and returns the final state as JSON.

## Separation Of Concerns

`data/` is the knowledge base. It contains the raw text that retrieval should search.

`rag/` owns retrieval infrastructure. It does not decide final triage answers; it prepares context.

`agent/` owns workflow orchestration. It uses LangGraph to pass serializable state through clear nodes.

`llm/` owns structured reasoning. It defines schemas, a service layer, a base client interface, and provider implementations.

`prompts/` owns hosted LLM task instructions for classification, owner recommendation, RCA generation, and comment drafting.

`src/api/` owns HTTP transport. It validates API payloads and delegates workflow execution to `agent.graph`.

`docs/` explains how the system works and how to discuss the architecture.

## Why This Design Matters

The system separates retrieval from reasoning. Retrieval finds relevant evidence. The LLM uses that evidence to form recommendations. This mirrors production RAG systems, where the LLM does not permanently know private company context; the application fetches that context at runtime and injects it into the prompt.

The system also separates orchestration from model calls. LangGraph coordinates state transitions, while `TriageService` owns model-facing business logic. This keeps the graph explicit without turning the project into a complex multi-agent system.
