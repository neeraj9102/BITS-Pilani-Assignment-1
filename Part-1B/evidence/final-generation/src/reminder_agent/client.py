"""Model client protocol used by the agent and deterministic tests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class ResponsesClient(Protocol):
    def generate(
        self,
        request: Mapping[str, Any],
        system_prompt: str,
    ) -> str | Mapping[str, Any]:
        """Return structured JSON text or a parsed mapping for one request."""
