"""Capture repeatable offline validation for the reminder agent."""

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
RUNS = ROOT / "evidence" / "harness-runs"


def _stamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _command(tool: str, arguments: list[str]) -> list[str]:
    executable = shutil.which(tool)
    if executable:
        return [executable, *arguments]
    return [sys.executable, "-m", tool, *arguments]


def _run(name: str, command: list[str], directory: Path, env: dict[str, str]) -> dict[str, Any]:
    started = datetime.now(UTC)
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except OSError as error:
        exit_code = 127
        stdout = ""
        stderr = f"could not start command ({type(error).__name__}): {error}\n"
    stdout_name, stderr_name = f"{name}.stdout.txt", f"{name}.stderr.txt"
    (directory / stdout_name).write_text(stdout, encoding="utf-8", newline="")
    (directory / stderr_name).write_text(stderr, encoding="utf-8", newline="")
    return {
        "name": name,
        "command": command,
        "started_at_utc": _stamp(started),
        "completed_at_utc": _stamp(datetime.now(UTC)),
        "exit_code": exit_code,
        "status": "passed" if exit_code == 0 else "failed",
        "stdout_file": stdout_name,
        "stderr_file": stderr_name,
    }


def run() -> tuple[dict[str, Any], Path]:
    run_id = datetime.now(UTC).strftime("offline-%Y%m%dT%H%M%S.%fZ")
    directory = RUNS / run_id
    directory.mkdir(parents=True, exist_ok=False)
    started = datetime.now(UTC)
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (src, env.get("PYTHONPATH", "")) if part
    )
    commands = [
        (
            "compileall",
            [sys.executable, "-m", "compileall", "-q", "src", "tests", ".harness"],
        ),
        ("ruff", _command("ruff", ["check", "src", "tests", ".harness"])),
        ("pytest", [sys.executable, "-m", "pytest", "-q"]),
    ]
    gates = [_run(name, command, directory, env) for name, command in commands]
    record = {
        "run_id": run_id,
        "run_type": "offline",
        "started_at_utc": _stamp(started),
        "completed_at_utc": _stamp(datetime.now(UTC)),
        "gates": gates,
        "overall_status": "passed" if all(item["exit_code"] == 0 for item in gates) else "failed",
    }
    (directory / "run.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record, directory


def main() -> int:
    record, directory = run()
    for gate in record["gates"]:
        print(f"{gate['name']}: {gate['status']} (exit {gate['exit_code']})")
    print(f"overall: {record['overall_status']}")
    print(f"evidence: {directory.relative_to(ROOT)}")
    return 0 if record["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
