"""Reminder request orchestration with independent local validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from reminder_agent.client import ResponsesClient
from reminder_agent.models import (
    InfrastructureFailure,
    InvalidTimezone,
    MalformedRequest,
    ReminderAgentError,
)
from reminder_agent.validation import parse_request_envelope, validate_output

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = ROOT / "prompts" / "system.md"


def _result(
    *,
    intent: str,
    status: str,
    reminder: dict[str, Any] | None = None,
    target_reminder_id: str | None = None,
    missing_fields: list[str] | None = None,
    clarification_question: str | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    return {
        "intent": intent,
        "status": status,
        "reminder": reminder,
        "target_reminder_id": target_reminder_id,
        "missing_fields": missing_fields or [],
        "clarification_question": clarification_question,
        "reason_code": reason_code,
    }


class ReminderAgent:
    def __init__(
        self,
        *,
        client: ResponsesClient | None = None,
        default_timezone: str | None = None,
        system_prompt_path: str | Path = SYSTEM_PROMPT_PATH,
    ) -> None:
        self.client = client
        self.default_timezone = default_timezone or os.environ.get(
            "REMINDER_TIMEZONE", "Asia/Kolkata"
        )
        try:
            self.system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError("the reminder system prompt is unavailable") from exc

    def run(self, envelope: Any) -> dict[str, Any]:
        try:
            request = parse_request_envelope(
                envelope,
                default_timezone=self.default_timezone,
            )
        except InvalidTimezone:
            return _result(
                intent="clarify",
                status="needs_clarification",
                missing_fields=["timezone"],
                clarification_question="Which IANA time zone should I use for this reminder?",
            )
        except MalformedRequest:
            return _result(
                intent="reject",
                status="rejected",
                reason_code="malformed_input",
            )

        client = self.client
        if client is None:
            from reminder_agent.openai_client import OpenAIResponsesClient

            client = OpenAIResponsesClient()
        try:
            output = client.generate(request.as_payload(), self.system_prompt)
        except ReminderAgentError:
            raise
        except Exception as exc:
            raise InfrastructureFailure(
                f"model client failed ({type(exc).__name__})"
            ) from exc
        return validate_output(output, request)


def malformed_json_result() -> dict[str, Any]:
    """Return the contract-compliant outcome for an invalid JSON input document."""
    return _result(
        intent="reject",
        status="rejected",
        reason_code="malformed_input",
    )
