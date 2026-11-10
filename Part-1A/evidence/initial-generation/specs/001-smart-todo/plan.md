# Implementation Plan: Smart Todo Task Management

**Branch**: `001-smart-todo` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-smart-todo/spec.md`

## Summary

Build a small local task CLI with deterministic CRUD, exact tag filtering, priority ordering, explicit status transitions, and UTF-8 JSON persistence. Production behavior uses Python's standard library; an independent pytest contract suite and a single harness runner enforce compile/lint, Bandit SAST, and functional gates. The runner stores the actual command output and machine-readable outcomes for each execution.

## Technical Context

**Language/Version**: Python 3.12 for development; project supports Python 3.11+

**Primary Dependencies**: Python standard library for the application; pytest, Ruff, and Bandit as development/harness tools

**Storage**: One local UTF-8 JSON file; default `.data/tasks.json` beneath the working directory; path can be overridden for isolation

**Testing**: pytest unit and black-box CLI contract tests; Python compile check; Ruff lint; Bandit SAST

**Target Platform**: Windows, macOS, or Linux with Python 3.11+

**Project Type**: Single local command-line application

**Performance Goals**: Correctly create, retrieve, update, and delete the 100-task success fixture; list, filter, and sort the same fixture in a single invocation

**Constraints**: Deterministic behavior; no network, credentials, background service, or GUI; malformed store data must not be overwritten; harness records real results and exits nonzero on any failed mandatory gate

**Scale/Scope**: One local user; task management only; 100 tasks used for the principal end-to-end success fixture

## Constitution Check

| Principle / gate | Design response | Status |
|---|---|---|
| Specification before implementation | Requirements and acceptance scenarios are fixed in `spec.md`; task IDs will trace back to FR/SC IDs | PASS |
| Deterministic behavior | Sequential persisted IDs, explicit priority/status/tag rules, and no wall-clock or network dependency | PASS |
| Independent harness controls | `.harness/` invokes black-box CLI tests, Ruff, compile check, and Bandit; the application cannot edit results | PASS |
| Safe local data handling | Validate complete state before mutation; write a sibling temporary file and atomically replace only after successful serialization | PASS |
| Small CLI and traceable changes | Standard-library CLI and focused source tree; snapshots preserve initial and final production source | PASS |

No constitution violations require an exception.

## Design

### Architecture

The command-line layer parses arguments and calls a small service layer. The service layer validates task fields and state transitions. A storage layer reads/writes the versioned JSON document and owns atomic replacement. The test harness invokes commands as subprocesses against temporary stores, so contract assertions do not depend on private implementation functions.

### Data and ordering decisions

- Store document fields are `schema_version`, `next_id`, `next_creation_order`, and `tasks`.
- Each task stores `id`, `title`, `description`, `priority`, `tags`, `status`, and `creation_order`.
- IDs use the persisted sequential counter; deletion never decrements it.
- Priority order is high, medium, low. Equal priorities are ordered by immutable creation order.
- Tag values are normalized by trimming; matching is exact and case-insensitive; multiple filters use AND semantics.
- Invalid JSON or invalid task structure fails closed and leaves the source file untouched.

### Harness design

`.harness/run_harness.py` runs the same four gates in this order: `compileall`, Ruff lint, recursive Bandit scan of production code, and pytest unit/contract suite. It records each command, exit code, stdout, stderr, timestamp, and final pass/fail in a unique `evidence/harness-runs/<run-id>/` folder. It does not short-circuit after a failed gate. Any nonzero gate makes the overall result fail. The runner does not change tests or expected results.

Harness-run evidence is machine-generated. `evidence/harness-log.md` will contain headings and blank fields only; the student completes narrative entries and the final human ACCEPT/REJECT decision.

## Phase 0: Research

See [research.md](research.md). Python's built-in `argparse`, `json`, `pathlib`, and `tempfile` keep production dependencies small. pytest supplies isolated temporary directories and tests; Ruff provides the required lint gate; Bandit scans Python ASTs for common security issues. The official documentation sources are linked from `research.md` and the project README.

## Phase 1: Design Artifacts

- [data-model.md](data-model.md) defines the task and persisted store fields and constraints.
- [contracts/cli-contract.md](contracts/cli-contract.md) defines commands, input validation, output, and exit behavior.
- [contracts/task-store.schema.json](contracts/task-store.schema.json) defines the persisted store shape.
- [quickstart.md](quickstart.md) describes environment setup, app use, and the required validation commands.

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-todo/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── clarifications.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── cli-contract.md
│   └── task-store.schema.json
└── tasks.md
```

### Source Code (Part-1A root)

```text
src/smart_todo/
├── __init__.py
├── __main__.py
├── cli.py
├── models.py
├── service.py
└── storage.py
tests/
├── unit/
└── contract/
.harness/
└── run_harness.py
evidence/
├── initial-generation/
├── final-generation/
├── harness-runs/
└── harness-log.md
pyproject.toml
README.md
```

**Structure Decision**: A single `src/` package separates CLI, task rules, and JSON storage. Tests and `.harness/` remain outside production code. Generation snapshots and machine run records live under `evidence/` to make the initial-to-final path inspectable.

## Complexity Tracking

No constitution violations or unnecessary architecture layers are introduced.
