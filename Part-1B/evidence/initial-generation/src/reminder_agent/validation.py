"""Independent JSON Schema, time-zone, and cross-field validation."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker

from reminder_agent.models import (
    InvalidTimezone,
    MalformedRequest,
    OutputValidationError,
    ReminderRequest,
    parse_aware_datetime,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_SCHEMA_PATH = ROOT / "specs" / "001-reminder-agent" / "contracts" / "reminder-output.schema.json"
SNOOZE_DURATION = re.compile(
    r"(?<![\w-])(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|days?|weeks?)\b",
    re.IGNORECASE,
)
SNOOZE_UNITS = {
    "minute": 60,
    "min": 60,
    "hour": 3600,
    "hr": 3600,
    "day": 86400,
    "week": 604800,
}


@lru_cache(maxsize=1)
def output_validator() -> Draft202012Validator:
    try:
        schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("the local reminder output schema is unavailable") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def parse_request_envelope(value: Any, *, default_timezone: str = "Asia/Kolkata") -> ReminderRequest:
    allowed = {"request", "reference_now", "timezone", "existing_reminders"}
    required = {"request", "reference_now"}
    if not isinstance(value, dict) or not required.issubset(value) or not set(value).issubset(allowed):
        raise MalformedRequest("request envelope has missing or unknown fields")
    request_text = value["request"]
    if not isinstance(request_text, str) or not request_text.strip() or len(request_text) > 4000:
        raise MalformedRequest("request must contain 1 to 4000 characters")
    reference_now = parse_aware_datetime(value["reference_now"], "reference_now")

    raw_timezone = value.get("timezone")
    timezone_name = raw_timezone.strip() if isinstance(raw_timezone, str) else default_timezone
    if not timezone_name:
        raise InvalidTimezone("timezone is missing")
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise InvalidTimezone("timezone must be a valid IANA time-zone identifier") from exc

    raw_reminders = value.get("existing_reminders", [])
    if not isinstance(raw_reminders, list):
        raise MalformedRequest("existing_reminders must be an array")
    reminders = []
    seen_ids: set[str] = set()
    for raw in raw_reminders:
        if (
            not isinstance(raw, dict)
            or set(raw) != {"id", "title", "due_at"}
            or not isinstance(raw["id"], str)
            or not raw["id"].strip()
            or not isinstance(raw["title"], str)
            or not raw["title"].strip()
        ):
            raise MalformedRequest("each existing reminder needs an ID, title, and due_at")
        reminder_id = raw["id"].strip()
        if reminder_id in seen_ids:
            raise MalformedRequest("existing reminder IDs must be unique")
        seen_ids.add(reminder_id)
        reminders.append(
            {
                "id": reminder_id,
                "title": raw["title"].strip(),
                "due_at": parse_aware_datetime(raw["due_at"], "existing reminder due_at"),
            }
        )
    from reminder_agent.models import ExistingReminder

    return ReminderRequest(
        request=request_text.strip(),
        reference_now=reference_now,
        timezone=timezone_name,
        existing_reminders=tuple(ExistingReminder(**item) for item in reminders),
    )


def parse_output_json(value: str | bytes | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise OutputValidationError("model output is not valid JSON") from exc
    if not isinstance(value, dict):
        raise OutputValidationError("model output must be a JSON object")
    return value


def _timestamp(value: str, field: str) -> datetime:
    try:
        normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
        result = datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as exc:
        raise OutputValidationError(f"{field} must be an ISO 8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise OutputValidationError(f"{field} must include an explicit UTC offset")
    return result


def _duration_from_snooze_request(text: str) -> timedelta | None:
    matches = list(SNOOZE_DURATION.finditer(text))
    if not matches:
        return None
    if len(matches) != 1:
        raise OutputValidationError("snooze request contains multiple plausible durations")
    amount = float(matches[0].group(1))
    if amount <= 0:
        raise OutputValidationError("snooze duration must be positive")
    unit = matches[0].group(2).casefold().rstrip("s")
    seconds = amount * SNOOZE_UNITS[unit]
    return timedelta(seconds=seconds)


def validate_output(value: Any, request: ReminderRequest) -> dict[str, Any]:
    output = parse_output_json(value) if isinstance(value, (str, bytes)) else value
    errors = sorted(output_validator().iter_errors(output), key=lambda error: list(error.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "output"
        raise OutputValidationError(f"{location}: {first.message}")

    intent = output["intent"]
    status = output["status"]
    reminder = output["reminder"]
    target = output["target_reminder_id"]
    missing = output["missing_fields"]
    question = output["clarification_question"]
    reason = output["reason_code"]

    if status == "ready":
        if intent not in {"create", "reschedule", "snooze"}:
            raise OutputValidationError("ready status requires a create, reschedule, or snooze intent")
        if reminder is None or missing or question is not None or reason is not None:
            raise OutputValidationError("ready result has inconsistent nullable fields")
        if not reminder["title"].strip():
            raise OutputValidationError("ready reminder title must not be empty")
        if reminder["timezone"] != request.timezone:
            raise OutputValidationError("ready reminder timezone must match the request timezone")
        due_at = _timestamp(reminder["due_at"], "reminder.due_at")
        try:
            zone = ZoneInfo(reminder["timezone"])
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise OutputValidationError("reminder timezone is not a valid IANA identifier") from exc
        zoned_due = due_at.astimezone(zone)
        if (
            zoned_due.utcoffset() != due_at.utcoffset()
            or zoned_due.replace(tzinfo=None) != due_at.replace(tzinfo=None)
        ):
            raise OutputValidationError("reminder timestamp offset does not match its IANA timezone")
        if due_at <= request.reference_now:
            raise OutputValidationError("ready reminder due_at must be later than reference_now")
        if intent == "create" and target is not None:
            raise OutputValidationError("ready create result must not name a target reminder")
        if intent in {"reschedule", "snooze"}:
            targets = [item for item in request.existing_reminders if item.id == target]
            if not target or len(targets) != 1:
                raise OutputValidationError("ready reschedule/snooze must name one supplied reminder")
        if intent == "snooze":
            duration = _duration_from_snooze_request(request.request)
            if duration is not None:
                target_reminder = next(
                    item for item in request.existing_reminders if item.id == target
                )
                reference_utc = request.reference_now.astimezone(UTC)
                target_utc = target_reminder.due_at.astimezone(UTC)
                expected_due = max(reference_utc, target_utc) + duration
                if due_at.astimezone(UTC) != expected_due:
                    raise OutputValidationError(
                        "snooze due time must equal the later of reference_now or current due_at plus the requested duration"
                    )
    elif status == "needs_clarification":
        if (
            intent != "clarify"
            or reminder is not None
            or target is not None
            or not missing
            or not question
            or reason is not None
        ):
            raise OutputValidationError("clarification result has inconsistent fields")
    else:
        if (
            intent != "reject"
            or reminder is not None
            or target is not None
            or missing
            or question is not None
            or reason is None
        ):
            raise OutputValidationError("rejected result has inconsistent fields")
    return output
