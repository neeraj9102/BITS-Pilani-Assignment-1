"""Shared error types for the Smart Todo application."""


class TodoError(Exception):
    """Base class for expected application errors."""


class ValidationError(TodoError):
    """Raised when a task or requested operation is invalid."""


class TaskNotFoundError(TodoError):
    """Raised when an operation references an unknown task ID."""


class StoreError(TodoError):
    """Raised when the persisted task store cannot be safely read or written."""
