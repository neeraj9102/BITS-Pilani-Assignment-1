import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = ROOT / ".harness" / "run_harness.py"
SPEC = importlib.util.spec_from_file_location("smart_todo_harness", HARNESS_PATH)
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


def valid_record():
    gates = []
    for index, name in enumerate(harness.GATE_ORDER):
        gates.append(
            {
                "name": name,
                "command": ["python", "-m", name],
                "started_at_utc": "2026-11-10T12:00:00+00:00",
                "completed_at_utc": "2026-11-10T12:00:01+00:00",
                "exit_code": 0,
                "status": "passed",
                "stdout_file": f"{name}.stdout.txt",
                "stderr_file": f"{name}.stderr.txt",
            }
        )
    return {
        "run_id": "20261110T120000.000000Z",
        "started_at_utc": "2026-11-10T12:00:00+00:00",
        "completed_at_utc": "2026-11-10T12:00:05+00:00",
        "gates": gates,
        "overall_status": "passed",
    }


def test_harness_record_accepts_all_required_ordered_gates():
    assert harness.validate_run_record(valid_record()) == []


def test_harness_record_rejects_missing_gate_and_wrong_order():
    record = valid_record()
    record["gates"].pop()
    errors = harness.validate_run_record(record)
    assert any("gate names and order" in error for error in errors)


def test_harness_record_rejects_pass_status_for_nonzero_exit():
    record = valid_record()
    record["gates"][1]["exit_code"] = 1
    errors = harness.validate_run_record(record)
    assert any("status must agree" in error for error in errors)


def test_harness_record_rejects_output_path_escape_and_naive_time():
    record = valid_record()
    record["gates"][0]["stdout_file"] = "../outside.txt"
    record["gates"][0]["started_at_utc"] = "2026-11-10T12:00:00"
    errors = harness.validate_run_record(record)
    assert any("remain inside" in error for error in errors)
    assert any("offset-aware" in error for error in errors)
