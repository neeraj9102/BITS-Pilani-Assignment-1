"""Deterministic policy checks for unsafe and unsupported request clauses."""

from __future__ import annotations

import re

_PROMPT_INJECTION = re.compile(
    r"\bignore\b[^.!?;\r\n]{0,120}"
    r"\b(?:reveal|show|expose|print|display|disclose)\b"
    r"[^.!?;\r\n]{0,120}"
    r"\b(?:hidden|system|prompt|instructions?|credential|api[\s_-]?key|secrets?)\b"
    r"[^.!?;\r\n]*(?:[.!?;]|$)",
    re.IGNORECASE,
)
_SUPPORTED_ACTION = re.compile(
    r"\b(?:remind(?:er)?|snooze|reschedule|postpone|move\s+(?:my|the))\b",
    re.IGNORECASE,
)
_EXTERNAL_DELIVERY = re.compile(
    r"\b(?:send|deliver|notify|message|text|email)\s+me\b",
    re.IGNORECASE,
)


def prepare_request_text(text: str) -> tuple[str, str | None]:
    """Remove explicit prompt-exfiltration clauses and reject unsupported sends."""
    matches = list(_PROMPT_INJECTION.finditer(text))
    sanitized = _PROMPT_INJECTION.sub(" ", text)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" \t\r\n,.;:!?")
    if matches:
        if not sanitized or not _SUPPORTED_ACTION.search(sanitized):
            return sanitized, "unsafe_request"
        text = sanitized
    if _EXTERNAL_DELIVERY.search(text):
        return text, "unsupported_action"
    return text, None
