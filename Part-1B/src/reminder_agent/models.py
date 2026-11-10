"""Typed request/result models and error classes for the reminder agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class ReminderAgentError(Exception):
    """Base class for expected reminder-agent errors."""


class MalformedRequest(ReminderAgentError):
    """The request envelope is malformed or outside documented bounds."""


class InvalidTimezone(ReminderAgentError):
    """A supplied timezone is missing or cannot be safely resolved."""


class OutputValidationError(ReminderAgentError):
    """The model response violates the declared structured output contract."""


class InfrastructureFailure(ReminderAgentError):
    """The configured model service could not provide a response."""


class ProviderRefusal(ReminderAgentError):
    """The provider returned a refusal instead of the requested JSON object."""


class IncompleteModelOutput(ReminderAgentError):
    """The provider ended generation before returning a complete structured result."""


@dataclass(frozen=True, slots=True)
class ExistingReminder:
    id: str
    title: str
    due_at: datetime


@dataclass(frozen=True, slots=True)
class ReminderRequest:
    request: str
    reference_now: datetime
    timezone: str
    existing_reminders: tuple[ExistingReminder, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "reference_now": self.reference_now.isoformat(),
            "timezone": self.timezone,
            "existing_reminders": [
                {
                    "id": reminder.id,
                    "title": reminder.title,
                    "due_at": reminder.due_at.isoformat(),
                }
                for reminder in self.existing_reminders
            ],
        }


def parse_aware_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise MalformedRequest(f"{field_name} must be a non-empty ISO 8601 timestamp")
    try:
        normalized = value.strip()
        if normalized.endswith(("Z", "z")):
            normalized = normalized[:-1] + "+00:00"
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise MalformedRequest(f"{field_name} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MalformedRequest(f"{field_name} must include an explicit UTC offset")
    return parsed
