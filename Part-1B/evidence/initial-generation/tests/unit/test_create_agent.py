import pytest

from reminder_agent.agent import ReminderAgent


def test_explicit_request_returns_a_valid_future_create_proposal(
    request_envelope, ready_create_result, fake_client_factory
):
    client = fake_client_factory([ready_create_result])
    result = ReminderAgent(client=client).run(request_envelope)
    assert result == ready_create_result
    sent_request, system_prompt = client.calls[0]
    assert sent_request["reference_now"] == request_envelope["reference_now"]
    assert sent_request["timezone"] == "Asia/Kolkata"
    assert "untrusted" in system_prompt.casefold()


def test_relative_date_is_grounded_in_the_supplied_reference_time(
    request_envelope, ready_create_result, fake_client_factory
):
    request_envelope["request"] = "Remind me to submit the assignment tomorrow at 9 AM."
    client = fake_client_factory([ready_create_result])
    result = ReminderAgent(client=client).run(request_envelope)
    assert result["reminder"]["due_at"] == "2026-11-11T09:00:00+05:30"
    assert client.calls[0][0]["reference_now"] == "2026-11-10T10:00:00+05:30"


def test_missing_date_and_time_produce_a_structured_clarification(fake_client_factory):
    request = {
        "request": "Remind me to call the dentist",
        "reference_now": "2026-11-10T10:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "existing_reminders": [],
    }
    clarification = {
        "intent": "clarify",
        "status": "needs_clarification",
        "reminder": None,
        "target_reminder_id": None,
        "missing_fields": ["date", "time"],
        "clarification_question": "What date and time should I use?",
        "reason_code": None,
    }
    client = fake_client_factory([clarification])
    result = ReminderAgent(client=client).run(request)
    assert result == clarification


def test_missing_timezone_is_clarified_without_calling_the_model(fake_client_factory):
    request = {
        "request": "Remind me tomorrow at 9 to call the dentist",
        "reference_now": "2026-11-10T10:00:00+05:30",
        "timezone": "Invalid/Zone",
        "existing_reminders": [],
    }
    client = fake_client_factory([])
    result = ReminderAgent(client=client).run(request)
    assert result["status"] == "needs_clarification"
    assert result["missing_fields"] == ["timezone"]
    assert not client.calls


def test_malformed_request_is_rejected_without_calling_the_model(fake_client_factory):
    request = {"request": "", "reference_now": "not-a-timestamp", "timezone": "Asia/Kolkata"}
    client = fake_client_factory([])
    result = ReminderAgent(client=client).run(request)
    assert result["intent"] == "reject"
    assert result["status"] == "rejected"
    assert result["reason_code"] == "malformed_input"
    assert not client.calls
