import pytest

from smart_todo.errors import ValidationError
from smart_todo.models import (
    normalize_tags,
    validate_description,
    validate_priority,
    validate_status,
    validate_title,
)


def test_title_is_trimmed_and_bounded():
    assert validate_title("  Write tests  ") == "Write tests"
    with pytest.raises(ValidationError):
        validate_title("   ")
    with pytest.raises(ValidationError):
        validate_title("x" * 201)
    assert len(validate_title("x" * 200)) == 200


def test_description_bounds_and_empty_value():
    assert validate_description(None) == ""
    assert validate_description("") == ""
    assert validate_description("x" * 2000) == "x" * 2000
    with pytest.raises(ValidationError):
        validate_description("x" * 2001)


def test_tags_are_trimmed_bounded_and_casefold_unique():
    assert normalize_tags(["  school ", "Urgent"]) == ["school", "Urgent"]
    with pytest.raises(ValidationError):
        normalize_tags([" "])
    with pytest.raises(ValidationError):
        normalize_tags(["x" * 33])
    with pytest.raises(ValidationError):
        normalize_tags(["School", " school "])


@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_allowed_priority_values(priority):
    assert validate_priority(priority) == priority


def test_invalid_priority_and_status_values_are_rejected():
    with pytest.raises(ValidationError):
        validate_priority("urgent")
    for status in ("todo", "in_progress", "done", "cancelled"):
        assert validate_status(status) == status
    with pytest.raises(ValidationError):
        validate_status("blocked")
