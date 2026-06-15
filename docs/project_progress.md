# Project Progress

## Current Status

The project has completed the data foundation, RAG ingestion/retrieval, structured LLM calls, lightweight LangGraph workflow orchestration, a FastAPI wrapper, Postgres-backed persistence, and a Streamlit demo UI.

Completed implementation steps:

- Step 1: repository and environment scaffolding
- Step 2: fake RAG source data
- Step 3: RAG ingestion into Chroma
- Step 4: top-k retrieval from Chroma
- Step 5: structured LLM calls with mock and OpenAI-compatible clients
- Step 6: LangGraph workflow orchestration
- Step 7: FastAPI endpoints
- Step 8: Postgres persistence
- Step 9: Streamlit UI

Remaining major steps:

- Step 10: evals and metrics

## What Works Today

You can ingest local project knowledge:

```bash
python -m rag.ingest --provider hash
python -m rag.ingest --provider openai
```

You can retrieve relevant chunks:

```bash
python -m rag.retriever "firmware update hash mismatch on hw-b2" --provider hash
python -m rag.retriever "firmware update hash mismatch on hw-b2" --provider openai
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
docker compose up -d
uvicorn src.api.main:app --reload
```

You can initialize the persistence tables directly:

```bash
python -c "from src.db.database import init_db; init_db(); print('db ok')"
```

You can run the persistence smoke test:

```bash
python scripts/smoke_test_persistence.py --provider mock
python scripts/smoke_test_persistence.py --provider openai
```

You can run the Streamlit/FastAPI contract smoke test after starting FastAPI:

```bash
python scripts/smoke_test_streamlit_api.py --provider mock
python scripts/smoke_test_streamlit_api.py --provider openai
```

You can start the Streamlit demo UI:

```bash
streamlit run frontend/streamlit_app.py
```

You can inspect stored runs in Postgres:

```bash
docker compose exec postgres psql -U bugtriage -d bugtriage
```

Useful tables:

```text
triage_runs
retrieved_sources
human_feedback
```

You can run focused tests:

```bash
python -m pytest tests/test_structured_llm.py
python -m pytest tests/test_langgraph_workflow.py
python -m pytest tests/test_api.py
python -m pytest tests/test_api.py tests/test_structured_llm.py tests/test_langgraph_workflow.py
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
  -> Postgres persistence
  -> FastAPI JSON response
  -> Streamlit demo UI
```

The important engineering split is:

- `rag/` finds relevant evidence.
- `agent/` orchestrates the stateful workflow using LangGraph.
- `llm/` turns issue context and evidence into structured recommendations.
- `src/api/` exposes the workflow through HTTP endpoints.
- `src/db/` persists workflow runs, retrieved evidence, latency, approval state, and feedback.
- `frontend/` provides a demo UI that calls FastAPI over HTTP.
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

At the end of Step 7, `/triage` returned the final workflow state as structured JSON. Step 8 then added durable storage around that API flow.

## What Step 8 Added

Step 8 added:

- `docker-compose.yml`: local Postgres for development
- `src/db/database.py`: SQLAlchemy engine, session, and table initialization
- `src/db/models.py`: persisted triage run, retrieved source, and feedback tables
- `src/db/repository.py`: database helper functions used by the API
- `GET /triage`: list recent stored triage runs
- `GET /triage/{run_id}`: fetch one stored triage run with retrieved sources and feedback
- `POST /feedback`: store human review feedback for a run
- `scripts/smoke_test_persistence.py`: manual persistence smoke test

At the end of Step 8, the API had a system of record. That made Step 9 straightforward because a UI could list past triage runs, inspect retrieved evidence, and submit approval feedback without changing the workflow logic.

For hands-on operation, see [Running The App](running_the_app.md).

## What Step 9 Added

Step 9 added:

- `frontend/streamlit_app.py`: customer-facing demo UI over the FastAPI API
- `API_BASE_URL`: configurable FastAPI base URL for the frontend
- `scripts/smoke_test_streamlit_api.py`: HTTP contract smoke test for the endpoints used by Streamlit
- Submit Issue page: create a new triage run and view the result
- Run History page: list persisted triage runs
- Run Details / Feedback page: inspect a run and submit human feedback

This is a good stopping point before evals because the project now has a visible demo surface and a persisted feedback loop.
