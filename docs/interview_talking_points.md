# Interview Talking Points

## One-Sentence Project Description

This project is an Agentic Engineering Operations Assistant that uses RAG to retrieve issue, code, log, and ownership context, then prepares structured bug triage recommendations for human approval.

## Current Architecture Explanation

The current system has a local RAG pipeline. It ingests engineering knowledge from Markdown, JSON, and log files, chunks the text, embeds each chunk, stores the chunks in Chroma, and retrieves relevant context for a new issue query.

The reasoning layer is abstracted behind `BaseTriageLLM` and exposed through `TriageService`. During MVP development, it uses a mock client to avoid token spend. Later, the same interface can call OpenAI or another LLM provider. The four structured reasoning steps are classification, owner recommendation, RCA generation, and draft comment creation.

LangGraph now orchestrates those steps as a lightweight state machine. It prepares the issue context, retrieves relevant RAG chunks, calls the structured triage service, drafts the comment, and sets the approval gate fields.

FastAPI exposes that workflow as an HTTP API, and Postgres stores each run. The persisted record includes the input issue, final state, retrieved evidence, latency, approval requirement, status, and any human feedback.

Streamlit provides a demo UI over the API, and the offline eval harness measures the same workflow against labeled cases.

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

## Why LangGraph Is Used

I used LangGraph as a lightweight workflow orchestrator, not because the MVP strictly required it, but because the system models a stateful enterprise workflow: retrieve context, classify, recommend ownership, generate RCA, draft a response, and route for human approval. I kept business logic in plain Python modules and used LangGraph to make the workflow explicit, testable, and extensible.

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

## What Postgres Does

Postgres is the system of record for the application. Chroma answers "what context is relevant?" while Postgres answers "what happened during this workflow run?"

The MVP stores:

- triage run input and final output
- retrieved source metadata and previews
- latency and status
- approval state
- human feedback

This is important because production AI systems need auditability. Engineers and stakeholders need to inspect what the agent retrieved, what it recommended, and whether humans accepted or corrected the result.

## Why SQLAlchemy And Dockerized Postgres

I used SQLAlchemy because it keeps database access explicit and testable while still allowing different database URLs for local development, tests, and cloud deployment.

I used Dockerized Postgres because it gives the MVP a realistic relational database without requiring a cloud account. Since the app reads `DATABASE_URL`, moving from local Docker to AWS RDS or GCP Cloud SQL should primarily be a configuration change, not an application rewrite.

## Why Offline Evals Matter

I added an offline evaluation harness that runs labeled issues through the same LangGraph workflow used by the API. It measures component accuracy, owner recommendation accuracy, issue type accuracy, approval routing correctness, retrieval hit rate, and latency. This gives me a repeatable way to test prompt, retrieval, and workflow changes instead of relying on anecdotal demo quality.

The eval setup also surfaced an important production lesson: retrieval and ingestion must use the same embedding provider and vector dimensionality. When I ingested with OpenAI embeddings but evaluated with hash retrieval, Chroma rejected the query vectors. That is exactly the kind of configuration issue a production system should make explicit and validate early.

The OpenAI evals also surfaced a model-behavior issue: the model sometimes over-inferred owners for ambiguous cases. I hardened the classification and ownership policy so weak evidence maps to `unknown` and `needs-human-triage`, and multi-component issues only choose a primary owner when one direct failure signal is clearly strongest.

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

Now that LangGraph is in place:

```text
I kept LangGraph intentionally boring: a linear workflow over a serializable state object. The graph does orchestration, not business logic. That makes the next FastAPI step straightforward because the API can call one function, run_triage_workflow(), and return the final state.
```

Now that persistence is in place:

```text
I added Postgres as the system of record. Chroma remains the retrieval index, but Postgres stores the durable workflow history: issue input, final triage output, retrieved evidence, latency, approval state, and human feedback. That gives the system auditability and creates the foundation for a UI, evals, and continuous improvement.
```

Now that evals are in place:

```text
I added an offline eval harness with labeled issue cases. It runs the same graph used by the API, scores structured outputs and retrieval evidence, and writes results to JSON. That gives me a regression test loop for workflow quality before adding more complex production evals like LLM-as-judge or online feedback metrics.
```

Now that routing policy is hardened:

```text
The evals showed that the hosted model could over-infer on ambiguous issues, so I tightened the output schema and prompt policy. The classifier can only return known components or unknown, and ownership routes to needs-human-triage when evidence is weak. That is an AI safety and reliability pattern: prefer human escalation over unsupported automation.
```

## Tradeoffs To Name Clearly

The current system optimizes for learning speed and local development, not final model quality.

Tradeoffs:

- hash embeddings are cheap and simple but weaker than semantic embeddings
- Chroma is easy locally but not necessarily the final production vector store
- full collection rebuild is simple but not scalable
- mock LLM is deterministic but not intelligent
- fake data is good for development but real issue data will require privacy and access controls
- `create_all()` is fine for the MVP but production should use Alembic migrations
- local Docker Postgres is realistic for development but production needs managed backups, access controls, and monitoring
- offline evals measure structured fields and retrieval hits, but they do not yet judge RCA or comment quality semantically
- hard enum constraints improve reliability but require prompt alignment so hosted models return valid structured values

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
- system of record: durable database storing authoritative workflow history
- audit trail: record of inputs, evidence, outputs, and human decisions
- migration: controlled database schema change, usually managed with Alembic in Python apps
- offline eval: repeatable labeled test set used to measure AI workflow quality
- regression eval: eval run used to catch quality drops after code, prompt, model, or retrieval changes
