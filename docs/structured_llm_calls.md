# Structured LLM Calls

## Purpose

The structured LLM layer turns issue context and retrieved evidence into typed triage outputs. It is designed so future LangGraph nodes can call simple methods and pass Pydantic models through workflow state.

This layer is Step 5 of the implementation plan.

## Core Flow

```text
TriageContext
  -> classify_issue()
  -> recommend_owner()
  -> generate_rca()
  -> draft_comment()
```

Each method lives on `TriageService` and delegates to the configured LLM client.

## Input Schema

`llm.schemas.TriageContext` is the shared input model:

```python
TriageContext(
    issue_title="...",
    issue_body="...",
    issue_comments=[],
    labels=[],
    retrieved_context=[],
    logs=[],
    repo_name=None,
)
```

This model is intentionally broader than the current smoke test. Later, GitHub issue data, retrieved Chroma chunks, comments, logs, and repository metadata can all land in this one normalized object.

## Output Schemas

`ClassificationOutput` contains:

- `issue_type`
- `component`
- `severity`
- `confidence`
- `reasoning_summary`

`OwnerRecommendationOutput` contains:

- `recommended_owner`
- `confidence`
- `supporting_evidence`

`RCAOutput` contains:

- `root_cause_hypothesis`
- `suggested_next_steps`
- `risk_level`
- `confidence`

`DraftCommentOutput` contains:

- `comment`
- `approval_required`
- `tone`

The confidence fields are constrained between `0` and `1`.

## Service Layer

`llm.triage_service.TriageService` is the application-facing API:

```python
service = TriageService()
classification = service.classify_issue(context)
owner = service.recommend_owner(context, classification)
rca = service.generate_rca(context, classification, owner)
comment = service.draft_comment(context, classification, owner, rca)
```

This is the interface future LangGraph nodes should use.

## Client Interface

`llm.base_client.BaseTriageLLM` is an abstract base class. It cannot be instantiated directly. It defines the contract every model provider must implement:

- `provider_name`
- `classify_issue`
- `recommend_owner`
- `generate_rca`
- `draft_comment`

This is an object-oriented provider abstraction. The graph or API layer does not need to know whether the backing implementation is mock logic or a hosted LLM.

## Mock Client

`llm.mock_client.MockTriageLLM` implements deterministic keyword rules.

Examples:

- firmware, OTA, manifest, hash -> `firmware_update`, `firmware-update-team`
- auth, login, redirect, token -> `auth`, `platform-team`
- bluetooth, pairing, BLE -> `bluetooth`, `device-connectivity-team`
- DNS, network, wifi -> `networking`, `networking-team`
- release, build, artifact, CI -> `release_pipeline`, `build-systems-team`

This is not real model reasoning. It exists to make the workflow testable and cheap while the system shape is still being built.

## OpenAI Client

`llm.openai_client.OpenAITriageLLM` uses prompt files from `prompts/` and expects JSON that matches the relevant Pydantic model.

If the model returns invalid JSON or JSON that fails schema validation, the client raises a clear `ValueError`.

Prompt files:

- `prompts/classify_issue.md`
- `prompts/recommend_owner.md`
- `prompts/generate_rca.md`
- `prompts/draft_comment.md`

## Smoke Test

Run:

```bash
python scripts/smoke_test_structured_llm.py
```

This creates a firmware issue context, runs all four structured calls with the mock client, and prints JSON output for each step.

For the full current flow, including Chroma retrieval before triage, run:

```bash
python scripts/smoke_test_rag_to_llm.py
```

That script reads `data/sample_issues/sample_issue_001.md`, retrieves the top matching chunks from Chroma, adds those chunks to `TriageContext.retrieved_context`, and then runs the four structured triage calls.

## Automated Tests

Run:

```bash
python -m pytest tests/test_structured_llm.py
```

The tests verify:

- firmware issue maps to `firmware_update` and `firmware-update-team`
- auth issue maps to `auth` and `platform-team`
- outputs are valid Pydantic models
- confidence values are between `0` and `1`

## How This Plugs Into LangGraph

In Step 6, each structured method can become a LangGraph node:

```text
classify_issue_node
  -> recommend_owner_node
  -> generate_rca_node
  -> draft_comment_node
```

The graph state can store:

- `context: TriageContext`
- `classification: ClassificationOutput`
- `owner: OwnerRecommendationOutput`
- `rca: RCAOutput`
- `draft_comment: DraftCommentOutput`

That keeps orchestration clean and makes each node easy to test.
