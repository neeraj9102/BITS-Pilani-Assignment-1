"""Task operations and business rules."""

from __future__ import annotations

from typing import Any

from smart_todo.errors import TaskNotFoundError, ValidationError
from smart_todo.models import (
    Task,
    normalize_tags,
    validate_description,
    validate_priority,
    validate_status,
    validate_title,
)
from smart_todo.storage import JsonTaskStore

UNSET = object()
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
ALLOWED_TRANSITIONS = {
    "todo": {"in_progress", "cancelled"},
    "in_progress": {"todo", "done", "cancelled"},
    "done": {"in_progress"},
    "cancelled": {"todo"},
}


class TodoService:
    def __init__(self, data_file: str) -> None:
        self.store = JsonTaskStore(data_file)

    def create(
        self,
        title: str,
        *,
        description: Any = None,
        priority: str = "medium",
        tags: Any = None,
    ) -> Task:
        valid_title = validate_title(title)
        valid_description = validate_description(description)
        valid_priority = validate_priority(priority)
        valid_tags = normalize_tags(tags)
        state = self.store.load()
        number = state["next_id"]
        order = state["next_creation_order"]
        task = Task(
            id=f"T-{number:06d}",
            title=valid_title,
            description=valid_description,
            priority=valid_priority,
            tags=tuple(valid_tags),
            status="todo",
            creation_order=order,
        )
        new_state = {
            **state,
            "next_id": number + 1,
            "next_creation_order": order + 1,
            "tasks": [*state["tasks"], task.to_record()],
        }
        self.store.save(new_state)
        return task

    def get(self, task_id: str) -> Task:
        state = self.store.load()
        record = next((item for item in state["tasks"] if item["id"] == task_id), None)
        if record is None:
            raise TaskNotFoundError(f"task not found: {task_id}")
        return Task.from_record(record)

    def list_tasks(self, *, tags: Any = None, sort: str | None = None) -> list[Task]:
        state = self.store.load()
        tasks = [Task.from_record(record) for record in state["tasks"]]
        requested = normalize_tags(tags)
        if requested:
            wanted = {tag.casefold() for tag in requested}
            tasks = [task for task in tasks if wanted.issubset({tag.casefold() for tag in task.tags})]
        if sort is not None:
            if sort != "priority":
                raise ValidationError("sort must be 'priority' when specified")
            tasks.sort(key=lambda task: (PRIORITY_RANK[task.priority], task.creation_order))
        return tasks

    def update(
        self,
        task_id: str,
        *,
        title: Any = UNSET,
        description: Any = UNSET,
        priority: Any = UNSET,
        tags: Any = UNSET,
    ) -> Task:
        state = self.store.load()
        records = list(state["tasks"])
        index = next((i for i, record in enumerate(records) if record["id"] == task_id), None)
        if index is None:
            raise TaskNotFoundError(f"task not found: {task_id}")
        old = Task.from_record(records[index])
        new_title = old.title if title is UNSET else validate_title(title)
        new_description = old.description if description is UNSET else validate_description(description)
        new_priority = old.priority if priority is UNSET else validate_priority(priority)
        new_tags = list(old.tags) if tags is UNSET else normalize_tags(tags)
        updated = Task(
            old.id,
            new_title,
            new_description,
            new_priority,
            tuple(new_tags),
            old.status,
            old.creation_order,
        )
        records[index] = updated.to_record()
        self.store.save({**state, "tasks": records})
        return updated

    def delete(self, task_id: str) -> None:
        state = self.store.load()
        records = list(state["tasks"])
        remaining = [record for record in records if record["id"] != task_id]
        if len(remaining) == len(records):
            raise TaskNotFoundError(f"task not found: {task_id}")
        self.store.save({**state, "tasks": remaining})

    def set_status(self, task_id: str, new_status: str) -> Task:
        valid_status = validate_status(new_status)
        state = self.store.load()
        records = list(state["tasks"])
        index = next((i for i, record in enumerate(records) if record["id"] == task_id), None)
        if index is None:
            raise TaskNotFoundError(f"task not found: {task_id}")
        old = Task.from_record(records[index])
        if valid_status not in ALLOWED_TRANSITIONS[old.status]:
            raise ValidationError(f"transition from {old.status} to {valid_status} is not allowed")
        updated = Task(
            old.id,
            old.title,
            old.description,
            old.priority,
            old.tags,
            valid_status,
            old.creation_order,
        )
        records[index] = updated.to_record()
        self.store.save({**state, "tasks": records})
        return updated
