import json

import pytest

from smart_todo.errors import StoreError, ValidationError
from smart_todo.models import validate_title
from smart_todo.service import TodoService
from smart_todo.storage import JsonTaskStore


def test_missing_file_is_an_empty_store(tmp_path):
    path = tmp_path / "tasks.json"
    store = JsonTaskStore(path)
    assert store.load() == {
        "schema_version": 1,
        "next_id": 1,
        "next_creation_order": 0,
        "tasks": [],
    }
    assert not path.exists()


def test_invalid_existing_json_is_not_rewritten(tmp_path):
    path = tmp_path / "tasks.json"
    original = b'{"tasks":'
    path.write_bytes(original)
    with pytest.raises(StoreError):
        JsonTaskStore(path).load()
    assert path.read_bytes() == original


def test_structurally_invalid_state_is_rejected_without_overwrite(tmp_path):
    path = tmp_path / "tasks.json"
    invalid = {"schema_version": 99, "next_id": 1, "next_creation_order": 0, "tasks": []}
    path.write_text(json.dumps(invalid), encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(StoreError):
        JsonTaskStore(path).load()
    assert path.read_bytes() == original


def test_validation_failure_happens_before_store_mutation():
    with pytest.raises(ValidationError):
        validate_title("  ")


def test_one_hundred_tasks_survive_restart_and_lifecycle_operations(tmp_path):
    path = tmp_path / "one-hundred.json"
    first_process = TodoService(str(path))
    created = [
        first_process.create(
            f"Task {number:03d}",
            description=f"Description {number}",
            priority=("high", "medium", "low")[number % 3],
            tags=["assignment", f"group-{number % 4}"],
        )
        for number in range(100)
    ]
    assert len({task.id for task in created}) == 100

    restarted = TodoService(str(path))
    reopened = restarted.list_tasks()
    assert len(reopened) == 100
    assert [task.id for task in reopened] == [task.id for task in created]
    assert [task.creation_order for task in reopened] == list(range(100))
    assert reopened[49].title == "Task 049"
    assert reopened[49].description == "Description 49"

    updated = restarted.update("T-000050", title="Updated task 49", priority="high")
    assert updated.title == "Updated task 49"
    assert updated.creation_order == 49
    restarted.delete("T-000001")
    new_task = restarted.create("Replacement task")
    assert new_task.id == "T-000101"
    assert len(restarted.list_tasks()) == 100


def test_failed_atomic_replace_keeps_last_valid_store(tmp_path, monkeypatch):
    import smart_todo.storage as storage_module

    path = tmp_path / "tasks.json"
    store = JsonTaskStore(path)
    empty = store.load()
    store.save(empty)
    original = path.read_bytes()
    changed = dict(empty, next_id=2)

    def fail_replace(*_args, **_kwargs):
        raise OSError("simulated filesystem replace failure")

    monkeypatch.setattr(storage_module.os, "replace", fail_replace)
    with pytest.raises(StoreError):
        store.save(changed)
    assert path.read_bytes() == original
