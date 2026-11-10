import copy
import json

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from reminder_agent.models import OutputValidationError
from reminder_agent.provider_schema import PROVIDER_SCHEMA, RESULT_FIELDS
from reminder_agent.validation import OUTPUT_SCHEMA_PATH, parse_request_envelope, validate_output


def test_schema_is_valid_and_strict_at_both_object_levels(ready_create_result):
    full_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(full_schema)
    validator = Draft202012Validator(full_schema, format_checker=FormatChecker())
    assert validator.is_valid(ready_create_result)
    assert full_schema["additionalProperties"] is False
    assert full_schema["required"] == RESULT_FIELDS
    assert PROVIDER_SCHEMA["additionalProperties"] is False
    assert PROVIDER_SCHEMA["required"] == RESULT_FIELDS
    assert PROVIDER_SCHEMA["properties"]["reminder"]["anyOf"][1]["additionalProperties"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda result: result.update(extra="forbidden"),
        lambda result: result.update(intent="create-reminder"),
        lambda result: result.update(status="ready", reminder=None),
        lambda result: result["reminder"].update(due_at="2026-11-11T09:00:00"),
        lambda result: result["reminder"].update(timezone="Not/AZone"),
        lambda result: result["reminder"].update(title="   "),
    ],
)
def test_output_contract_rejects_malformed_or_invalid_results(
    mutation, ready_create_result, request_envelope
):
    result = copy.deepcopy(ready_create_result)
    mutation(result)
    request = parse_request_envelope(request_envelope)
    with pytest.raises(OutputValidationError):
        validate_output(result, request)


def test_ready_result_must_be_future_and_timezone_offset_must_match(
    ready_create_result, request_envelope
):
    request = parse_request_envelope(request_envelope)
    past = copy.deepcopy(ready_create_result)
    past["reminder"]["due_at"] = "2026-11-10T09:00:00+05:30"
    with pytest.raises(OutputValidationError, match="later than"):
        validate_output(past, request)

    wrong_offset = copy.deepcopy(ready_create_result)
    wrong_offset["reminder"]["due_at"] = "2026-11-11T09:00:00+00:00"
    with pytest.raises(OutputValidationError, match="offset does not match"):
        validate_output(wrong_offset, request)


def test_reschedule_target_must_exist_in_context(ready_create_result, request_envelope):
    request_envelope["existing_reminders"] = [
        {"id": "R-1", "title": "Pay rent", "due_at": "2026-11-12T09:00:00+05:30"}
    ]
    request = parse_request_envelope(request_envelope)
    result = copy.deepcopy(ready_create_result)
    result["intent"] = "reschedule"
    result["target_reminder_id"] = "R-missing"
    with pytest.raises(OutputValidationError, match="one supplied reminder"):
        validate_output(result, request)
