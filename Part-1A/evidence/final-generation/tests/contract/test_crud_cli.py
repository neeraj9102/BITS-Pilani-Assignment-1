import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from smart_todo.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_cli(store_path, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    env.pop("OPENAI_API_KEY", None)
    completed = subprocess.run(
        [sys.executable, "-m", "smart_todo", "--data-file", str(store_path), *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed


def run_cli_in_process(store_path, *args):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        returncode = main(["--data-file", str(store_path), *args])
    return SimpleNamespace(
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def parse_success(completed):
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_crud_defaults_updates_clear_tags_and_id_non_reuse(tmp_path):
    path = tmp_path / "store.json"
    created = parse_success(run_cli(path, "add", "  Submit assignment  ", "--tag", "school"))
    assert created["id"] == "T-000001"
    assert created["title"] == "Submit assignment"
    assert created["priority"] == "medium"
    assert created["status"] == "todo"
    assert created["tags"] == ["school"]

    shown = parse_success(run_cli(path, "show", "T-000001"))
    assert shown == created

    updated = parse_success(
        run_cli_in_process(path, "update", "T-000001", "--priority", "high", "--clear-tags")
    )
    assert updated["priority"] == "high"
    assert updated["tags"] == []
    assert updated["description"] == ""

    assert parse_success(run_cli_in_process(path, "delete", "T-000001")) == {"deleted": "T-000001"}
    assert parse_success(run_cli_in_process(path, "list")) == []
    created_again = parse_success(run_cli_in_process(path, "add", "Second task"))
    assert created_again["id"] == "T-000002"


def test_rejected_crud_requests_leave_persisted_state_unchanged(tmp_path):
    path = tmp_path / "store.json"
    parse_success(run_cli_in_process(path, "add", "Kept"))
    original = path.read_bytes()

    rejected = run_cli_in_process(path, "add", "   ")
    assert rejected.returncode != 0
    assert rejected.stderr.strip()
    assert path.read_bytes() == original

    missing = run_cli_in_process(path, "show", "T-999999")
    assert missing.returncode != 0
    assert path.read_bytes() == original


def test_unknown_update_and_delete_do_not_report_success(tmp_path):
    path = tmp_path / "store.json"
    for command in (
        ("update", "T-000001", "--title", "ghost"),
        ("delete", "T-000001"),
    ):
        completed = run_cli_in_process(path, *command)
        assert completed.returncode != 0
        assert not completed.stdout


def test_malformed_store_is_not_replaced_by_cli_mutation(tmp_path):
    path = tmp_path / "store.json"
    path.write_bytes(b"not json")
    original = path.read_bytes()
    completed = run_cli_in_process(path, "add", "Task")
    assert completed.returncode != 0
    assert completed.stderr.strip()
    assert path.read_bytes() == original
