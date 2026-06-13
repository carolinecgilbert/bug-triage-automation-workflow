"""Optional OpenAI LLM client for later non-MVP triage reasoning."""

from __future__ import annotations

import json
import os

from openai import OpenAI

from llm.base_client import BaseTriageLLM, TriageContext, TriageResponse


DEFAULT_OPENAI_CHAT_MODEL = "gpt-4.1-mini"


class OpenAITriageLLM(BaseTriageLLM):
    """Hosted LLM implementation with the same shape as the mock client."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_OPENAI_CHAT_MODEL) -> None:
        self.model_name = model_name
        self._client = OpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    def generate_triage_response(
        self,
        issue_text: str,
        retrieved_context: TriageContext,
    ) -> TriageResponse:
        context_text = "\n\n".join(
            f"Source: {item.get('source', 'unknown')}\n{item.get('text', '')}"
            for item in retrieved_context
        )
        response = self._client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an engineering bug triage assistant. Return only JSON with keys: "
                        "component, recommended_owner, confidence, root_cause_hypotheses, "
                        "recommended_next_steps, human_approval_required."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Issue:\n{issue_text}\n\nRetrieved context:\n{context_text}",
                },
            ],
        )
        parsed = json.loads(response.output_text)
        parsed["provider"] = self.provider_name
        return parsed


def create_openai_triage_llm() -> OpenAITriageLLM:
    """Create an OpenAI triage client when you are ready to spend tokens."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
    model_name = os.getenv("OPENAI_CHAT_MODEL", DEFAULT_OPENAI_CHAT_MODEL)
    return OpenAITriageLLM(api_key=api_key, model_name=model_name)
