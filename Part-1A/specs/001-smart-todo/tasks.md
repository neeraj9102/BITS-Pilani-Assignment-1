# Tasks: Smart Todo Task Management

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` in this feature directory.

**Prerequisites**: Approved specification and plan; checklist review completed. Tests are required by the assignment and user request.

**Organization**: Tasks are dependency ordered and grouped by user story. Each story receives tests before implementation, with a genuine pre-implementation test run.

## Phase 1: Setup

**Purpose**: Establish the package and reproducible development environment.

- [X] T001 Create `pyproject.toml` with the Python 3.11+ `src` package, pytest, Ruff, and Bandit development dependencies
- [X] T002 [P] Create `.gitignore` covering virtual environments, build output, `.data/`, caches, and secrets without ignoring evidence
- [X] T003 [P] Add root `README.md` linking the approved spec, quickstart, and harness instructions

## Phase 2: Foundational

**Purpose**: Establish stable package and error conventions used by all stories.

- [X] T004 Create `src/smart_todo/__init__.py` and `src/smart_todo/__main__.py` so the documented `python -m smart_todo` entry point is usable
- [X] T005 Create shared application and store error types in `src/smart_todo/errors.py`

**Checkpoint**: Package metadata and common error handling are ready.

## Phase 3: User Story 1 - Manage Tasks (Priority: P1, MVP)

**Goal**: Create, retrieve, update, and delete tasks while preserving valid state across process restarts.

**Independent Test**: Use a temporary JSON store and black-box subprocess commands to exercise CRUD, defaults, field preservation, ID monotonicity, invalid-input atomicity, and restart persistence.

### Tests first

- [X] T006 [P] [US1] Write model and validation tests for title/description/tag bounds, defaults, enum values, and unique tags in `tests/unit/test_models.py` (FR-002–006, FR-013)
- [X] T007 [P] [US1] Write store tests for missing-file defaults, schema validation, ID counters, atomic writes, malformed JSON, and unchanged files after rejected mutations in `tests/unit/test_storage.py` (FR-008, FR-011–013, SC-002, SC-006)
- [X] T008 [P] [US1] Write black-box CLI CRUD contract tests, including restart persistence, unknown IDs, and replacing/clearing optional fields and tags, in `tests/contract/test_crud_cli.py` (FR-001, FR-013, FR-015–016, SC-001–002)
- [X] T009 [US1] Run `python -m pytest tests/unit/test_models.py tests/unit/test_storage.py tests/contract/test_crud_cli.py` before production implementation and preserve the real output in development evidence

### Implementation

- [X] T010 [US1] Implement validated task models, enums, and allowed-field rules in `src/smart_todo/models.py` (FR-002–006)
- [X] T011 [US1] Implement strict UTF-8 store loading, complete-state validation, sequential counters, sibling-temp writes, and atomic replacement in `src/smart_todo/storage.py` (FR-008, FR-011–012)
- [X] T012 [US1] Implement create, show, update, and delete services with no mutation on invalid input in `src/smart_todo/service.py` (FR-001–004, FR-013)
- [X] T013 [US1] Implement `add`, `show`, `update`, and `delete` JSON CLI commands, selectable/default local paths, empty-tag replacement, non-zero error exits, and a standard-library-only runtime in `src/smart_todo/cli.py` (FR-001, FR-013, FR-015–016)
- [X] T014 [US1] Run the unchanged CRUD tests in `tests/unit/test_models.py`, `tests/unit/test_storage.py`, and `tests/contract/test_crud_cli.py`, then record actual outcomes

**Checkpoint**: All CRUD commands preserve the specified task fields and durable store invariants.

## Phase 4: User Story 2 - Find and Prioritize Work (Priority: P2)

**Goal**: Return exact tag-filter membership and stable priority ordering.

**Independent Test**: Seed a fixed mixed fixture, then compare the complete result membership and ordering with specification-derived expectations.

### Tests first

- [X] T015 [P] [US2] Write tag case-folding, exact-match, AND-filter, empty-result, and stable priority-order contract tests in `tests/contract/test_filter_sort_cli.py` (FR-009–010, FR-014, SC-003–004)
- [X] T016 [US2] Run `tests/contract/test_filter_sort_cli.py` against the initial filtering and sorting implementation and preserve the real output

### Implementation

- [X] T017 [US2] Implement exact case-insensitive AND tag matching and stable `high`, `medium`, `low` sorting in `src/smart_todo/service.py` (FR-009–010, FR-014)
- [X] T018 [US2] Add repeated `--tag` and `--sort priority` options to the list command in `src/smart_todo/cli.py` (FR-001, FR-009–010, FR-014)
- [X] T019 [US2] Run the unchanged `tests/contract/test_filter_sort_cli.py` and record actual outcomes

**Checkpoint**: Filtered results contain all and only matching tasks; equal-priority items retain creation order.

## Phase 5: User Story 3 - Track Task Status (Priority: P3)

**Goal**: Enforce the exact lifecycle transition table without changing state on rejected requests.

**Independent Test**: Exercise every allowed transition and every disallowed source/target pair against the public CLI; compare persisted state before and after rejection.

### Tests first

- [X] T020 [P] [US3] Write the complete allowed/disallowed transition matrix and no-mutation contract tests in `tests/contract/test_status_cli.py` (FR-006–007, FR-013, SC-005)
- [X] T021 [US3] Run `tests/contract/test_status_cli.py` against the initial transition implementation and preserve the real output

### Implementation

- [X] T022 [US3] Implement the FR-007 transition table and rejected-transition immutability in `src/smart_todo/service.py` (FR-006–007, FR-013)
- [X] T023 [US3] Expose the `status TASK_ID STATUS` CLI command in `src/smart_todo/cli.py` (FR-001, FR-006–007)
- [X] T024 [US3] Run the unchanged `tests/contract/test_status_cli.py` and record actual outcomes

**Checkpoint**: Every permitted transition succeeds and every other transition fails without mutation.

## Phase 6: Independent Harness, Evidence, and Polish

**Purpose**: Run independent quality/security/functionality gates and preserve the first and final code generations.

- [X] T025 Create `.harness/run_harness.py` to run compileall, Ruff, Bandit, and pytest in order, continue through failures, retain exact command/exit/stdout/stderr/timestamp data, and return non-zero if any gate fails (SC-001–006)
- [X] T026 Create harness-run verification tests in `tests/unit/test_harness.py` without allowing production code to write or alter expectations
- [X] T027 Create `evidence/initial-generation/`, `evidence/final-generation/`, `evidence/harness-runs/`, and a blank-field-only `evidence/harness-log.md`
- [X] T028 Snapshot the first complete source generation to `evidence/initial-generation/` before any harness-driven repair
- [X] T029 Execute the same `.harness/run_harness.py` before and after evidence-driven repairs; preserve each genuine run under `evidence/harness-runs/` and never change tests/specifications to force PASS
- [X] T030 Snapshot the final validated source to `evidence/final-generation/` and update `README.md`/`specs/001-smart-todo/quickstart.md` to match actual commands

## Dependencies & Execution Order

- Setup precedes foundational package work; foundational work precedes all stories.
- US1 precedes US2 and US3 because filtering, sorting, and lifecycle changes operate on persisted tasks. US2 and US3 are otherwise independent after US1.
- In every story, tests are written and run before the corresponding implementation. The tests remain unchanged during repair.
- The initial source snapshot is captured after the first full implementation and before any harness-driven code repair. The final snapshot is captured only after the final unchanged harness run.

## Parallel Opportunities

- T002 and T003 can run independently after project setup.
- Within US1, model, store, and black-box contract test files can be authored in parallel; implementation remains sequential by dependency.
- US2 and US3 test files can be prepared in parallel, but implementation depends on completed US1 CRUD.

## Implementation Strategy

1. Complete setup and foundational package tasks.
2. Complete US1 as the MVP and validate it with its unchanged tests.
3. Add and independently validate US2 and US3.
4. Capture the first complete source, run the four-gate harness, repair root causes without weakening criteria, rerun the same harness, and capture the final source generation.

## Notes

- Each task uses the Spec Kit checklist format and names the exact affected file path.
- Harness outcomes are machine generated. `harness-log.md` narrative and final human ACCEPT/REJECT fields stay blank for the student.
- Assignment-driven evidence includes the original and final code generations, every real harness run, and any actual failure/repair cycle.
- The initial shared service/CLI pass included filtering, sorting, and status transitions before their dedicated story test files were authored. The acceptance criteria and tests were retained and then run unchanged; this is a procedural deviation from the planned per-story test-first order and is recorded rather than hidden.

## Requirement Coverage Map

| Requirement | Task coverage |
|---|---|
| FR-001–008 | T006–T013, T018, T020–T023 |
| FR-009–010 | T015, T017–T018 |
| FR-011–016 | T007–T008, T011–T013, T025–T030 |
| SC-001–002 | T007–T008, T025–T030 |
| SC-003–004 | T015, T017–T019, T025–T030 |
| SC-005 | T020–T024, T025–T030 |
| SC-006 | T007–T008, T025–T030 |
