import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVALUATOR_PATH = ROOT / ".harness" / "evaluate.py"
SPEC = importlib.util.spec_from_file_location("reminder_evaluator", EVALUATOR_PATH)
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)


def case_by_id(case_id):
    return next(case for case in evaluator.load_dataset()["cases"] if case["id"] == case_id)


def ready_result(
    *, title="Turn in homework", due_at="2026-11-11T09:00:00+05:30", timezone="Asia/Kolkata"
):
    return {
        "intent": "create",
        "status": "ready",
        "reminder": {"title": title, "due_at": due_at, "timezone": timezone},
        "target_reminder_id": None,
        "missing_fields": [],
        "clarification_question": None,
        "reason_code": None,
    }


def test_independent_structural_layer_accepts_valid_and_rejects_extra_fields():
    valid = ready_result()
    assert evaluator.validate_structural(valid)["status"] == "PASS"
    invalid = {**valid, "unapproved": True}
    assert evaluator.validate_structural(invalid)["status"] == "FAIL"


def test_independent_structural_layer_rejects_invalid_zone_and_offset_mismatch():
    invalid_zone = ready_result(timezone="Mars/Olympus")
    zone_result = evaluator.validate_structural(invalid_zone)
    assert zone_result["status"] == "FAIL"
    assert any("valid IANA identifier" in error for error in zone_result["errors"])

    mismatched_offset = ready_result(timezone="America/Los_Angeles")
    offset_result = evaluator.validate_structural(mismatched_offset)
    assert offset_result["status"] == "FAIL"
    assert any("offset does not match" in error for error in offset_result["errors"])


def test_property_layer_checks_time_and_supplied_target():
    case = case_by_id("REM-003")
    result = {
        "intent": "reschedule",
        "status": "ready",
        "reminder": {
            "title": "Dentist appointment",
            "due_at": "2026-11-12T14:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        "target_reminder_id": "R-7",
        "missing_fields": [],
        "clarification_question": None,
        "reason_code": None,
    }
    checks = evaluator.evaluate_properties(case, result)
    assert checks["status"] == "PASS"
    assert all(check["passed"] for check in checks["checks"])


def test_semantic_rubric_accepts_equivalent_title_wording():
    case = case_by_id("REM-002")
    result = ready_result()
    scored = evaluator.score_semantic(case, result)
    assert scored["score"] == pytest.approx(1.0)
    title_score = next(item for item in scored["criteria"] if item["criterion"] == "title_content")
    assert title_score["score"] == 1.0


def test_semantic_rubric_penalizes_missing_task_concepts():
    case = case_by_id("REM-002")
    result = ready_result(title="Turn in the form")
    scored = evaluator.score_semantic(case, result)
    assert scored["score"] < 1.0


def test_secret_redaction_covers_configured_key(monkeypatch):
    secret = "test-secret-token-never-log"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    assert secret not in evaluator._redact(f"provider error: {secret}")


def test_aggregate_requires_hard_gates_and_the_fixed_threshold():
    passed = {
        "structural": {"status": "PASS"},
        "properties": {"status": "PASS"},
        "semantic": {"score": 0.9},
        "failure_category": None,
    }
    assert evaluator.aggregate_results([passed], threshold=0.85)["decision"] == "PASS"

    low_score = {**passed, "semantic": {"score": 0.84}}
    assert evaluator.aggregate_results([low_score], threshold=0.85)["decision"] == "FAIL"

    property_failure = {**passed, "properties": {"status": "FAIL"}}
    assert evaluator.aggregate_results([property_failure], threshold=0.85)["decision"] == "FAIL"

    infrastructure = {**passed, "failure_category": "infrastructure"}
    assert evaluator.aggregate_results([infrastructure], threshold=0.85)["decision"] == "INCOMPLETE"
