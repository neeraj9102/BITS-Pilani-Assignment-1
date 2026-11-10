import json

import pytest

from reminder_agent.models import parse_aware_datetime


class FakeClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, request, system_prompt):
        self.calls.append((request, system_prompt))
        output = self.outputs.pop(0)
        return json.dumps(output) if isinstance(output, dict) else output


@pytest.fixture
def request_envelope():
    return {
        "request": "Remind me to submit the assignment tomorrow at 9 AM.",
        "reference_now": "2026-11-10T10:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "existing_reminders": [],
    }


@pytest.fixture
def ready_create_result():
    return {
        "intent": "create",
        "status": "ready",
        "reminder": {
            "title": "Submit the assignment",
            "due_at": "2026-11-11T09:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        "target_reminder_id": None,
        "missing_fields": [],
        "clarification_question": None,
        "reason_code": None,
    }


@pytest.fixture
def fake_client_factory():
    return FakeClient


@pytest.fixture
def fixed_now():
    return parse_aware_datetime("2026-11-10T10:00:00+05:30", "reference_now")
