from __future__ import annotations

from datetime import timedelta

from reminder_agent.agent import ReminderAgent
from reminder_agent.request_analysis import apply_request_guardrails, assess_request
from reminder_agent.validation import parse_request_envelope


def _request(text: str, reminders: list[dict[str, str]] | None = None):
    return parse_request_envelope(
        {
            "request": text,
            "reference_now": "2026-11-10T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "existing_reminders": reminders or [],
        }
    )


def _ready_output(
    *, intent: str = "create", due_at: str = "2026-11-11T18:00:00+05:30"
) -> dict:
    return {
        "intent": intent,
        "status": "ready",
        "reminder": {
            "title": "Pay the bill",
            "due_at": due_at,
            "timezone": "Asia/Kolkata",
        },
        "target_reminder_id": None,
        "missing_fields": [],
        "clarification_question": None,
        "reason_code": None,
    }


class _StaticClient:
    def __init__(self, output: dict) -> None:
        self.output = output

    def generate(self, request: dict, system_prompt: str) -> dict:
        return self.output


def test_complete_explicit_create_has_no_missing_fields() -> None:
    request = _request("Remind me to pay rent tomorrow at 9 AM.")

    assessment = assess_request(request)

    assert assessment.intent == "create"
    assert assessment.missing_fields == ()


def test_create_duration_is_a_complete_relative_schedule() -> None:
    assessment = assess_request(_request("Remind me to check the oven in 15 minutes."))

    assert assessment.missing_fields == ()
    assert assessment.relative_duration == timedelta(minutes=15)


def test_create_relative_duration_is_computed_from_reference_time() -> None:
    request = _request("Remind me to check the oven in 15 minutes.")
    output = _ready_output(due_at="2026-11-10T11:15:00+05:30")

    guarded, reasons = apply_request_guardrails(output, request)

    assert guarded["reminder"]["due_at"] == "2026-11-10T10:15:00+05:30"
    assert "relative_duration_applied" in reasons


def test_weekday_without_time_requires_time_clarification() -> None:
    assessment = assess_request(_request("Remind me to call the dentist on Friday."))

    assert assessment.missing_fields == ("time",)


def test_task_without_date_or_time_requires_both() -> None:
    assessment = assess_request(_request("Call the dentist."))

    assert assessment.missing_fields == ("date", "time")


def test_date_and_time_without_task_requires_title() -> None:
    assessment = assess_request(_request("Remind me tomorrow at 9 AM."))

    assert assessment.missing_fields == ("title",)


def test_month_without_day_and_bare_hour_are_incomplete() -> None:
    assessment = assess_request(_request("Set a reminder for next month at 4."))

    assert assessment.missing_fields == ("title", "date", "time")


def test_snooze_without_matching_existing_reminder_requires_target() -> None:
    assessment = assess_request(_request("Snooze my medicine reminder for 30 minutes."))

    assert assessment.intent == "snooze"
    assert assessment.missing_fields == ("existing_reminder",)


def test_similarly_named_targets_are_ambiguous() -> None:
    request = _request(
        "Move my dentist appointment to November 12, 2026 at 2 PM.",
        [
            {"id": "R-7", "title": "Dentist cleaning", "due_at": "2026-11-11T09:00:00+05:30"},
            {"id": "R-9", "title": "Dentist follow-up", "due_at": "2026-11-13T10:00:00+05:30"},
        ],
    )

    assert assess_request(request).missing_fields == ("existing_reminder",)


def test_single_matching_target_is_selected() -> None:
    request = _request(
        "Move my dentist appointment to November 12, 2026 at 2 PM.",
        [{"id": "R-7", "title": "Dentist appointment", "due_at": "2026-11-11T09:00:00+05:30"}],
    )

    assessment = assess_request(request)

    assert assessment.intent == "reschedule"
    assert assessment.missing_fields == ()
    assert assessment.target_reminder_id == "R-7"


def test_past_ready_proposal_is_rejected_by_local_policy() -> None:
    request = _request("Remind me to pay rent yesterday at 9 AM.")
    output = _ready_output(due_at="2026-11-09T09:00:00+05:30")

    guarded, reasons = apply_request_guardrails(output, request)

    assert guarded["status"] == "rejected"
    assert guarded["reason_code"] == "past_datetime"
    assert "past_datetime_rejected" in reasons


def test_snooze_intent_and_duration_are_normalized_from_request_context() -> None:
    request = _request(
        "Snooze my medicine reminder for 2 hours.",
        [{"id": "R-100", "title": "Take medicine", "due_at": "2026-11-10T11:00:00+05:30"}],
    )
    output = _ready_output(intent="reschedule", due_at="2026-11-10T13:00:00+05:30")

    guarded, reasons = apply_request_guardrails(output, request)

    assert guarded["intent"] == "snooze"
    assert guarded["target_reminder_id"] == "R-100"
    assert guarded["reminder"]["title"] == "Take medicine"
    assert guarded["reminder"]["due_at"] == "2026-11-10T13:00:00+05:30"
    assert "snooze_duration_applied" in reasons


def test_agent_clarifies_when_model_proposes_ready_without_requested_time() -> None:
    agent = ReminderAgent(client=_StaticClient(_ready_output()))

    result = agent.run(
        {
            "request": "Remind me to call the dentist on Friday.",
            "reference_now": "2026-11-10T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
        }
    )

    assert result["intent"] == "clarify"
    assert result["missing_fields"] == ["time"]
    assert "clarification_for_missing_or_ambiguous_request_fields" in agent.policy_adjustments


def test_agent_corrects_explicit_snooze_intent_and_target() -> None:
    agent = ReminderAgent(client=_StaticClient(_ready_output()))

    result = agent.run(
        {
            "request": "Snooze my medicine reminder for 2 hours.",
            "reference_now": "2026-11-10T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "existing_reminders": [
                {"id": "R-100", "title": "Take medicine", "due_at": "2026-11-10T11:00:00+05:30"}
            ],
        }
    )

    assert result["intent"] == "snooze"
    assert result["target_reminder_id"] == "R-100"
    assert result["reminder"]["title"] == "Take medicine"
    assert result["reminder"]["due_at"] == "2026-11-10T13:00:00+05:30"


def test_agent_rejects_model_proposal_for_resolved_past_time() -> None:
    agent = ReminderAgent(
        client=_StaticClient(
            _ready_output(due_at="2026-11-09T09:00:00+05:30")
        )
    )

    result = agent.run(
        {
            "request": "Remind me to pay rent yesterday at 9 AM.",
            "reference_now": "2026-11-10T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
        }
    )

    assert result["intent"] == "reject"
    assert result["reason_code"] == "past_datetime"
