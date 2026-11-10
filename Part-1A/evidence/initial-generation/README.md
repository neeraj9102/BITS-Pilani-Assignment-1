# Part 1A — Smart Todo

This is the deterministic application for BITS Pilani Assignment 1. The approved source of behavior is the Spec Kit feature specification at [`specs/001-smart-todo/spec.md`](specs/001-smart-todo/spec.md). The CLI uses only the Python standard library; the independent harness uses pytest, Ruff, and Bandit.

## Setup and run

See [`specs/001-smart-todo/quickstart.md`](specs/001-smart-todo/quickstart.md). Install development tools with `python -m pip install -e ".[dev]"`, then run commands with `python -m smart_todo`.

## Independent validation

Run `python .harness/run_harness.py`. The runner executes compileall, Ruff, Bandit, and pytest in that order and continues through failures. Each command, exit code, stdout, stderr, timestamp, and gate result is recorded under `evidence/harness-runs/`. Any failed mandatory gate makes the run fail. Evidence is machine generated; the student completes `evidence/harness-log.md` and the final human acceptance decision.

## Spec Kit artifacts

The constitution and feature artifacts are under `.specify/` and `specs/001-smart-todo/`. The reviewed acceptance criteria are linked in the feature spec. Code snapshots and genuine harness outputs are retained under `evidence/`.
