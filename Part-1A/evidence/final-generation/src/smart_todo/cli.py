"""Argument parsing and JSON command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from smart_todo.errors import TodoError
from smart_todo.service import UNSET, TodoService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smart-todo")
    parser.add_argument(
        "--data-file",
        default=".data/tasks.json",
        help="path to the local JSON task store",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="create a task")
    add.add_argument("title")
    add.add_argument("--description")
    add.add_argument("--priority", choices=["low", "medium", "high"], default="medium")
    add.add_argument("--tag", action="append", dest="tags")

    show = commands.add_parser("show", help="show one task")
    show.add_argument("task_id")

    listing = commands.add_parser("list", help="list tasks")
    listing.add_argument("--tag", action="append", dest="tags")
    listing.add_argument("--sort", choices=["priority"])

    update = commands.add_parser("update", help="update supplied task fields")
    update.add_argument("task_id")
    update.add_argument("--title")
    update.add_argument("--description")
    update.add_argument("--priority", choices=["low", "medium", "high"])
    tag_options = update.add_mutually_exclusive_group()
    tag_options.add_argument("--tag", action="append", dest="tags")
    tag_options.add_argument("--clear-tags", action="store_true")

    delete = commands.add_parser("delete", help="delete a task")
    delete.add_argument("task_id")

    status = commands.add_parser("status", help="transition a task status")
    status.add_argument("task_id")
    status.add_argument("status", choices=["todo", "in_progress", "done", "cancelled"])
    return parser


def _jsonable(value):
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "to_record"):
        return value.to_record()
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    service = TodoService(args.data_file)
    try:
        if args.command == "add":
            result = service.create(
                args.title,
                description=args.description,
                priority=args.priority,
                tags=args.tags,
            )
        elif args.command == "show":
            result = service.get(args.task_id)
        elif args.command == "list":
            result = service.list_tasks(tags=args.tags, sort=args.sort)
        elif args.command == "update":
            result = service.update(
                args.task_id,
                title=args.title if args.title is not None else UNSET,
                description=args.description if args.description is not None else UNSET,
                priority=args.priority if args.priority is not None else UNSET,
                tags=[] if args.clear_tags else (args.tags if args.tags is not None else UNSET),
            )
        elif args.command == "delete":
            service.delete(args.task_id)
            result = {"deleted": args.task_id}
        else:
            result = service.set_status(args.task_id, args.status)
    except TodoError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(_jsonable(result), ensure_ascii=False, separators=(",", ":")))
    return 0
