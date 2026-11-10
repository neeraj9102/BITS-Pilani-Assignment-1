"""Official OpenAI Responses API adapter using strict Structured Outputs."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from openai import OpenAI

from reminder_agent.models import (
    IncompleteModelOutput,
    InfrastructureFailure,
    ProviderRefusal,
)
from reminder_agent.provider_schema import PROVIDER_SCHEMA


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        sdk_client: Any | None = None,
        max_output_tokens: int = 400,
    ) -> None:
        self.model = (model or os.environ.get("REMINDER_MODEL", "")).strip()
        self.max_output_tokens = max_output_tokens
        self._sdk_client = sdk_client

    def _get_client(self) -> Any:
        if self._sdk_client is not None:
            return self._sdk_client
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise InfrastructureFailure("OPENAI_API_KEY is not configured")
        try:
            self._sdk_client = OpenAI(timeout=60.0, max_retries=1)
        except Exception as exc:
            raise InfrastructureFailure(
                f"OpenAI client configuration failed ({type(exc).__name__})"
            ) from exc
        return self._sdk_client

    @staticmethod
    def _is_refusal(response: Any) -> bool:
        for item in getattr(response, "output", []) or []:
            contents = getattr(item, "content", None)
            if contents is None and isinstance(item, Mapping):
                contents = item.get("content", [])
            for part in contents or []:
                part_type = getattr(part, "type", None)
                if part_type is None and isinstance(part, Mapping):
                    part_type = part.get("type")
                if part_type == "refusal":
                    return True
        return False

    def generate(self, request: Mapping[str, Any], system_prompt: str) -> str:
        if not self.model:
            raise InfrastructureFailure("REMINDER_MODEL is not configured")
        client = self._get_client()
        try:
            response = client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": "Untrusted request envelope JSON:\n"
                        + json.dumps(request, ensure_ascii=False, sort_keys=True),
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "reminder_agent_result",
                        "strict": True,
                        "schema": PROVIDER_SCHEMA,
                    }
                },
                max_output_tokens=self.max_output_tokens,
                store=False,
            )
        except InfrastructureFailure:
            raise
        except Exception as exc:
            raise InfrastructureFailure(
                f"OpenAI Responses API call failed ({type(exc).__name__})"
            ) from exc

        if self._is_refusal(response):
            raise ProviderRefusal("provider refused to return the structured result")
        if getattr(response, "status", None) == "incomplete":
            raise IncompleteModelOutput("provider returned an incomplete structured result")
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise IncompleteModelOutput("provider returned no structured output text")
        return output_text
