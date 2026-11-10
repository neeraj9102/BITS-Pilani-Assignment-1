"""Domain models and input validation for Smart Todo."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from smart_todo.errors import ValidationError

TASK_ID_PATTERN = re.compile(r"^T-\d{6,}$")


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


def validate_title(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("title must be text")
    normalized = value.strip()
    if not normalized:
        raise ValidationError("title must not be empty")
    if len(normalized) > 200:
        raise ValidationError("title must be at most 200 characters")
    return normalized


def validate_description(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError("description must be text")
    if len(value) > 2000:
        raise ValidationError("description must be at most 2000 characters")
    return value


def validate_priority(value: Any) -> str:
    if not isinstance(value, str) or value not in {item.value for item in Priority}:
        raise ValidationError("priority must be one of: low, medium, high")
    return value


def validate_status(value: Any) -> str:
    if not isinstance(value, str) or value not in {item.value for item in Status}:
        raise ValidationError("status must be one of: todo, in_progress, done, cancelled")
    return value


def normalize_tags(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple)):
        raise ValidationError("tags must be a list of text values")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValidationError("each tag must be text")
        tag = value.strip()
        if not tag:
            raise ValidationError("tags must not be empty")
        if len(tag) > 32:
            raise ValidationError("each tag must be at most 32 characters")
        folded = tag.casefold()
        if folded in seen:
            raise ValidationError("tags must be unique, ignoring case")
        result.append(tag)
        seen.add(folded)
    return result


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    title: str
    description: str
    priority: str
    tags: tuple[str, ...]
    status: str
    creation_order: int

    @classmethod
    def from_record(cls, record: Any) -> Task:
        expected = {
            "id",
            "title",
            "description",
            "priority",
            "tags",
            "status",
            "creation_order",
        }
        if not isinstance(record, dict) or set(record) != expected:
            raise ValidationError("task record has missing or unknown fields")
        task_id = record["id"]
        if not isinstance(task_id, str) or not TASK_ID_PATTERN.fullmatch(task_id):
            raise ValidationError("task ID has an invalid format")
        title = validate_title(record["title"])
        if title != record["title"]:
            raise ValidationError("stored task title must already be trimmed")
        description = validate_description(record["description"])
        priority = validate_priority(record["priority"])
        status = validate_status(record["status"])
        tags = normalize_tags(record["tags"])
        if tags != record["tags"]:
            raise ValidationError("stored tags must already be trimmed")
        order = record["creation_order"]
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise ValidationError("creation_order must be a non-negative integer")
        return cls(task_id, title, description, priority, tuple(tags), status, order)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "tags": list(self.tags),
            "status": self.status,
            "creation_order": self.creation_order,
        }
