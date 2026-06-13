# MVP vs Production

## Why The MVP Uses A Hash Embedder

The MVP currently defaults to:

```env
EMBEDDING_PROVIDER=hash
```

This provider creates deterministic local vectors from tokens using a hashing trick. It is simple and free. It avoids:

- OpenAI token usage
- Hugging Face model downloads
- PyTorch installation issues
- local ML dependency debugging

This is appropriate while learning and validating the RAG pipeline.

## Hash Embeddings Are Not Production Semantic Embeddings

The hash embedder is useful for wiring the system, but it has limitations:

- It mainly captures keyword overlap.
- It does not understand synonyms well.
- It does not capture deeper semantic similarity.
- Retrieval quality will be weaker than a real embedding model.

For this corpus, it can still work surprisingly well because the fake docs share explicit terms like `firmware`, `hash`, `auth`, `session`, and `DNS`.

## Production Embedding Options

A production version would likely use one of:

- OpenAI `text-embedding-3-small` or a newer approved embedding model
- Azure OpenAI embeddings
- a managed embedding provider such as Cohere or Voyage
- a vetted local embedding model served behind an internal API

The right choice depends on:

- retrieval quality
- latency
- cost
- privacy requirements
- operational burden
- compliance constraints

## Local Chroma vs Production Vector Store

The MVP uses Chroma persisted to a local directory.

That is useful for local development, but production systems often use:

- managed vector databases
- Postgres with `pgvector`
- OpenSearch or Elasticsearch vector search
- cloud search platforms
- self-hosted Chroma or Qdrant

Production concerns include:

- backups
- access control
- indexing latency
- multi-tenant isolation
- observability
- data retention
- rollback strategy

## Repeatable Ingestion vs Incremental Ingestion

The current ingestion script deletes and recreates the collection each run.

That is fine for a 20-file corpus.

In production, this would become incremental:

```text
detect changed source document
  -> remove stale chunks for that source
  -> chunk updated document
  -> embed updated chunks
  -> upsert into vector store
```

Incremental indexing saves cost and avoids downtime for larger corpora.

## Mock LLM vs Real LLM

The MVP defaults to:

```env
LLM_PROVIDER=mock
```

The mock client returns deterministic structured output. It is not meant to produce real reasoning. It is meant to stabilize the interface.

Production would use:

```env
LLM_PROVIDER=openai
```

or another hosted/internal LLM provider.

The key engineering choice is that both clients inherit from `BaseTriageLLM`, so the workflow can switch providers without changing orchestration code.

## Human-In-The-Loop Design

The current mock response includes:

```json
"human_approval_required": true
```

This is important. For engineering operations, the agent should not blindly label, assign, close, or remediate issues without approval.

Production approval flow might include:

- draft recommendation
- confidence score
- retrieved evidence
- suggested GitHub labels and owner
- approval or rejection by a human
- audit log of action taken

## Observability Needed Later

Production AI workflows need observability around both retrieval and generation.

Useful signals:

- source files indexed
- chunk counts
- embedding provider and model
- retrieval latency
- top retrieved sources
- LLM provider and model
- prompt version
- output schema validation result
- human approval decision
- final GitHub action

These are the signals an AI FDE would use to debug quality and reliability.

