import pytest

from reminder_agent.agent import ReminderAgent
from reminder_agent.models import MalformedRequest, OutputValidationError
from reminder_agent.validation import parse_request_envelope, validate_output


def test_empty_oversized_and_missing_reference_requests_are_rejected(
    fake_client_factory,
):
    client = fake_client_factory([])
    agent = ReminderAgent(client=client)
    invalid_envelopes = [
        {"request": "", "reference_now": "2026-11-10T10:00:00+05:30"},
        {"request": "x" * 4001, "reference_now": "2026-11-10T10:00:00+05:30"},
        {"request": "Call the dentist tomorrow", "reference_now": "not-a-date"},
    ]
    for envelope in invalid_envelopes:
        assert agent.run(envelope)["reason_code"] == "malformed_input"
    assert not client.calls


def test_invalid_context_timestamp_and_duplicate_ids_are_malformed():
    base = {
        "request": "Move dentist appointment to tomorrow at 9 AM",
        "reference_now": "2026-11-10T10:00:00+05:30",
        "timezone": "Asia/Kolkata",
    }
    with pytest.raises(MalformedRequest):
        parse_request_envelope(
            {
                **base,
                "existing_reminders": [
                    {"id": "R-1", "title": "Dentist", "due_at": "2026-11-11T09:00:00"}
                ],
            }
        )
    reminder = {"id": "R-1", "title": "Dentist", "due_at": "2026-11-11T09:00:00+05:30"}
    with pytest.raises(MalformedRequest, match="unique"):
        parse_request_envelope({**base, "existing_reminders": [reminder, reminder]})


def test_nonexistent_daylight_saving_time_is_rejected(request_envelope, ready_create_result):
    request_envelope["request"] = "Remind me at the daylight saving transition."
    request_envelope["reference_now"] = "2026-03-07T12:00:00-05:00"
    request_envelope["timezone"] = "America/New_York"
    result = {
        **ready_create_result,
        "reminder": {
            "title": "Daylight saving transition",
            "due_at": "2026-03-08T02:30:00-05:00",
            "timezone": "America/New_York",
        },
    }
    with pytest.raises(OutputValidationError, match="offset does not match"):
        validate_output(result, parse_request_envelope(request_envelope))


def test_time_zone_absence_uses_configured_default_and_invalid_zone_clarifies(
    fake_client_factory, ready_create_result
):
    no_timezone = {
        "request": "Remind me to submit tomorrow at 9 AM",
        "reference_now": "2026-11-10T10:00:00+05:30",
    }
    client = fake_client_factory([ready_create_result])
    agent = ReminderAgent(client=client, default_timezone="Asia/Kolkata")
    assert agent.run(no_timezone)["status"] == "ready"

    invalid = {**no_timezone, "timezone": "No/Such_Zone"}
    no_call_client = fake_client_factory([])
    result = ReminderAgent(client=no_call_client).run(invalid)
    assert result["status"] == "needs_clarification"
    assert result["missing_fields"] == ["timezone"]
    assert not no_call_client.calls
