import pytest

from reminder_agent.client_factory import create_client, provider_name
from reminder_agent.models import InfrastructureFailure
from reminder_agent.ollama_client import OllamaClient
from reminder_agent.openai_client import OpenAIResponsesClient


def test_provider_factory_selects_local_ollama(monkeypatch):
    monkeypatch.setenv("REMINDER_PROVIDER", "ollama")
    monkeypatch.setenv("REMINDER_MODEL", "qwen-test")
    assert provider_name() == "ollama"
    assert isinstance(create_client(), OllamaClient)


def test_provider_factory_keeps_openai_available(monkeypatch):
    monkeypatch.setenv("REMINDER_PROVIDER", "openai")
    assert isinstance(create_client(), OpenAIResponsesClient)


def test_provider_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("REMINDER_PROVIDER", "unknown")
    with pytest.raises(InfrastructureFailure, match="REMINDER_PROVIDER"):
        create_client()
