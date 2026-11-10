from reminder_agent.agent import ReminderAgent


def test_reschedule_targets_the_single_matching_context_reminder(
    request_envelope, fake_client_factory
):
    request_envelope["request"] = "Move my dentist appointment to November 12 at 2 PM."
    request_envelope["existing_reminders"] = [
        {"id": "R-7", "title": "Dentist", "due_at": "2026-11-11T09:00:00+05:30"}
    ]
    expected = {
        "intent": "reschedule",
        "status": "ready",
        "reminder": {
            "title": "Dentist appointment",
            "due_at": "2026-11-12T14:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        "target_reminder_id": "R-7",
        "missing_fields": [],
        "clarification_question": None,
        "reason_code": None,
    }
    result = ReminderAgent(client=fake_client_factory([expected])).run(request_envelope)
    assert result == expected


def test_no_matching_target_requires_clarification(request_envelope, fake_client_factory):
    request_envelope["request"] = "Snooze my dentist appointment by 30 minutes."
    request_envelope["existing_reminders"] = []
    expected = {
        "intent": "clarify",
        "status": "needs_clarification",
        "reminder": None,
        "target_reminder_id": None,
        "missing_fields": ["existing_reminder"],
        "clarification_question": "Which reminder should I snooze?",
        "reason_code": None,
    }
    result = ReminderAgent(client=fake_client_factory([expected])).run(request_envelope)
    assert result == expected
