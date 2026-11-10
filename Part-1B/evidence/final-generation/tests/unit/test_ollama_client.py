import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from reminder_agent.models import IncompleteModelOutput, InfrastructureFailure
from reminder_agent.ollama_client import OllamaClient
from reminder_agent.provider_schema import PROVIDER_SCHEMA


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.payload


def test_ollama_client_sends_schema_to_loopback_and_returns_model_content():
    captured = {}

    def opener(request, *, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse({"message": {"content": '{"intent":"clarify"}'}})

    client = OllamaClient(model="qwen-test", opener=opener)
    output = client.generate(
        {"request": "Remind me tomorrow", "reference_now": "2030-01-01T09:00:00+05:30"},
        "Return the required JSON.",
    )

    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert output == '{"intent":"clarify"}'
    assert captured["request"].full_url == "http://127.0.0.1:11434/api/chat"
    assert captured["request"].get_header("Authorization") is None
    assert captured["timeout"] == 60
    assert payload["model"] == "qwen-test"
    assert payload["format"] == PROVIDER_SCHEMA
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0.2
    assert "tools" not in payload


def test_ollama_client_rejects_non_loopback_endpoint():
    with pytest.raises(InfrastructureFailure, match="loopback"):
        OllamaClient(model="qwen-test", base_url="https://example.com")


def test_ollama_client_classifies_service_errors_without_response_body():
    def opener(request, *, timeout):
        raise HTTPError(request.full_url, 500, "failure", {}, BytesIO(b"sensitive body"))

    client = OllamaClient(model="qwen-test", opener=opener)
    with pytest.raises(InfrastructureFailure, match="HTTP 500") as captured:
        client.generate({"request": "private request"}, "rules")
    assert "sensitive body" not in str(captured.value)


def test_ollama_client_rejects_invalid_or_empty_output():
    invalid_json = OllamaClient(
        model="qwen-test",
        opener=lambda request, *, timeout: FakeResponse({"unexpected": True}),
    )
    with pytest.raises(IncompleteModelOutput, match="no structured output"):
        invalid_json.generate({"request": "request"}, "rules")
