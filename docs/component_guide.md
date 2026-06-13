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

The workflow can depend on the interface instead of a specific provider. This makes it easy to use a mock client during development and switch to OpenAI later.

## `llm/mock_client.py`

Provides deterministic triage output with no API call.

Role in the stack:

```text
issue + retrieved context -> fake structured triage response
```

Why it matters:

The mock client lets you develop orchestration, data flow, and output handling without token cost or network dependency.

## `llm/openai_client.py`

Provides an optional hosted LLM implementation.

Role in the stack:

```text
issue + retrieved context -> real LLM-generated triage response
```

Why it matters:

This is the production-style reasoning path. It should be introduced after retrieval, output contracts, and human approval flows are stable.

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

