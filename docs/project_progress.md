# Project Progress

## Current Status

The project has completed the data foundation, RAG ingestion/retrieval, and structured LLM call layer.

Completed implementation steps:

- Step 1: repository and environment scaffolding
- Step 2: fake RAG source data
- Step 3: RAG ingestion into Chroma
- Step 4: top-k retrieval from Chroma
- Step 5: structured LLM calls with mock and OpenAI-compatible clients

Remaining major steps:

- Step 6: LangGraph workflow orchestration
- Step 7: FastAPI endpoints
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

You can run the structured LLM sequence with the mock client:

```bash
python scripts/smoke_test_structured_llm.py
```

You can run the full current RAG-to-triage flow:

```bash
python scripts/smoke_test_rag_to_llm.py
```

You can run focused tests:

```bash
python -m pytest tests/test_structured_llm.py
```

## Current End-To-End Mental Model

```text
fake engineering corpus
  -> RAG ingestion
  -> Chroma vector store
  -> retrieval for a new issue
  -> structured triage service
  -> classify issue
  -> recommend owner
  -> generate RCA hypothesis
  -> draft human-reviewable comment
```

The important engineering split is:

- `rag/` finds relevant evidence.
- `llm/` turns issue context and evidence into structured recommendations.
- `prompts/` defines hosted LLM task instructions.
- `tests/` protects expected structured behavior.
- `scripts/` gives a quick manual demo path.

## Why This Is A Good Stopping Point Before LangGraph

LangGraph should orchestrate known, stable node functions. The project now has those functions through `TriageService`:

- `classify_issue`
- `recommend_owner`
- `generate_rca`
- `draft_comment`

That means the next step can focus on graph state and node wiring instead of inventing output schemas at the same time.
