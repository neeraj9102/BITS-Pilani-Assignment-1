"""Select a configured real model provider for the reminder agent."""

from __future__ import annotations

import os

from reminder_agent.client import ResponsesClient
from reminder_agent.models import InfrastructureFailure


def provider_name() -> str:
    provider = os.environ.get("REMINDER_PROVIDER", "openai").strip().casefold()
    if provider not in {"openai", "ollama"}:
        raise InfrastructureFailure("REMINDER_PROVIDER must be openai or ollama")
    return provider


def create_client() -> ResponsesClient:
    provider = provider_name()
    if provider == "ollama":
        from reminder_agent.ollama_client import OllamaClient

        return OllamaClient()
    from reminder_agent.openai_client import OpenAIResponsesClient

    return OpenAIResponsesClient()
