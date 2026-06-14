# Project Progress

## Current Status

The project has completed the data foundation, RAG ingestion/retrieval, structured LLM calls, lightweight LangGraph workflow orchestration, and a FastAPI wrapper.

Completed implementation steps:

- Step 1: repository and environment scaffolding
- Step 2: fake RAG source data
- Step 3: RAG ingestion into Chroma
- Step 4: top-k retrieval from Chroma
- Step 5: structured LLM calls with mock and OpenAI-compatible clients
- Step 6: LangGraph workflow orchestration
- Step 7: FastAPI endpoints

Remaining major steps:

- Step 8: SQLite persistence
- Step 9: Streamlit UI
- Step 10: evals and metrics

## What Works Today

You can ingest local project knowledge:

```bash
python -m rag.ingest
```

You can retrieve relevant chunks:

```bash
python -m rag.retriever "firmware update hash mismatch on hw-b2"
```

You can run the structured LLM sequence with either mock or OpenAI:

```bash
python scripts/smoke_test_structured_llm.py --provider mock
python scripts/smoke_test_structured_llm.py --provider openai
```

You can run the full current RAG-to-triage flow:

```bash
python scripts/smoke_test_rag_to_llm.py --provider mock
python scripts/smoke_test_rag_to_llm.py --provider openai
```

You can run the LangGraph-orchestrated workflow:

```bash
python scripts/smoke_test_langgraph.py --provider mock
python scripts/smoke_test_langgraph.py --provider openai
```

You can run the FastAPI endpoint smoke test:

```bash
python scripts/smoke_test_fastapi.py --provider mock
python scripts/smoke_test_fastapi.py --provider openai
```

You can start the API server locally:

```bash
uvicorn src.api.main:app --reload
```

You can run focused tests:

```bash
python -m pytest tests/test_structured_llm.py
python -m pytest tests/test_langgraph_workflow.py
python -m pytest tests/test_api.py
```

## Current End-To-End Mental Model

```text
fake engineering corpus
  -> RAG ingestion
  -> Chroma vector store
  -> retrieval for a new issue
  -> LangGraph workflow nodes
  -> structured triage service
  -> classify issue
  -> recommend owner
  -> generate RCA hypothesis
  -> draft human-reviewable comment
  -> approval gate
  -> FastAPI JSON response
```

The important engineering split is:

- `rag/` finds relevant evidence.
- `agent/` orchestrates the stateful workflow using LangGraph.
- `llm/` turns issue context and evidence into structured recommendations.
- `src/api/` exposes the workflow through HTTP endpoints.
- `prompts/` defines hosted LLM task instructions.
- `tests/` protects expected structured behavior.
- `scripts/` gives a quick manual demo path.

## What Step 6 Added

Step 6 added:

- `agent/state.py`: serializable `TriageState`
- `agent/nodes.py`: plain Python workflow nodes
- `agent/graph.py`: linear LangGraph orchestration
- `scripts/smoke_test_langgraph.py`: manual end-to-end graph smoke test
- `tests/test_langgraph_workflow.py`: focused graph tests

This is a good stopping point before FastAPI because `run_triage_workflow()` now provides one clean callable function for an API route to invoke.

## What Step 7 Added

Step 7 added:

- `src/api/main.py`: FastAPI app with `/health` and `/triage`
- `src/api/schemas.py`: request and response schemas
- `src/api/dependencies.py`: provider selection for mock or OpenAI
- `scripts/smoke_test_fastapi.py`: in-process FastAPI smoke test
- `tests/test_api.py`: API tests using `TestClient`

This is a good stopping point before persistence because `/triage` now returns the final workflow state as structured JSON, but it does not store anything yet.
