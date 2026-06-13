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

## `rag/retriever.py`

Owns query-time retrieval.

Role in the stack:

```text
query -> query vector -> Chroma search -> relevant chunks
```

Why it matters:

This is the runtime path that gives the LLM private, current, task-specific context.

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
```
