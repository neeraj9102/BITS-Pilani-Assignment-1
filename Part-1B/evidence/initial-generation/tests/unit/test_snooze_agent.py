import pytest

from reminder_agent.models import OutputValidationError
from reminder_agent.validation import parse_request_envelope, validate_output


def snooze_case(due_at):
    return {
        "intent": "snooze",
        "status": "ready",
        "reminder": {
            "title": "Dentist appointment",
            "due_at": due_at,
            "timezone": "Asia/Kolkata",
        },
        "target_reminder_id": "R-8",
        "missing_fields": [],
        "clarification_question": None,
        "reason_code": None,
    }


@pytest.mark.parametrize(
    ("reference_now", "current_due", "request_text", "expected_due"),
    [
        (
            "2026-11-10T10:00:00+05:30",
            "2026-11-10T09:00:00+05:30",
            "Snooze my dentist appointment by 30 minutes.",
            "2026-11-10T10:30:00+05:30",
        ),
        (
            "2026-11-10T10:00:00+05:30",
            "2026-11-10T11:00:00+05:30",
            "Snooze my dentist appointment for 2 hours.",
            "2026-11-10T13:00:00+05:30",
        ),
    ],
)
def test_snooze_due_time_uses_later_reference_or_current_due(
    reference_now, current_due, request_text, expected_due
):
    envelope = {
        "request": request_text,
        "reference_now": reference_now,
        "timezone": "Asia/Kolkata",
        "existing_reminders": [
            {"id": "R-8", "title": "Dentist appointment", "due_at": current_due}
        ],
    }
    request = parse_request_envelope(envelope)
    result = snooze_case(expected_due)
    assert validate_output(result, request) == result


def test_snooze_due_time_that_ignores_requested_duration_is_rejected():
    envelope = {
        "request": "Snooze my dentist appointment for 2 hours.",
        "reference_now": "2026-11-10T10:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "existing_reminders": [
            {"id": "R-8", "title": "Dentist appointment", "due_at": "2026-11-10T11:00:00+05:30"}
        ],
    }
    result = snooze_case("2026-11-10T14:00:00+05:30")
    with pytest.raises(OutputValidationError, match="snooze due time"):
        validate_output(result, parse_request_envelope(envelope))


def test_non_snooze_intent_is_not_subject_to_snooze_arithmetic(request_envelope):
    request = parse_request_envelope(request_envelope)
    result = {
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
    assert validate_output(result, request) == result
