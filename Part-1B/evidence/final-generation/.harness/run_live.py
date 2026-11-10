"""Run and capture the non-deterministic evaluation without saving credentials."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "evidence" / "harness-runs"
SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|authorization)\s*[:=]\s*(?:bearer\s+)?[^\s,;]+"),
)


def _stamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _redact(value: str) -> tuple[str, bool]:
    original = value
    configured_key = os.environ.get("OPENAI_API_KEY", "")
    if configured_key:
        value = value.replace(configured_key, "[REDACTED]")
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value, value != original


def run() -> tuple[dict[str, Any], Path]:
    run_id = datetime.now(UTC).strftime("live-%Y%m%dT%H%M%S.%fZ")
    directory = RUNS / run_id
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(ROOT / ".harness" / "evaluate.py"), "--mode", "live"]
    started = datetime.now(UTC)
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (src, env.get("PYTHONPATH", "")) if part
    )
    result_path = ROOT / "evidence" / "eval-results.json"
    previous_result_mtime = result_path.stat().st_mtime_ns if result_path.exists() else None
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        exit_code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except OSError as error:
        exit_code = 127
        stdout = ""
        stderr = f"could not start command ({type(error).__name__}): {error}\n"
    stdout, stdout_redacted = _redact(stdout)
    stderr, stderr_redacted = _redact(stderr)
    (directory / "evaluate.stdout.txt").write_text(stdout, encoding="utf-8", newline="")
    (directory / "evaluate.stderr.txt").write_text(stderr, encoding="utf-8", newline="")
    completed_at = datetime.now(UTC)
    result = None
    if result_path.exists() and result_path.stat().st_mtime_ns != previous_result_mtime:
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            result = None
    aggregate = result.get("aggregate") if isinstance(result, dict) else None
    decision = aggregate.get("decision") if isinstance(aggregate, dict) else None
    complete_decision = decision in {"PASS", "FAIL"}
    result_snapshot = None
    if complete_decision:
        result_snapshot = "eval-results.json"
        shutil.copy2(result_path, directory / result_snapshot)
    if complete_decision:
        status = "completed_pass" if decision == "PASS" else "completed_fail"
    else:
        status = "incomplete"
    record = {
        "run_id": run_id,
        "run_type": "live_evaluation",
        "command": command,
        "started_at_utc": _stamp(started),
        "completed_at_utc": _stamp(completed_at),
        "exit_code": exit_code,
        "status": status,
        "stdout_file": "evaluate.stdout.txt",
        "stderr_file": "evaluate.stderr.txt",
        "stdout_redacted": stdout_redacted,
        "stderr_redacted": stderr_redacted,
        "evaluation_result_file": result_snapshot,
        "result_snapshot": result_snapshot,
        "evaluation_decision": decision if complete_decision else None,
        "semantic_mean": aggregate.get("semantic_mean") if complete_decision else None,
        "case_count": aggregate.get("case_count") if complete_decision else None,
        "infrastructure_failures": (
            aggregate.get("infrastructure_failures") if complete_decision else None
        ),
    }
    (directory / "run.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record, directory


def main() -> int:
    record, directory = run()
    print(f"live evaluation process exit: {record['exit_code']}")
    print(f"evaluation evidence: {record['evaluation_result_file']}")
    print(f"command evidence: {directory.relative_to(ROOT)}")
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
