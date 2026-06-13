# Interview Talking Points

## One-Sentence Project Description

This project is an Agentic Engineering Operations Assistant that uses RAG to retrieve issue, code, log, and ownership context, then prepares structured bug triage recommendations for human approval.

## Current Architecture Explanation

The current system has a local RAG pipeline. It ingests engineering knowledge from Markdown, JSON, and log files, chunks the text, embeds each chunk, stores the chunks in Chroma, and retrieves relevant context for a new issue query.

The reasoning layer is abstracted behind `BaseTriageLLM` and exposed through `TriageService`. During MVP development, it uses a mock client to avoid token spend. Later, the same interface can call OpenAI or another LLM provider. The four structured reasoning steps are classification, owner recommendation, RCA generation, and draft comment creation.

## How To Explain RAG In This Project

RAG is used to ground the model in project-specific context. Instead of asking an LLM to guess the owner or root cause from a GitHub issue alone, the application retrieves relevant troubleshooting docs, historical issues, code summaries, logs, and ownership metadata. The LLM can then reason over both the user issue and the retrieved evidence.

## Why Metadata Matters

Each chunk stores metadata such as source file, filename, document type, and chunk index. This makes retrieval traceable. In a production triage assistant, recommendations need citations or evidence because engineers need to trust why the agent suggested a team or root cause.

## Why There Is A Mock LLM

The mock LLM allows the workflow to be developed and tested without calling a paid API. This is a common engineering pattern: stabilize interfaces and data flow before adding expensive or nondeterministic external services.

The mock client and OpenAI client inherit from the same abstract base class, which keeps the application code provider-agnostic.

## Why Structured Outputs Matter

The project uses Pydantic models for LLM inputs and outputs. This makes the system more production-like because each step returns a predictable object instead of a free-form paragraph.

Structured outputs make it easier to:

- test behavior
- store results in a database later
- pass state through LangGraph
- evaluate quality
- show human reviewers consistent fields

## Why The MVP Uses Hash Embeddings

The MVP uses a dependency-free hash embedder to avoid local ML installation issues and avoid OpenAI token usage. It is not the final retrieval model. It is a practical local substitute that lets the project exercise the full RAG flow.

For production, the hash embedder should be replaced with a real semantic embedding model, such as OpenAI embeddings or a vetted internal embedding service.

## What Chroma Does

Chroma is the local vector store. It stores:

- vectors
- chunk text
- metadata
- chunk IDs

At query time, Chroma performs nearest-neighbor search to find chunks whose vectors are close to the query vector.

## Production Evolution

A production version would likely add:

- GitHub issue webhook ingestion
- repository/code context sync
- incremental vector indexing
- real semantic embeddings
- real LLM reasoning with structured output validation
- LangGraph orchestration over the existing structured service calls
- human approval workflow
- GitHub comment, label, and assignment actions
- observability and audit logs

## Strong Interview Framing

Good way to explain the design:

```text
I separated retrieval from reasoning. The RAG layer is responsible for finding grounded evidence from internal sources, while the LLM layer is responsible for turning the issue and retrieved evidence into a structured triage recommendation. Both embedding and LLM providers are abstracted so the MVP can run locally and cheaply, while production can swap in stronger hosted models.
```

Another strong framing:

```text
Before adding LangGraph, I created stable typed functions for each reasoning step. That gives the graph clean nodes to orchestrate: classify, route ownership, generate RCA, and draft a comment. The graph will coordinate the workflow, but the business logic already lives behind testable service methods.
```

## Tradeoffs To Name Clearly

The current system optimizes for learning speed and local development, not final model quality.

Tradeoffs:

- hash embeddings are cheap and simple but weaker than semantic embeddings
- Chroma is easy locally but not necessarily the final production vector store
- full collection rebuild is simple but not scalable
- mock LLM is deterministic but not intelligent
- fake data is good for development but real issue data will require privacy and access controls

Being able to name these tradeoffs is a strength. It shows you understand both the MVP and the production path.

## Useful Vocabulary

- RAG: retrieval-augmented generation
- embedding: vector representation of text
- vector store: database optimized for similarity search
- chunking: splitting documents into retrievable passages
- metadata: source and classification data attached to chunks
- retrieval: finding relevant chunks for a query
- grounding: giving the LLM evidence to reduce guessing
- provider abstraction: interface that allows implementation swapping
- human-in-the-loop: requiring human approval before action
- incremental ingestion: updating only changed documents in the vector store
- structured output: predictable machine-readable LLM response
