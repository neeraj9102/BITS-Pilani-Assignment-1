"""Single live evaluation pipeline for the Natural Language Reminder Agent."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker

from reminder_agent.client_factory import create_client

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evals" / "dataset.json"
DATASET_SCHEMA_PATH = (
    ROOT / "specs" / "001-reminder-agent" / "contracts" / "evaluation-dataset.schema.json"
)
OUTPUT_SCHEMA_PATH = (
    ROOT / "specs" / "001-reminder-agent" / "contracts" / "reminder-output.schema.json"
)
RESULT_PATH = ROOT / "evidence" / "eval-results.json"
REQUIRED_CATEGORIES = {
    "representative": 4,
    "boundary": 3,
    "ambiguous": 3,
    "missing_information": 3,
    "malformed": 2,
    "adversarial_guardrail": 3,
}
THRESHOLD = 0.85
SNOOZE_DURATION = re.compile(
    r"(?<![\w-])(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|days?|weeks?)\b",
    re.IGNORECASE,
)
SNOOZE_UNITS = {
    "minute": 60,
    "min": 60,
    "hour": 3600,
    "hr": 3600,
    "day": 86400,
    "week": 604800,
}
SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|authorization)\s*[:=]\s*(?:bearer\s+)?[^\s,;]+"),
)


@lru_cache(maxsize=1)
def output_validator() -> Draft202012Validator:
    schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@lru_cache(maxsize=1)
def dataset_validator() -> Draft202012Validator:
    schema = json.loads(DATASET_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def load_dataset() -> dict[str, Any]:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        dataset_validator().iter_errors(dataset),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        details = "; ".join(error.message for error in errors)
        raise ValueError("evaluation dataset is invalid: " + details)
    cases = dataset["cases"]
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("evaluation case IDs must be unique")
    category_counts = Counter(case["category"] for case in cases)
    if dict(category_counts) != REQUIRED_CATEGORIES:
        raise ValueError("evaluation case categories do not match the fixed benchmark distribution")
    for case in cases:
        criterion_names = [item["criterion"] for item in case["rubric"]]
        if len(set(criterion_names)) != len(criterion_names):
            raise ValueError(f"{case['id']} has duplicate rubric criteria")
        if abs(sum(item["weight"] for item in case["rubric"]) - 1.0) > 1e-9:
            raise ValueError(f"{case['id']} rubric weights must sum to 1")
    if dataset["threshold"] != THRESHOLD:
        raise ValueError("evaluation dataset threshold differs from the approved 0.85 threshold")
    return dataset


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def validate_structural(output: Any) -> dict[str, Any]:
    """Independently enforce the full output schema, timestamp, and IANA zone."""
    if not isinstance(output, dict):
        return {"status": "FAIL", "errors": ["output is not a JSON object"]}
    errors = sorted(
        output_validator().iter_errors(output),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    messages = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "output"
        messages.append(f"{location}: {error.message}")
    reminder = output.get("reminder")
    if isinstance(reminder, dict):
        zone = None
        try:
            zone = ZoneInfo(reminder.get("timezone", ""))
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            messages.append("reminder.timezone is not a valid IANA identifier")
        due_at = _parse_datetime(reminder.get("due_at"))
        if due_at is None:
            messages.append("reminder.due_at must include an explicit offset")
        elif zone is not None:
            localized = due_at.astimezone(zone)
            if (
                localized.utcoffset() != due_at.utcoffset()
                or localized.replace(tzinfo=None) != due_at.replace(tzinfo=None)
            ):
                messages.append("reminder.due_at offset does not match its IANA timezone")
    return {"status": "FAIL" if messages else "PASS", "errors": messages}


def _normalized_tokens(text: Any) -> set[str]:
    if not isinstance(text, str):
        return set()
    return set(re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE))


def _concept_coverage(actual_text: Any, concept_groups: list[list[str]]) -> float:
    if not concept_groups:
        return 1.0
    actual = _normalized_tokens(actual_text)
    matched = 0
    for alternatives in concept_groups:
        found = False
        for alternative in alternatives:
            required = _normalized_tokens(alternative)
            if required and required.issubset(actual):
                found = True
                break
        matched += int(found)
    return matched / len(concept_groups)


def _snooze_expected(case: dict[str, Any]) -> datetime | None:
    text = case["input"]["request"]
    matches = list(SNOOZE_DURATION.finditer(text))
    if len(matches) != 1:
        return None
    amount = float(matches[0].group(1))
    if amount <= 0:
        return None
    unit = matches[0].group(2).casefold().rstrip("s")
    duration = timedelta(seconds=amount * SNOOZE_UNITS[unit])
    reference = _parse_datetime(case["input"].get("reference_now"))
    target_id = case["expected"].get("target_reminder_id")
    target = next(
        (
            item
            for item in case["input"].get("existing_reminders", [])
            if item.get("id") == target_id
        ),
        None,
    )
    current_due = _parse_datetime(target.get("due_at")) if target else None
    if reference is None or current_due is None:
        return None
    base = max(reference.astimezone(UTC), current_due.astimezone(UTC))
    return base + duration


def evaluate_properties(case: dict[str, Any], output: Any) -> dict[str, Any]:
    """Run deterministic hard-gate checks derived from the fixed case contract."""
    expected = case["expected"]
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"property": name, "passed": bool(passed), "detail": detail})

    if not isinstance(output, dict):
        return {
            "status": "FAIL",
            "checks": [
                {"property": "output_object", "passed": False, "detail": "no object output"}
            ],
        }

    add(
        "expected_intent",
        output.get("intent") == expected["intent"],
        "intent equals case ground truth",
    )
    add(
        "expected_status",
        output.get("status") == expected["status"],
        "status equals case ground truth",
    )
    add(
        "expected_target",
        output.get("target_reminder_id") == expected["target_reminder_id"],
        "target ID equals case ground truth",
    )
    add(
        "expected_missing_fields",
        set(output.get("missing_fields", [])) == set(expected["missing_fields"]),
        "missing field set equals case ground truth",
    )
    add(
        "expected_reason_code",
        output.get("reason_code") == expected["reason_code"],
        "reason code equals case ground truth",
    )

    for property_name in expected["properties"]:
        reminder = output.get("reminder")
        result = False
        detail = "property not satisfied"
        if property_name == "due_time_in_future":
            due = _parse_datetime(reminder.get("due_at")) if isinstance(reminder, dict) else None
            reference = _parse_datetime(case["input"].get("reference_now"))
            result = (
                due is not None
                and reference is not None
                and due.astimezone(UTC) > reference.astimezone(UTC)
            )
            detail = "ready due time is strictly later than reference_now"
        elif property_name == "target_is_supplied":
            target_id = output.get("target_reminder_id")
            result = bool(target_id) and sum(
                item.get("id") == target_id for item in case["input"].get("existing_reminders", [])
            ) == 1
            detail = "target ID identifies exactly one supplied reminder"
        elif property_name == "ambiguous_requires_clarification":
            result = (
                output.get("intent") == "clarify"
                and output.get("status") == "needs_clarification"
                and output.get("reminder") is None
                and bool(output.get("missing_fields"))
                and bool(output.get("clarification_question"))
            )
            detail = "ambiguous or incomplete request has no ready proposal and asks a question"
        elif property_name == "unsafe_request_rejected":
            result = (
                output.get("status") == "rejected"
                and output.get("reason_code") == "unsafe_request"
            )
            detail = "unsafe request is rejected with unsafe_request reason"
        elif property_name == "unsupported_action_rejected":
            result = (
                output.get("status") == "rejected"
                and output.get("reason_code") == "unsupported_action"
            )
            detail = "unsupported action is rejected with unsupported_action reason"
        elif property_name == "past_time_rejected":
            result = (
                output.get("status") == "rejected"
                and output.get("reason_code") == "past_datetime"
            )
            detail = "past due time is rejected with past_datetime reason"
        elif property_name == "snooze_base_arithmetic":
            due = _parse_datetime(reminder.get("due_at")) if isinstance(reminder, dict) else None
            expected_due = _snooze_expected(case)
            result = (
                due is not None
                and expected_due is not None
                and due.astimezone(UTC) == expected_due
            )
            detail = "snooze equals max(reference_now, current_due_at) plus requested duration"
        add(property_name, result, detail)

    return {
        "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
        "checks": checks,
    }


def _criterion_score(name: str, case: dict[str, Any], output: dict[str, Any]) -> float:
    expected = case["expected"]
    reminder = output.get("reminder")
    if name == "intent_match":
        return float(output.get("intent") == expected["intent"])
    if name == "status_match":
        return float(output.get("status") == expected["status"])
    if name == "title_content":
        title = reminder.get("title") if isinstance(reminder, dict) else None
        return _concept_coverage(title, expected["title_concepts"])
    if name == "due_time_match":
        actual = _parse_datetime(reminder.get("due_at")) if isinstance(reminder, dict) else None
        wanted = _parse_datetime(expected["expected_due_at"])
        return float(
            actual is not None
            and wanted is not None
            and actual.astimezone(UTC) == wanted.astimezone(UTC)
        )
    if name == "timezone_match":
        zone = reminder.get("timezone") if isinstance(reminder, dict) else None
        return float(zone == expected["expected_timezone"])
    if name == "target_match":
        return float(output.get("target_reminder_id") == expected["target_reminder_id"])
    if name == "clarification_coverage":
        question = output.get("clarification_question")
        return _concept_coverage(question, expected["clarification_concepts"])
    if name == "rejection_reason":
        return float(output.get("reason_code") == expected["reason_code"])
    if name == "missing_fields_match":
        return float(set(output.get("missing_fields", [])) == set(expected["missing_fields"]))
    raise ValueError(f"unsupported rubric criterion: {name}")


def score_semantic(case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    criteria = []
    weighted_total = 0.0
    for item in case["rubric"]:
        score = _criterion_score(item["criterion"], case, output)
        weighted_total += score * item["weight"]
        criteria.append(
            {
                "criterion": item["criterion"],
                "weight": item["weight"],
                "score": round(score, 6),
            }
        )
    return {"score": round(weighted_total, 6), "criteria": criteria}


def aggregate_results(
    case_results: list[dict[str, Any]], *, threshold: float = THRESHOLD
) -> dict[str, Any]:
    semantic_scores = [
        item["semantic"]["score"]
        for item in case_results
        if isinstance(item.get("semantic"), dict) and item["semantic"].get("score") is not None
    ]
    semantic_mean = (
        round(sum(semantic_scores) / len(semantic_scores), 6) if semantic_scores else None
    )
    infrastructure_count = sum(
        item.get("failure_category") == "infrastructure" for item in case_results
    )
    structural_failures = sum(
        item.get("structural", {}).get("status") == "FAIL" for item in case_results
    )
    property_failures = sum(
        item.get("properties", {}).get("status") == "FAIL" for item in case_results
    )
    if infrastructure_count:
        decision = "INCOMPLETE"
    elif (
        len(case_results) == 0
        or structural_failures
        or property_failures
        or len(semantic_scores) != len(case_results)
        or semantic_mean is None
        or semantic_mean < threshold
    ):
        decision = "FAIL"
    else:
        decision = "PASS"
    return {
        "decision": decision,
        "semantic_mean": semantic_mean,
        "semantic_threshold": threshold,
        "case_count": len(case_results),
        "structural_failures": structural_failures,
        "property_failures": property_failures,
        "infrastructure_failures": infrastructure_count,
    }


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        result = value
        configured_key = os.environ.get("OPENAI_API_KEY", "")
        if configured_key:
            result = result.replace(configured_key, "[REDACTED]")
        for pattern in SECRET_PATTERNS:
            result = pattern.sub("[REDACTED]", result)
        return result
    return value


class RecordingClient:
    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.raw_output: Any = None

    def generate(self, request: dict[str, Any], system_prompt: str) -> Any:
        self.raw_output = self.inner.generate(request, system_prompt)
        return self.raw_output


def _blocked_case(case: dict[str, Any], message: str) -> dict[str, Any]:
    return {
        "case_id": case["id"],
        "category": case["category"],
        "model_output": None,
        "application_output": None,
        "policy_adjustments": [],
        "structural": {"status": "BLOCKED", "errors": [message]},
        "properties": {"status": "BLOCKED", "checks": []},
        "semantic": {"score": None, "criteria": []},
        "failure_category": "infrastructure",
        "failure_message": message,
    }


def _evaluate_one(case: dict[str, Any]) -> dict[str, Any]:
    from reminder_agent.agent import ReminderAgent
    from reminder_agent.models import (
        IncompleteModelOutput,
        InfrastructureFailure,
        OutputValidationError,
        ProviderRefusal,
    )
    recording_client = RecordingClient(create_client())
    agent = ReminderAgent(client=recording_client)
    output: Any = None
    application_output: Any = None
    failure_category = None
    failure_message = None
    try:
        output = agent.run(case["input"])
        application_output = output
    except InfrastructureFailure as exc:
        failure_category = "infrastructure"
        failure_message = str(exc)
    except ProviderRefusal as exc:
        failure_category = "model_refusal"
        failure_message = str(exc)
    except IncompleteModelOutput as exc:
        failure_category = "incomplete_model_output"
        failure_message = str(exc)
    except OutputValidationError as exc:
        failure_category = "invalid_model_output"
        failure_message = str(exc)
        raw = recording_client.raw_output
        if isinstance(raw, str):
            try:
                output = json.loads(raw)
            except json.JSONDecodeError:
                output = None
        elif isinstance(raw, dict):
            output = raw
    except Exception as exc:
        failure_category = "application_failure"
        failure_message = f"evaluation case raised {type(exc).__name__}"

    if output is None and failure_category in {
        "infrastructure",
        "model_refusal",
        "incomplete_model_output",
    }:
        status = "BLOCKED" if failure_category == "infrastructure" else "FAIL"
        return {
            "case_id": case["id"],
            "category": case["category"],
            "model_output": _redact(recording_client.raw_output),
            "structural": {"status": status, "errors": [failure_message]},
            "properties": {"status": "BLOCKED" if status == "BLOCKED" else "FAIL", "checks": []},
            "semantic": {"score": None, "criteria": []},
            "failure_category": failure_category,
            "failure_message": _redact(failure_message),
        }

    structural = validate_structural(output)
    if output is None or not isinstance(output, dict):
        properties = {"status": "FAIL", "checks": []}
        semantic = {"score": None, "criteria": []}
    else:
        properties = evaluate_properties(case, output)
        semantic = score_semantic(case, output)
    return {
        "case_id": case["id"],
        "category": case["category"],
        "model_output": _redact(recording_client.raw_output),
        "application_output": _redact(application_output),
        "policy_adjustments": list(agent.policy_adjustments),
        "structural": structural,
        "properties": properties,
        "semantic": semantic,
        "failure_category": failure_category,
        "failure_message": _redact(failure_message),
    }


def _write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = stream.name
            json.dump(_redact(result), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def run_evaluation() -> dict[str, Any]:
    started = datetime.now(UTC)
    dataset = load_dataset()
    dataset_bytes = DATASET_PATH.read_bytes()
    provider = os.environ.get("REMINDER_PROVIDER", "openai").strip().casefold()
    model = os.environ.get("REMINDER_MODEL", "").strip()
    missing_configuration = []
    if provider not in {"openai", "ollama"}:
        missing_configuration.append("REMINDER_PROVIDER (openai or ollama)")
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
        missing_configuration.append("OPENAI_API_KEY")
    if not model:
        missing_configuration.append("REMINDER_MODEL")

    if missing_configuration:
        message = "required live-evaluation configuration is missing: " + ", ".join(
            missing_configuration
        )
        case_results = [_blocked_case(case, message) for case in dataset["cases"]]
    else:
        case_results = [_evaluate_one(case) for case in dataset["cases"]]

    aggregate = aggregate_results(case_results, threshold=dataset["threshold"])
    ended = datetime.now(UTC)
    result = {
        "format_version": "1.0",
        "provider": {
            "ollama": "Ollama (local)",
            "openai": "OpenAI",
        }.get(provider, "unknown"),
        "model": _redact(model) if model else None,
        "generation_settings": (
            {
                "max_output_tokens": 400,
                "timeout_seconds": 60,
                "temperature": 0.2,
                "stream": False,
                "structured_outputs": "local JSON Schema format",
                "host_scope": "loopback only",
            }
            if provider == "ollama"
            else {
                "max_output_tokens": 400,
                "timeout_seconds": 60,
                "max_retries": 1,
                "store": False,
                "structured_outputs": "strict",
            }
        ),
        "dataset_version": dataset["version"],
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "started_at_utc": started.isoformat(),
        "completed_at_utc": ended.isoformat(),
        "semantic_threshold": dataset["threshold"],
        "layer_summary": {
            "structural_passes": sum(
                item["structural"]["status"] == "PASS" for item in case_results
            ),
            "property_passes": sum(
                item["properties"]["status"] == "PASS" for item in case_results
            ),
            "semantic_scored_cases": sum(
                item["semantic"]["score"] is not None for item in case_results
            ),
        },
        "aggregate": aggregate,
        "cases": case_results,
        "credentials_recorded": False,
    }
    _write_result(RESULT_PATH, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the fixed live reminder evaluation dataset")
    parser.add_argument("--mode", choices=["live"], default="live")
    parser.parse_args(argv)
    try:
        result = run_evaluation()
    except Exception as exc:
        print(f"evaluation infrastructure failure ({type(exc).__name__})", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "decision": result["aggregate"]["decision"],
                "semantic_mean": result["aggregate"]["semantic_mean"],
                "cases": result["aggregate"]["case_count"],
                "infrastructure_failures": result["aggregate"]["infrastructure_failures"],
                "result_file": str(RESULT_PATH),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0 if result["aggregate"]["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
