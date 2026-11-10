import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

from smart_todo.cli import main
from smart_todo.service import ALLOWED_TRANSITIONS, TodoService

STATUSES = ("todo", "in_progress", "done", "cancelled")


def invoke(store_path, *args):
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--data-file", str(store_path), *args])
    return code, out.getvalue(), err.getvalue()


def stage_task(service, task_id, target_status):
    path_to_status = {
        "todo": [],
        "in_progress": ["in_progress"],
        "done": ["in_progress", "done"],
        "cancelled": ["cancelled"],
    }
    for status in path_to_status[target_status]:
        service.set_status(task_id, status)


@pytest.mark.parametrize("source", STATUSES)
@pytest.mark.parametrize("target", STATUSES)
def test_every_allowed_and_disallowed_transition(source, target, tmp_path):
    path = tmp_path / f"{source}-{target}.json"
    service = TodoService(str(path))
    task = service.create("Transition fixture")
    stage_task(service, task.id, source)
    before = path.read_bytes()

    code, stdout, stderr = invoke(path, "status", task.id, target)
    if target in ALLOWED_TRANSITIONS[source]:
        assert code == 0, stderr
        updated = json.loads(stdout)
        assert updated["status"] == target
        assert service.get(task.id).status == target
    else:
        assert code != 0
        assert not stdout
        assert "not allowed" in stderr
        assert path.read_bytes() == before
