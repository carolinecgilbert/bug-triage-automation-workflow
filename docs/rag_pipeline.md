# RAG Pipeline

## What RAG Means

RAG stands for Retrieval-Augmented Generation.

In this project, retrieval is the part that finds relevant engineering context before an LLM produces a triage recommendation. The future LLM should not guess from the issue alone. It should reason over the issue plus retrieved docs, logs, historical incidents, ownership metadata, and code summaries.

## Step 1: Source Documents

The current corpus lives under `data/`:

- `data/docs/`: troubleshooting docs and severity policy
- `data/historical_issues/`: resolved bugs with root causes and owners
- `data/code_summaries/`: summaries of important modules
- `data/sample_issues/`: unresolved issues for testing
- `data/logs/`: realistic logs with root cause signals
- `data/ownership.json`: component-to-team routing metadata

In a production system, these sources might come from GitHub, Confluence, incident tools, log stores, service catalogs, or code search.

## Step 2: Document Loading

`rag.ingest.load_documents()` discovers `.md`, `.log`, and `.json` files under `data/`.

Each loaded document gets metadata:

- `source`: full repo-relative file path
- `filename`: file basename
- `doc_type`: normalized category for retrieval filtering and traceability

Doc types are inferred from directory names:

- `docs`
- `historical_issue`
- `code_summary`
- `sample_issue`
- `log`
- `ownership`

Metadata matters because retrieved chunks need provenance. In an engineering workflow, a recommendation is more credible when it can point to the exact source that influenced it.

## Step 3: Chunking

`rag.chunking.chunk_text()` splits each document into readable overlapping chunks.

Defaults:

```python
chunk_size = 1000
chunk_overlap = 150
```

Chunking exists because vector search works better on focused passages than on entire long documents. The overlap helps preserve context that might otherwise be split across chunk boundaries.

The current chunker is character-based and prefers natural boundaries such as paragraphs, lines, sentences, and spaces. In production, this might evolve into token-aware or structure-aware chunking.

## Step 4: Embedding

An embedding converts text into a vector, which is a list of numbers representing the text for similarity search.

Current MVP default:

```env
EMBEDDING_PROVIDER=hash
HASH_EMBEDDING_DIMENSIONS=384
```

The hash provider is dependency-free and token-free. It is not a production semantic model. It exists so the project can exercise the full RAG pipeline without fighting local ML installs or spending OpenAI tokens.

Optional providers in `rag.embeddings`:

- `hash`: local deterministic keyword-style vectors for MVP wiring
- `sentence-transformers`: local semantic embeddings if that stack is installed later
- `openai`: hosted OpenAI embeddings for production-style quality comparison

Important rule: ingestion and retrieval must use the same embedding provider and dimensionality. If you ingest with `hash` and query with OpenAI embeddings, the vectors are incompatible.

## Step 5: Vector Storage

`rag.ingest` stores chunks in Chroma with:

- chunk ID
- chunk text
- chunk metadata
- embedding vector

The Chroma collection is recreated on each ingestion run. This makes ingestion repeatable while the corpus is small and static.

In production, ingestion would usually become incremental. Instead of deleting the collection every time, the system would detect changed documents, re-embed only affected chunks, and preserve stable IDs.

## Step 6: Retrieval

`rag.retriever` accepts a command-line query, embeds it with the configured provider, and asks Chroma for the top matching chunks.

Example:

```bash
python -m rag.retriever "firmware update hash mismatch on hw-b2"
```

The retriever prints:

- source file
- document type
- similarity distance
- short preview

This is the evidence that a future triage agent would pass into the LLM reasoning layer.

## Step 7: Reasoning

The current project does not yet run a real triage agent. It includes `llm.MockTriageLLM` as a token-free reasoning stand-in.

The expected future flow is:

```text
GitHub issue text
  -> retrieve relevant chunks
  -> pass issue + context to LLM
  -> return structured triage recommendation
```

The mock client gives the workflow a stable output shape before real LLM calls are introduced.

