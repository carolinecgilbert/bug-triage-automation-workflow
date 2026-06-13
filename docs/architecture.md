# Architecture Overview

## Project Goal

`bug-triage-automation-workflow` is an Agentic Engineering Operations Assistant. The end-state system will analyze GitHub issues, retrieve relevant repository and operational context, recommend ownership, generate root cause hypotheses, suggest remediation steps, and require human approval before taking action.

Step 3 focuses on the data and retrieval foundation for that future workflow.

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
llm client
  mock reasoning now, OpenAI reasoning later
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

### Mock Reasoning Path

Run:

```bash
python -m llm.mock_demo "Users are logged out after dashboard refresh"
```

This proves that future workflow code can call an LLM-like interface and receive a structured triage response without spending tokens.

## Separation Of Concerns

`data/` is the knowledge base. It contains the raw text that retrieval should search.

`rag/` owns retrieval infrastructure. It does not decide final triage answers; it prepares context.

`llm/` owns reasoning clients. It receives issue text and retrieved context, then returns structured triage output.

`docs/` explains how the system works and how to discuss the architecture.

## Why This Design Matters

The system separates retrieval from reasoning. Retrieval finds relevant evidence. The LLM uses that evidence to form recommendations. This mirrors production RAG systems, where the LLM does not permanently know private company context; the application fetches that context at runtime and injects it into the prompt.

