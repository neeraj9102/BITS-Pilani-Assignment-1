"""Run the independent deterministic quality and behavior gates."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "evidence" / "harness-runs"
GATE_ORDER = ("compileall", "ruff", "bandit", "pytest")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _tool_command(tool: str, arguments: list[str]) -> list[str]:
    executable = shutil.which(tool)
    if executable:
        return [executable, *arguments]
    return [sys.executable, "-m", tool, *arguments]


def commands() -> list[tuple[str, list[str]]]:
    return [
        ("compileall", [sys.executable, "-m", "compileall", "-q", "src", "tests", ".harness"]),
        ("ruff", _tool_command("ruff", ["check", "src", "tests", ".harness"])),
        ("bandit", _tool_command("bandit", ["-r", "src"])),
        ("pytest", [sys.executable, "-m", "pytest", "-q"]),
    ]


def validate_run_record(record: Any) -> list[str]:
    """Validate the minimum integrity contract for a saved harness run."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["run record must be an object"]
    for key in ("run_id", "started_at_utc", "completed_at_utc", "gates"):
        if key not in record:
            errors.append(f"missing top-level field: {key}")
    if not isinstance(record.get("run_id"), str) or not record.get("run_id"):
        errors.append("run_id must be a non-empty string")
    for field in ("started_at_utc", "completed_at_utc"):
        stamp = record.get(field)
        try:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError
        except (AttributeError, TypeError, ValueError):
            errors.append(f"{field} must be an offset-aware timestamp")
    gates = record.get("gates")
    if not isinstance(gates, list):
        errors.append("gates must be an array")
        return errors
    names = [gate.get("name") if isinstance(gate, dict) else None for gate in gates]
    if tuple(names) != GATE_ORDER:
        errors.append("gate names and order must exactly match the required four gates")
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append(f"gate {index} must be an object")
            continue
        for field in (
            "name",
            "command",
            "started_at_utc",
            "completed_at_utc",
            "exit_code",
            "status",
            "stdout_file",
            "stderr_file",
        ):
            if field not in gate:
                errors.append(f"gate {index} is missing {field}")
        command = gate.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) for part in command
        ):
            errors.append(f"gate {index} command must be a non-empty string array")
        code = gate.get("exit_code")
        if not isinstance(code, int) or isinstance(code, bool):
            errors.append(f"gate {index} exit_code must be an integer")
        elif gate.get("status") != ("passed" if code == 0 else "failed"):
            errors.append(f"gate {index} status must agree with its exit code")
        for field in ("started_at_utc", "completed_at_utc"):
            stamp = gate.get(field)
            try:
                parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError
            except (AttributeError, TypeError, ValueError):
                errors.append(f"gate {index} {field} must be an offset-aware timestamp")
        for field in ("stdout_file", "stderr_file"):
            path = gate.get(field)
            if not isinstance(path, str) or not path:
                errors.append(f"gate {index} {field} must be a non-empty relative path")
            elif Path(path).is_absolute() or ".." in Path(path).parts:
                errors.append(f"gate {index} {field} must remain inside the run directory")
    expected_overall = "passed" if len(gates) == len(GATE_ORDER) and all(
        isinstance(gate, dict) and gate.get("exit_code") == 0 for gate in gates
    ) else "failed"
    if record.get("overall_status") != expected_overall:
        errors.append("overall_status must agree with the gate exit codes")
    return errors


def _run_gate(
    name: str, command: list[str], run_directory: Path, environment: dict[str, str]
) -> dict[str, Any]:
    started = _utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except OSError as error:
        exit_code = 127
        stdout = ""
        stderr = f"could not start command ({type(error).__name__}): {error}\n"
    completed_at = _utc_now()
    stdout_file = f"{name}.stdout.txt"
    stderr_file = f"{name}.stderr.txt"
    (run_directory / stdout_file).write_text(stdout, encoding="utf-8", newline="")
    (run_directory / stderr_file).write_text(stderr, encoding="utf-8", newline="")
    return {
        "name": name,
        "command": command,
        "started_at_utc": _timestamp(started),
        "completed_at_utc": _timestamp(completed_at),
        "exit_code": exit_code,
        "status": "passed" if exit_code == 0 else "failed",
        "stdout_file": stdout_file,
        "stderr_file": stderr_file,
    }


def run_harness() -> tuple[dict[str, Any], Path]:
    run_id = _utc_now().strftime("%Y%m%dT%H%M%S.%fZ")
    run_directory = EVIDENCE_ROOT / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    started = _utc_now()
    environment = os.environ.copy()
    source_path = str(ROOT / "src")
    current_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_path, current_pythonpath) if part
    )
    results = []
    for name, command in commands():
        results.append(_run_gate(name, command, run_directory, environment))
    completed = _utc_now()
    record = {
        "run_id": run_id,
        "started_at_utc": _timestamp(started),
        "completed_at_utc": _timestamp(completed),
        "gates": results,
        "overall_status": "passed" if all(gate["exit_code"] == 0 for gate in results) else "failed",
    }
    errors = validate_run_record(record)
    if errors:
        raise RuntimeError("harness generated an invalid run record: " + "; ".join(errors))
    (run_directory / "run.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record, run_directory


def main() -> int:
    try:
        record, run_directory = run_harness()
    except Exception as error:
        print(f"harness infrastructure failure ({type(error).__name__}): {error}", file=sys.stderr)
        return 2
    for gate in record["gates"]:
        print(f"{gate['name']}: {gate['status']} (exit {gate['exit_code']})")
    print(f"overall: {record['overall_status']}")
    print(f"evidence: {run_directory.relative_to(ROOT)}")
    return 0 if record["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
