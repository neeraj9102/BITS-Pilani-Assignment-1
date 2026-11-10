"""Local Ollama chat adapter using its JSON Schema structured-output API."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from reminder_agent.models import IncompleteModelOutput, InfrastructureFailure
from reminder_agent.provider_schema import PROVIDER_SCHEMA

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class OllamaClient:
    """Call a loopback-only Ollama server without credentials or tools."""

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 60.0,
        temperature: float = 0.2,
        max_output_tokens: int = 400,
        opener: Any = urlopen,
    ) -> None:
        self.model = (model or os.environ.get("REMINDER_MODEL", "")).strip()
        self.base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.opener = opener
        parsed = urlsplit(self.base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in LOCAL_HOSTS
            or parsed.port not in {None, 11434}
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise InfrastructureFailure(
                "OLLAMA_BASE_URL must be a loopback HTTP URL on the local Ollama port"
            )

    def generate(self, request: Mapping[str, Any], system_prompt: str) -> str:
        if not self.model:
            raise InfrastructureFailure("REMINDER_MODEL is not configured")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Untrusted request envelope JSON:\n"
                    + json.dumps(request, ensure_ascii=False, sort_keys=True),
                },
            ],
            "format": PROVIDER_SCHEMA,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_output_tokens,
            },
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        http_request = Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.opener(http_request, timeout=self.timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise InfrastructureFailure(
                f"local Ollama API returned HTTP {error.code}"
            ) from error
        except (TimeoutError, URLError, OSError) as error:
            raise InfrastructureFailure(
                f"local Ollama API request failed ({type(error).__name__})"
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise IncompleteModelOutput("local Ollama API returned invalid JSON") from error

        message = response_data.get("message") if isinstance(response_data, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise IncompleteModelOutput("local Ollama model returned no structured output text")
        return content
