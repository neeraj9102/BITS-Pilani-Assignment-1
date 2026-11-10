import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "evals" / "dataset.json"
SCHEMA_PATH = (
    ROOT
    / "specs"
    / "001-reminder-agent"
    / "contracts"
    / "evaluation-dataset.schema.json"
)


def test_dataset_matches_schema_and_has_all_required_case_categories():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(dataset))
    assert not errors, "\n".join(error.message for error in errors)

    cases = dataset["cases"]
    assert len(cases) == 18
    assert len({case["id"] for case in cases}) == 18
    assert Counter(case["category"] for case in cases) == {
        "representative": 4,
        "boundary": 3,
        "ambiguous": 3,
        "missing_information": 3,
        "malformed": 2,
        "adversarial_guardrail": 3,
    }


def test_each_case_has_traceable_machine_expectations_and_fixed_weights():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    for case in dataset["cases"]:
        assert case["requirements"]
        assert case["expected"]["properties"] is not None
        assert case["rubric"]
        criteria = [item["criterion"] for item in case["rubric"]]
        assert len(criteria) == len(set(criteria))
        assert abs(sum(item["weight"] for item in case["rubric"]) - 1.0) < 1e-9
