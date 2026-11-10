"""JSON-over-stdin command-line interface."""

from __future__ import annotations

import json
import sys

from reminder_agent.agent import ReminderAgent, malformed_json_result
from reminder_agent.models import ReminderAgentError


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError):
        payload = None
        result = malformed_json_result()
    else:
        try:
            result = ReminderAgent().run(payload)
        except ReminderAgentError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0
