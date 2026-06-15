# Running The App

This runbook explains how to start the MVP locally, run the current workflow, and inspect persisted triage data.

## What You Are Running

The local system has two kinds of storage:

```text
Chroma
  stores embedded RAG chunks for retrieval

Postgres
  stores triage runs, retrieved evidence, and human feedback
```

The runtime flow is:

```text
Streamlit
  -> POST /triage
  -> FastAPI validates the request
  -> LangGraph runs the triage workflow
  -> RAG retrieves context from Chroma
  -> TriageService calls mock or OpenAI client
  -> approval gate marks the run for review
  -> SQLAlchemy stores the result in Postgres
  -> API returns structured JSON
```

## Prerequisites

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure `.env` has the local database URL:

```env
DATABASE_URL=postgresql+psycopg://bugtriage:bugtriage@localhost:5432/bugtriage
```

If you use the OpenAI provider, also set:

```env
OPENAI_API_KEY=your-key
LLM_PROVIDER=openai
```

For OpenAI embeddings, use:

```env
OPENAI_API_KEY=your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

For normal local testing, keep:

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
API_BASE_URL=http://127.0.0.1:8000
```

## Full Local Demo Sequence

Use this sequence when you want to run the complete MVP:

```bash
docker compose up -d
python -m rag.ingest --provider hash
uvicorn src.api.main:app --reload
```

Then open a second terminal and run:

```bash
streamlit run frontend/streamlit_app.py
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

Streamlit app:

```text
http://localhost:8501
```

## Start Postgres

Start the local database:

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

If Docker reports that it cannot connect to the Docker API, Docker Desktop is not running. Open Docker Desktop, wait for it to finish starting, and retry the command.

## Initialize Tables

The API initializes tables on startup, but you can initialize them directly:

```bash
python -c "from src.db.database import init_db; init_db(); print('db ok')"
```

Expected output:

```text
db ok
```

## Build Or Refresh The RAG Index

Run ingestion before testing retrieval-heavy flows:

```bash
python -m rag.ingest --provider hash
```

This loads files under `data/`, chunks them, embeds the chunks, and writes them into Chroma.

To intentionally use OpenAI embeddings instead:

```bash
python -m rag.ingest --provider openai
```

Retrieval must use the same provider used for ingestion:

```bash
python -m rag.retriever "firmware update hash mismatch" --provider hash
python -m rag.retriever "firmware update hash mismatch" --provider openai
```

## Run Smoke Tests

Structured LLM only:

```bash
python scripts/smoke_test_structured_llm.py --provider mock
```

RAG to LLM:

```bash
python scripts/smoke_test_rag_to_llm.py --provider mock
```

LangGraph:

```bash
python scripts/smoke_test_langgraph.py --provider mock
```

FastAPI in-process:

```bash
python scripts/smoke_test_fastapi.py --provider mock
```

Persistence:

```bash
python scripts/smoke_test_persistence.py --provider mock
```

The persistence smoke test exercises:

```text
POST /triage
GET /triage/{run_id}
POST /feedback
```

Streamlit/FastAPI contract:

```bash
python scripts/smoke_test_streamlit_api.py --provider mock
```

Offline evals:

```bash
python scripts/run_evals.py --provider mock
```

If the average retrieval hit rate is `0`, refresh Chroma first:

```bash
python -m rag.ingest --provider hash
```

## Start The API Server

Run:

```bash
uvicorn src.api.main:app --reload
```

FastAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Run triage:

```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "BUG-LOCAL-001",
    "title": "Firmware update fails with hash mismatch",
    "description": "Devices download the OTA package but fail integrity validation before install.",
    "provider": "mock",
    "require_approval": true
  }'
```

Copy the returned `run_id`.

Fetch one stored run:

```bash
curl http://127.0.0.1:8000/triage/YOUR_RUN_ID_HERE
```

List recent runs:

```bash
curl http://127.0.0.1:8000/triage
```

Submit feedback:

```bash
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "YOUR_RUN_ID_HERE",
    "approved": true,
    "correct_owner": true,
    "useful_rca": true,
    "useful_comment": true,
    "notes": "Looks accurate for firmware ownership."
  }'
```

Fetch the same run again to confirm feedback was attached:

```bash
curl http://127.0.0.1:8000/triage/YOUR_RUN_ID_HERE
```

## Start The Streamlit UI

With FastAPI still running, start Streamlit in another terminal:

```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit app is usually available at:

```text
http://localhost:8501
```

Use the sidebar pages:

- Submit Issue: create a triage run and view the result
- Run History: list persisted runs from Postgres through FastAPI
- Run Details / Feedback: inspect a run and submit review feedback

The Streamlit app uses:

```env
API_BASE_URL=http://127.0.0.1:8000
```

It only calls FastAPI over HTTP. It does not call LangGraph or SQLAlchemy directly.

## Inspect Postgres

Open `psql`:

```bash
docker compose exec postgres psql -U bugtriage -d bugtriage
```

List tables:

```sql
\dt
```

Inspect table schemas:

```sql
\d triage_runs
\d retrieved_sources
\d human_feedback
```

List recent triage runs:

```sql
SELECT id, run_id, ticket_id, provider, status, latency_ms, approval_required
FROM triage_runs
ORDER BY id DESC
LIMIT 5;
```

Inspect retrieved RAG evidence:

```sql
SELECT id, run_id, doc_type, source, distance
FROM retrieved_sources
ORDER BY id DESC
LIMIT 10;
```

Inspect human feedback:

```sql
SELECT id, run_id, approved, correct_owner, useful_rca, useful_comment, notes
FROM human_feedback
ORDER BY id DESC
LIMIT 10;
```

Inspect final agent output JSON:

```sql
SELECT run_id, final_state_json
FROM triage_runs
ORDER BY id DESC
LIMIT 1;
```

Exit `psql`:

```sql
\q
```

## Run Tests

Run the focused test suite:

```bash
python -m pytest tests/test_api.py tests/test_structured_llm.py tests/test_langgraph_workflow.py
```

The API tests use a temporary SQLite database so they do not depend on Docker or mutate your local Postgres data.

## Run Offline Evals

Run:

```bash
python scripts/run_evals.py --provider mock
```

The eval runner:

- loads cases from `evals/test_cases.json`
- runs each issue through the existing LangGraph workflow
- scores component, owner, issue type, approval routing, retrieval hit rate, and latency
- writes results to `evals/results/latest_results.json`

Use OpenAI intentionally:

```bash
EMBEDDING_PROVIDER=openai python scripts/run_evals.py --provider openai
```

OpenAI evals spend tokens. Keep `mock` as the default for local regression checks.

If you ingested Chroma with OpenAI embeddings, eval retrieval must also use OpenAI embeddings. A dimension error like `Collection expecting embedding with dimension of 1536, got 384` means Chroma was built with OpenAI vectors but retrieval used hash vectors. Fix it by setting `EMBEDDING_PROVIDER=openai` for the eval run.

## Reset Local Data

To stop containers while keeping the database volume:

```bash
docker compose down
```

To delete all local Postgres data and start fresh:

```bash
docker compose down -v
docker compose up -d
python -c "from src.db.database import init_db; init_db(); print('db ok')"
```

Use `docker compose down -v` carefully. It deletes the `postgres_data` volume and all persisted triage runs.

## What To Look For

After a successful run, you should see:

- one new row in `triage_runs`
- several rows in `retrieved_sources`
- one row in `human_feedback` after calling `/feedback`
- `final_state_json` containing classification, owner recommendation, RCA, draft comment, approval state, and retrieved context

That proves the MVP can run the AI workflow and preserve an auditable record of what happened.

After a successful Streamlit demo, you should also be able to:

- submit a new issue through the UI
- see the triage result immediately
- select a persisted run from history
- view retrieved sources and raw final state
- submit feedback and confirm it appears on the run detail page
