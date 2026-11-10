from types import SimpleNamespace

import pytest

from reminder_agent.models import IncompleteModelOutput, InfrastructureFailure, ProviderRefusal
from reminder_agent.openai_client import OpenAIResponsesClient


class FakeResponses:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeSdkClient:
    def __init__(self, responses):
        self.responses = responses


def test_responses_adapter_uses_strict_schema_and_registers_no_tools():
    response = SimpleNamespace(status="completed", output_text='{"intent":"clarify"}', output=[])
    responses = FakeResponses(response=response)
    client = OpenAIResponsesClient(model="test-model", sdk_client=FakeSdkClient(responses))
    request = {
        "request": "Call the dentist tomorrow at 9 AM",
        "reference_now": "2026-11-10T10:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "existing_reminders": [],
    }
    assert client.generate(request, "fixed system prompt") == response.output_text
    call = responses.calls[0]
    assert call["model"] == "test-model"
    assert call["store"] is False
    assert "tools" not in call
    assert call["text"]["format"]["strict"] is True
    assert call["text"]["format"]["schema"]["additionalProperties"] is False
    assert call["input"][0] == {"role": "system", "content": "fixed system prompt"}
    assert call["input"][1]["role"] == "user"


def test_missing_key_is_an_infrastructure_failure_without_secret_output(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = OpenAIResponsesClient(model="test-model")
    with pytest.raises(InfrastructureFailure, match="OPENAI_API_KEY is not configured") as error:
        client.generate({}, "system")
    assert "secret-sentinel" not in str(error.value)


def test_api_exception_body_is_not_exposed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-sentinel")
    responses = FakeResponses(error=RuntimeError("secret-sentinel echoed in provider error"))
    client = OpenAIResponsesClient(model="test-model", sdk_client=FakeSdkClient(responses))
    with pytest.raises(InfrastructureFailure) as error:
        client.generate({}, "system")
    assert "secret-sentinel" not in str(error.value)


def test_refusal_and_incomplete_responses_have_separate_categories():
    refusal = SimpleNamespace(
        status="completed",
        output_text="",
        output=[SimpleNamespace(content=[{"type": "refusal"}])],
    )
    refused_client = OpenAIResponsesClient(
        model="test-model", sdk_client=FakeSdkClient(FakeResponses(response=refusal))
    )
    with pytest.raises(ProviderRefusal):
        refused_client.generate({}, "system")

    incomplete = SimpleNamespace(status="incomplete", output_text="{", output=[])
    incomplete_client = OpenAIResponsesClient(
        model="test-model", sdk_client=FakeSdkClient(FakeResponses(response=incomplete))
    )
    with pytest.raises(IncompleteModelOutput):
        incomplete_client.generate({}, "system")
