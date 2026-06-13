# Architecture Overview

## Project Goal

`bug-triage-automation-workflow` is an Agentic Engineering Operations Assistant. The end-state system will analyze GitHub issues, retrieve relevant repository and operational context, recommend ownership, generate root cause hypotheses, suggest remediation steps, and require human approval before taking action.

The current implementation reaches Step 5: the data foundation, RAG ingestion/retrieval, and structured LLM calls are in place.

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
llm.TriageService
  classify -> recommend owner -> generate RCA -> draft comment
        |
        v
BaseTriageLLM implementation
  MockTriageLLM now, OpenAITriageLLM later
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

## Separation Of Concerns

`data/` is the knowledge base. It contains the raw text that retrieval should search.

`rag/` owns retrieval infrastructure. It does not decide final triage answers; it prepares context.

`llm/` owns structured reasoning. It defines schemas, a service layer, a base client interface, and provider implementations.

`prompts/` owns hosted LLM task instructions for classification, owner recommendation, RCA generation, and comment drafting.

`docs/` explains how the system works and how to discuss the architecture.

## Why This Design Matters

The system separates retrieval from reasoning. Retrieval finds relevant evidence. The LLM uses that evidence to form recommendations. This mirrors production RAG systems, where the LLM does not permanently know private company context; the application fetches that context at runtime and injects it into the prompt.

The system also separates orchestration from model calls. `TriageService` exposes clean methods that LangGraph can call later without caring whether the backing model is a mock client or OpenAI.
