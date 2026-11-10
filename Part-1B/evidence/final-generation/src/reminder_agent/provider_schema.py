"""The strict Structured Outputs schema using the supported provider subset."""

RESULT_FIELDS = [
    "intent",
    "status",
    "reminder",
    "target_reminder_id",
    "missing_fields",
    "clarification_question",
    "reason_code",
]

PROVIDER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": RESULT_FIELDS,
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["create", "reschedule", "snooze", "clarify", "reject"],
        },
        "status": {
            "type": "string",
            "enum": ["ready", "needs_clarification", "rejected"],
        },
        "reminder": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "due_at", "timezone"],
                    "properties": {
                        "title": {"type": "string"},
                        "due_at": {"type": "string"},
                        "timezone": {"type": "string"},
                    },
                },
            ]
        },
        "target_reminder_id": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "missing_fields": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["title", "date", "time", "timezone", "existing_reminder"],
            },
        },
        "clarification_question": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "reason_code": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [
                        "malformed_input",
                        "past_datetime",
                        "unsupported_action",
                        "unsafe_request",
                    ],
                },
                {"type": "null"},
            ]
        },
    },
}
