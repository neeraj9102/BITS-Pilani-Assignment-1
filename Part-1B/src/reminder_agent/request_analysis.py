"""Conservative request checks that prevent unsafe or incomplete proposals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from reminder_agent.models import ReminderRequest

_SNOOZE = re.compile(r"\bsnooz(?:e|ing)\b", re.IGNORECASE)
_RESCHEDULE = re.compile(
    r"\b(?:move|reschedule|postpone|delay|shift|push\s+back|change)\b",
    re.IGNORECASE,
)
_DURATION = re.compile(
    r"(?<![\w-])(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|days?|weeks?)\b",
    re.IGNORECASE,
)
_IN_DURATION = re.compile(
    r"\bin\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|days?|weeks?)\b",
    re.IGNORECASE,
)
_DURATION_SECONDS = {
    "minute": 60,
    "min": 60,
    "hour": 3600,
    "hr": 3600,
    "day": 86400,
    "week": 604800,
}
_MONTHS = (
    "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    "jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)
_WEEKDAYS = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"
_DATE_PATTERNS = (
    re.compile(r"\b(?:today|tomorrow|yesterday|tonight)\b", re.IGNORECASE),
    re.compile(rf"\b(?:(?:next|this|coming)\s+)?(?:{_WEEKDAYS})\b", re.IGNORECASE),
    re.compile(
        rf"\b(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:{_MONTHS})(?:\s+\d{{4}})?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(r"\b(?:next|this)\s+(?:month|week|year)\b", re.IGNORECASE),
)
_EXPLICIT_TIME = re.compile(
    r"\b(?:noon|midnight|\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?|"
    r"\d{1,2}\s*[ap]\.?m\.?)\b",
    re.IGNORECASE,
)
_AT_HOUR = re.compile(r"\bat\s+(\d{1,2})(?!\s*:\s*\d)", re.IGNORECASE)
_AT_TIME = re.compile(
    r"\bat\s+(?:\d{1,2}(?::\d{2})?\s*(?:[ap]\.?m\.?)?|noon|midnight)\b",
    re.IGNORECASE,
)
_STANDALONE_TIME = re.compile(
    r"\b(?:\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?|\d{1,2}\s*[ap]\.?m\.?|noon|midnight)\b",
    re.IGNORECASE,
)
_TASK_PREFIX = re.compile(
    r"^\s*(?:please\s+)?(?:remind\s+me(?:\s+to)?|"
    r"(?:set|create|add)\s+(?:me\s+)?(?:a\s+)?reminder(?:\s+to)?|"
    r"schedule\s+(?:me\s+)?(?:a\s+)?reminder(?:\s+to)?)\s*",
    re.IGNORECASE,
)
_STOPWORDS = {
    "a", "an", "and", "at", "by", "for", "me", "my", "on", "please",
    "remind", "reminder", "reminders", "set", "the", "this", "to", "with",
    "tomorrow", "today", "yesterday", "tonight", "next", "coming", "month",
    "week", "year", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "move", "reschedule", "postpone", "delay", "shift",
    "push", "back", "change", "snooze", "snoozing", "hour", "hours", "hr",
    "hrs", "minute", "minutes", "min", "mins", "day", "days", "weeks",
}


@dataclass(frozen=True)
class RequestAssessment:
    """High-confidence intent and completeness facts from the request envelope."""

    intent: str
    missing_fields: tuple[str, ...]
    target_reminder_id: str | None
    snooze_duration: timedelta | None
    relative_duration: timedelta | None


def _intent(text: str) -> str:
    if _SNOOZE.search(text):
        return "snooze"
    if _RESCHEDULE.search(text):
        return "reschedule"
    return "create"


def _duration(text: str) -> timedelta | None:
    matches = list(_DURATION.finditer(text))
    if len(matches) != 1:
        return None
    amount = float(matches[0].group(1))
    if amount <= 0:
        return None
    unit = matches[0].group(2).casefold().rstrip("s")
    return timedelta(seconds=amount * _DURATION_SECONDS[unit])


def _relative_duration(text: str) -> timedelta | None:
    matches = list(_IN_DURATION.finditer(text))
    if len(matches) != 1:
        return None
    amount = float(matches[0].group(1))
    if amount <= 0:
        return None
    unit = matches[0].group(2).casefold().rstrip("s")
    return timedelta(seconds=amount * _DURATION_SECONDS[unit])


def _date_complete(text: str) -> bool:
    date_match = None
    for pattern in _DATE_PATTERNS:
        date_match = pattern.search(text)
        if date_match:
            break
    if date_match is None:
        return False
    matched_text = date_match.group(0).casefold()
    if re.fullmatch(r"(?:next|this)\s+(?:month|week|year)", matched_text):
        return False
    return True


def _time_complete(text: str) -> bool:
    if _EXPLICIT_TIME.search(text):
        return True
    match = _AT_HOUR.search(text)
    if match is None:
        return False
    hour = int(match.group(1))
    return hour == 0 or hour >= 13


def _remove_temporal_phrases(text: str) -> str:
    result = text
    for pattern in _DATE_PATTERNS:
        result = pattern.sub(" ", result)
    result = _AT_TIME.sub(" ", result)
    result = _STANDALONE_TIME.sub(" ", result)
    result = _DURATION.sub(" ", result)
    return re.sub(r"\s+", " ", result).strip(" \t\r\n,.;:!?-")


def _has_task(text: str) -> bool:
    residual = _TASK_PREFIX.sub("", _remove_temporal_phrases(text))
    words = [word.casefold() for word in re.findall(r"[^\W_]+", residual, flags=re.UNICODE)]
    meaningful = [word for word in words if word not in _STOPWORDS and not word.isdigit()]
    return bool(meaningful)


def _target_tokens(text: str) -> set[str]:
    residual = _remove_temporal_phrases(text)
    words = re.findall(r"[^\W_]+", residual.casefold(), flags=re.UNICODE)
    return {word for word in words if word not in _STOPWORDS and not word.isdigit()}


def _matching_target_id(request: ReminderRequest) -> str | None:
    query = _target_tokens(request.request)
    if not query:
        return None
    scored = []
    for reminder in request.existing_reminders:
        title_tokens = {
            word
            for word in re.findall(r"[^\W_]+", reminder.title.casefold(), flags=re.UNICODE)
            if word not in _STOPWORDS
        }
        score = len(query & title_tokens)
        if score:
            scored.append((score, reminder.id))
    if not scored:
        return None
    best = max(score for score, _ in scored)
    winners = [reminder_id for score, reminder_id in scored if score == best]
    return winners[0] if len(winners) == 1 else None


def assess_request(request: ReminderRequest) -> RequestAssessment:
    """Find only high-confidence missing fields and target ambiguity."""
    text = request.request
    intent = _intent(text)
    missing: list[str] = []
    target_id = None
    snooze_duration = None
    relative_duration = None

    if intent == "snooze":
        target_id = _matching_target_id(request)
        if target_id is None:
            missing.append("existing_reminder")
        snooze_duration = _duration(text)
        if snooze_duration is None:
            missing.append("time")
    elif intent == "reschedule":
        target_id = _matching_target_id(request)
        if target_id is None:
            missing.append("existing_reminder")
        if not _date_complete(text):
            missing.append("date")
        if not _time_complete(text):
            missing.append("time")
    else:
        if not _has_task(text):
            missing.append("title")
        relative_duration = _relative_duration(text)
        if relative_duration is None:
            if not _date_complete(text):
                missing.append("date")
            if not _time_complete(text):
                missing.append("time")

    return RequestAssessment(
        intent=intent,
        missing_fields=tuple(missing),
        target_reminder_id=target_id,
        snooze_duration=snooze_duration,
        relative_duration=relative_duration,
    )


def _clarification(missing_fields: tuple[str, ...]) -> dict:
    details = ", ".join(missing_fields)
    return {
        "intent": "clarify",
        "status": "needs_clarification",
        "reminder": None,
        "target_reminder_id": None,
        "missing_fields": list(missing_fields),
        "clarification_question": f"Please provide the missing information: {details}.",
        "reason_code": None,
    }


def apply_request_guardrails(
    output: dict, request: ReminderRequest
) -> tuple[dict, list[str]]:
    """Enforce clearly missing fields, target selection, action, and time safety."""
    assessment = assess_request(request)
    if assessment.missing_fields:
        if (
            output.get("status") == "needs_clarification"
            and set(output.get("missing_fields", [])) == set(assessment.missing_fields)
            and isinstance(output.get("clarification_question"), str)
            and output["clarification_question"].strip()
        ):
            return output, []
        return _clarification(assessment.missing_fields), [
            "clarification_for_missing_or_ambiguous_request_fields"
        ]

    if output.get("status") != "ready" or not isinstance(output.get("reminder"), dict):
        return output, []

    guarded = {
        **output,
        "reminder": dict(output["reminder"]),
    }
    adjustments: list[str] = []
    expected_intent = assessment.intent
    if guarded.get("intent") != expected_intent:
        guarded["intent"] = expected_intent
        adjustments.append("intent_aligned_with_explicit_request_action")

    if expected_intent == "create":
        if guarded.get("target_reminder_id") is not None:
            guarded["target_reminder_id"] = None
            adjustments.append("create_target_cleared")
    else:
        if guarded.get("target_reminder_id") != assessment.target_reminder_id:
            guarded["target_reminder_id"] = assessment.target_reminder_id
            adjustments.append("target_aligned_with_unique_context_match")
        target = next(
            item
            for item in request.existing_reminders
            if item.id == assessment.target_reminder_id
        )
        if (
            expected_intent == "snooze"
            and guarded["reminder"].get("title") != target.title
        ):
            guarded["reminder"]["title"] = target.title
            adjustments.append("existing_target_title_preserved")

    if expected_intent == "snooze":
        target = next(
            item
            for item in request.existing_reminders
            if item.id == assessment.target_reminder_id
        )
        due_at = max(
            request.reference_now.astimezone(UTC),
            target.due_at.astimezone(UTC),
        ) + assessment.snooze_duration
        guarded["reminder"]["due_at"] = due_at.astimezone(
            ZoneInfo(request.timezone)
        ).isoformat(timespec="seconds")
        adjustments.append("snooze_duration_applied")

    if expected_intent == "create" and assessment.relative_duration is not None:
        due_at = request.reference_now.astimezone(UTC) + assessment.relative_duration
        guarded["reminder"]["due_at"] = due_at.astimezone(
            ZoneInfo(request.timezone)
        ).isoformat(timespec="seconds")
        adjustments.append("relative_duration_applied")

    try:
        due_text = guarded["reminder"].get("due_at", "")
        due_normalized = due_text[:-1] + "+00:00" if due_text.endswith(("Z", "z")) else due_text
        due_at = datetime.fromisoformat(due_normalized)
    except (AttributeError, TypeError, ValueError):
        return guarded, adjustments
    if due_at.tzinfo is not None and due_at <= request.reference_now:
        return (
            {
                "intent": "reject",
                "status": "rejected",
                "reminder": None,
                "target_reminder_id": None,
                "missing_fields": [],
                "clarification_question": None,
                "reason_code": "past_datetime",
            },
            [*adjustments, "past_datetime_rejected"],
        )
    return guarded, adjustments
