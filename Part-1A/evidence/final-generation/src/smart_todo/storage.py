"""Validated, atomic JSON persistence for the task store."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from smart_todo.errors import StoreError, ValidationError
from smart_todo.models import Task

STORE_FIELDS = {"schema_version", "next_id", "next_creation_order", "tasks"}


def empty_store() -> dict[str, Any]:
    return {"schema_version": 1, "next_id": 1, "next_creation_order": 0, "tasks": []}


def validate_store(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != STORE_FIELDS:
        raise ValidationError("store has missing or unknown fields")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise ValidationError("unsupported store schema version")
    next_id = value["next_id"]
    next_order = value["next_creation_order"]
    if isinstance(next_id, bool) or not isinstance(next_id, int) or next_id < 1:
        raise ValidationError("next_id must be a positive integer")
    if isinstance(next_order, bool) or not isinstance(next_order, int) or next_order < 0:
        raise ValidationError("next_creation_order must be a non-negative integer")
    records = value["tasks"]
    if not isinstance(records, list):
        raise ValidationError("tasks must be an array")

    tasks: list[Task] = []
    seen_ids: set[str] = set()
    seen_orders: set[int] = set()
    max_id_number = 0
    max_order = -1
    for record in records:
        task = Task.from_record(record)
        if task.id in seen_ids:
            raise ValidationError("task IDs must be unique")
        if task.creation_order in seen_orders:
            raise ValidationError("creation_order values must be unique")
        seen_ids.add(task.id)
        seen_orders.add(task.creation_order)
        max_id_number = max(max_id_number, int(task.id[2:]))
        max_order = max(max_order, task.creation_order)
        tasks.append(task)
    if next_id <= max_id_number:
        raise ValidationError("next_id must exceed every task ID to prevent ID reuse")
    if next_order <= max_order:
        raise ValidationError("next_creation_order must exceed every task creation_order")
    if [task.creation_order for task in tasks] != sorted(task.creation_order for task in tasks):
        raise ValidationError("stored tasks must retain creation order")
    return {
        "schema_version": 1,
        "next_id": next_id,
        "next_creation_order": next_order,
        "tasks": [task.to_record() for task in tasks],
    }


class JsonTaskStore:
    """Read and atomically replace one UTF-8 JSON task store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return empty_store()
        try:
            raw = self.path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            return validate_store(parsed)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
            raise StoreError(f"cannot read task store: {exc}") from exc

    def save(self, store: Any) -> None:
        try:
            valid = validate_store(store)
        except ValidationError as exc:
            raise StoreError(f"refusing invalid task store: {exc}") from exc

        temporary_path: str | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = temporary.name
                json.dump(valid, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
        except OSError as exc:
            raise StoreError(f"cannot safely save task store: {exc}") from exc
        finally:
            if temporary_path and os.path.exists(temporary_path):
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
