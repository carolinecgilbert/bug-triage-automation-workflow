"""Optional OpenAI LLM client for later non-MVP triage reasoning."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TypeVar
from dotenv import load_dotenv

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from llm.base_client import BaseTriageLLM
from llm.schemas import (
    ClassificationOutput,
    DraftCommentOutput,
    OwnerRecommendationOutput,
    RCAOutput,
    TriageContext,
)


DEFAULT_OPENAI_CHAT_MODEL = "gpt-4.1-mini"
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
SchemaModel = TypeVar("SchemaModel", bound=BaseModel)

load_dotenv()


class OpenAITriageLLM(BaseTriageLLM):
    """Hosted LLM implementation with the same shape as the mock client."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_OPENAI_CHAT_MODEL) -> None:
        self.model_name = model_name
        self._client = OpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    def classify_issue(self, context: TriageContext) -> ClassificationOutput:
        """Classify an issue using the hosted model and validate JSON output."""
        return self._request_structured_output(
            prompt_name="classify_issue.md",
            payload={"context": context.model_dump()},
            output_model=ClassificationOutput,
        )

    def recommend_owner(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
    ) -> OwnerRecommendationOutput:
        """Recommend owner using the hosted model and validate JSON output."""
        return self._request_structured_output(
            prompt_name="recommend_owner.md",
            payload={
                "context": context.model_dump(),
                "classification": classification.model_dump(),
            },
            output_model=OwnerRecommendationOutput,
        )

    def generate_rca(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
    ) -> RCAOutput:
        """Generate RCA hypothesis using the hosted model and validate JSON output."""
        return self._request_structured_output(
            prompt_name="generate_rca.md",
            payload={
                "context": context.model_dump(),
                "classification": classification.model_dump(),
                "owner": owner.model_dump(),
            },
            output_model=RCAOutput,
        )

    def draft_comment(
        self,
        context: TriageContext,
        classification: ClassificationOutput,
        owner: OwnerRecommendationOutput,
        rca: RCAOutput,
    ) -> DraftCommentOutput:
        """Draft a GitHub comment using the hosted model and validate JSON output."""
        return self._request_structured_output(
            prompt_name="draft_comment.md",
            payload={
                "context": context.model_dump(),
                "classification": classification.model_dump(),
                "owner": owner.model_dump(),
                "rca": rca.model_dump(),
            },
            output_model=DraftCommentOutput,
        )

    def _request_structured_output(
        self,
        prompt_name: str,
        payload: dict[str, object],
        output_model: type[SchemaModel],
    ) -> SchemaModel:
        """Call OpenAI and parse the response into the requested Pydantic model."""
        prompt = load_prompt(prompt_name)
        user_payload = json.dumps(payload, indent=2)

        response = self._client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": f"Input JSON:\n{user_payload}",
                },
            ],
        )

        raw_output = response.output_text
        json_text = extract_json_object(raw_output)

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"OpenAI response for {prompt_name} was not valid JSON: {raw_output}"
            ) from exc

        try:
            return output_model.model_validate(parsed)
        except ValidationError as exc:
            raise ValueError(
                f"OpenAI response for {prompt_name} did not match {output_model.__name__}: {parsed}"
            ) from exc


def load_prompt(prompt_name: str) -> str:
    """Load a prompt markdown file by name."""
    prompt_path = PROMPTS_DIR / prompt_name
    return prompt_path.read_text(encoding="utf-8")


def extract_json_object(raw_output: str) -> str:
    """Extract a JSON object from plain or Markdown-fenced model output."""
    text = raw_output.strip()

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def create_openai_triage_llm() -> OpenAITriageLLM:
    """Create an OpenAI triage client when you are ready to spend tokens."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
    model_name = os.getenv("OPENAI_CHAT_MODEL", DEFAULT_OPENAI_CHAT_MODEL)
    return OpenAITriageLLM(api_key=api_key, model_name=model_name)
