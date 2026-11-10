import io
import json
from contextlib import redirect_stderr, redirect_stdout

from smart_todo.cli import main


def invoke(store_path, *args):
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--data-file", str(store_path), *args])
    assert code == 0, err.getvalue()
    return json.loads(out.getvalue())


def test_tag_matching_is_casefolded_exact_and_uses_and_semantics(tmp_path):
    path = tmp_path / "tags.json"
    invoke(path, "add", "Alpha", "--tag", "School", "--tag", "Art")
    invoke(path, "add", "Beta", "--tag", "school", "--tag", "Artist")
    invoke(path, "add", "Gamma", "--tag", "School")

    assert [task["title"] for task in invoke(path, "list", "--tag", " school ")] == [
        "Alpha",
        "Beta",
        "Gamma",
    ]
    assert [task["title"] for task in invoke(path, "list", "--tag", "SCHOOL", "--tag", "art")] == [
        "Alpha"
    ]
    assert invoke(path, "list", "--tag", "school", "--tag", "missing") == []


def test_priority_sort_is_high_medium_low_and_stable_for_ties(tmp_path):
    path = tmp_path / "priorities.json"
    invoke(path, "add", "Medium first")
    invoke(path, "add", "Low", "--priority", "low")
    invoke(path, "add", "High first", "--priority", "high")
    invoke(path, "add", "Medium second")
    invoke(path, "add", "High second", "--priority", "high")

    assert [task["title"] for task in invoke(path, "list")] == [
        "Medium first",
        "Low",
        "High first",
        "Medium second",
        "High second",
    ]
    assert [task["title"] for task in invoke(path, "list", "--sort", "priority")] == [
        "High first",
        "High second",
        "Medium first",
        "Medium second",
        "Low",
    ]
