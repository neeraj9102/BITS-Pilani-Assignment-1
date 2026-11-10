# Tasks: Natural Language Reminder Agent

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` in this feature directory.

**Prerequisites**: Approved specification and plan; checklist review completed. Offline tests and a live model evaluation are required by the assignment and user request.

**Organization**: Tasks are dependency ordered and grouped by user story. Each story's tests precede implementation; live evaluation is performed only after the fixed dataset, rubric, and threshold are established.

## Phase 1: Setup

**Purpose**: Establish the package and explicit external model configuration.

- [X] T001 Create `pyproject.toml` with Python 3.11+, `openai`, `jsonschema`, `tzdata`, pytest, and Ruff dependencies
- [X] T002 [P] Create `.gitignore` for `.env`, virtual environments, caches, local results, and build output while preserving reviewed evidence
- [X] T003 [P] Add the Part 1B `README.md` with offline-test and secret-safe live-evaluation instructions
- [X] T004 Create `.env.example` with variable names only (`OPENAI_API_KEY`, `REMINDER_MODEL`) and no credential values

## Phase 2: Foundational

**Purpose**: Establish stable schemas, request/result types, and an injectable model boundary.

- [X] T005 Create `src/reminder_agent/__init__.py` and `src/reminder_agent/__main__.py` for the documented CLI entry point
- [X] T006 [P] Create typed request, reminder-context, result, and categorized error models in `src/reminder_agent/models.py`
- [X] T007 Create the full local validation contract from `specs/001-reminder-agent/contracts/reminder-output.schema.json` in `src/reminder_agent/validation.py`, including format, timezone, and cross-field validation not expressible in the provider subset (FR-002–009)
- [X] T008 Create the separate provider-compatible strict Structured Outputs schema in `src/reminder_agent/provider_schema.py`; close every object and avoid unsupported keywords
- [X] T009 Create an injectable Responses API protocol and fake-client fixture in `src/reminder_agent/client.py` and `tests/conftest.py`; never require a live key for unit tests

**Checkpoint**: Local schema, provider boundary, and offline fake client are ready.

## Phase 3: User Story 1 - Create a Reminder from Natural Language (Priority: P1, MVP)

**Goal**: Convert an unambiguous natural-language request into a valid future reminder proposal or a precise clarification.

**Independent Test**: Use a fixed reference timestamp and timezone with an injected fake response; validate output shape, task/time meaning, relative-date resolution, and missing-field clarification without live inference.

### Tests first

- [X] T010 [P] [US1] Write contract tests for exact output keys, enums, timestamps, IANA zones, and status-to-field relationships in `tests/contract/test_output_contract.py` (FR-002–009, SC-002)
- [X] T011 [P] [US1] Write agent tests for create prompts, absolute/relative times, future-time constraints, and missing title/date/time clarification in `tests/unit/test_create_agent.py` (FR-001, FR-005, FR-010, FR-012, SC-003–004)
- [X] T012 [US1] Run the tests in `tests/contract/test_output_contract.py` and `tests/unit/test_create_agent.py` with injected fixtures before implementation and preserve the real output

### Implementation

- [X] T013 [US1] Write the system prompt with untrusted request data separated from governing instructions in `prompts/system.md`
- [X] T014 [US1] Implement explicit Responses API Structured Outputs calls, incomplete/refusal detection, timeout/error classification, and credential-safe errors in `src/reminder_agent/openai_client.py` (FR-018, FR-021)
- [X] T015 [US1] Implement request bounds, fixed-reference parsing, model orchestration, full local validation, and JSON output in `src/reminder_agent/agent.py` (FR-001–005, FR-010, FR-012, SC-002–004)
- [X] T016 [US1] Implement create/clarify command input and output handling in `src/reminder_agent/cli.py`
- [X] T017 [US1] Run unchanged `tests/contract/test_output_contract.py` and `tests/unit/test_create_agent.py` offline and record actual outcomes

**Checkpoint**: Clear requests create valid future proposals; missing mandatory facts are clarified without invention.

## Phase 4: User Story 2 - Reschedule or Snooze an Existing Reminder (Priority: P2)

**Goal**: Propose time changes only for one reminder present in supplied read-only context.

**Independent Test**: Inject fixed context and output fixtures to verify target identity, explicit reschedule time, snooze base-time arithmetic, and clarification on no or multiple targets.

### Tests first

- [X] T018 [P] [US2] Write target-selection and reschedule tests in `tests/unit/test_reschedule_agent.py` (FR-006, FR-012, SC-003)
- [X] T019 [P] [US2] Write snooze arithmetic tests covering a due time before and after `reference_now` in `tests/unit/test_snooze_agent.py` (FR-011, SC-003)
- [X] T020 [US2] Run `tests/unit/test_reschedule_agent.py` and `tests/unit/test_snooze_agent.py` before adding story-specific behavior and preserve the real output

### Implementation

- [X] T021 [US2] Add explicit read-only reminder context and unique-target rules to `prompts/system.md`
- [X] T022 [US2] Implement reschedule/snooze intent and deterministic target/time invariants in `src/reminder_agent/agent.py` and `src/reminder_agent/validation.py` (FR-006, FR-011–012)
- [X] T023 [US2] Run unchanged `tests/unit/test_reschedule_agent.py` and `tests/unit/test_snooze_agent.py` offline and record actual outcomes

**Checkpoint**: A ready reschedule/snooze proposal references exactly one supplied target and obeys the specified due-time arithmetic.

## Phase 5: User Story 3 - Handle Unclear, Invalid, and Unsafe Requests (Priority: P3)

**Goal**: Clarify missing or ambiguous information, reject malformed/past/unsupported/unsafe requests, and never claim external side effects.

**Independent Test**: Exercise fixed malformed, ambiguous, past-time, unsupported-action, and adversarial fixtures with the fake client and validate all hard invariants.

### Tests first

- [X] T024 [P] [US3] Write malformed-input, missing-timezone, daylight-saving ambiguity, and past-time tests in `tests/unit/test_boundaries.py` (FR-009–010, FR-012–013, SC-003–004)
- [X] T025 [P] [US3] Write unsupported-action and prompt-injection guardrail tests asserting no tool calls or claimed side effects in `tests/unit/test_guardrails.py` (FR-013–015, SC-004)
- [X] T026 [US3] Run `tests/unit/test_boundaries.py` and `tests/unit/test_guardrails.py` before adding boundary/guardrail behavior and preserve the real output

### Implementation

- [X] T027 [US3] Implement safe clarification/rejection paths and deterministic datetime/zone checks in `src/reminder_agent/agent.py` and `src/reminder_agent/validation.py` (FR-007–013, FR-015, SC-003–004)
- [X] T028 [US3] Keep the API adapter free of calendar, messaging, notification, or other function tools in `src/reminder_agent/openai_client.py` (FR-014–015, SC-004)
- [X] T029 [US3] Run unchanged `tests/unit/test_boundaries.py` and `tests/unit/test_guardrails.py` offline and record actual outcomes

**Checkpoint**: Missing/ambiguous requests clarify; invalid, past, unsupported, and unsafe requests reject; no state or external side effect is claimed.

## Phase 6: Fixed Evaluation Dataset and Single Harness Pipeline

**Purpose**: Establish a versioned benchmark and a single inspectable pipeline before final live evaluation.

- [X] T030 Create exactly 18 distinct cases spanning representative, boundary, ambiguous, missing-information, malformed, and adversarial/guardrail categories in `evals/dataset.json`, each with requirement trace, expected properties, and a case-specific rubric (FR-016, FR-020, SC-001, SC-006)
- [X] T031 Validate the dataset against `specs/001-reminder-agent/contracts/evaluation-dataset.schema.json` and add dataset integrity tests in `tests/contract/test_dataset.py`
- [X] T032 [P] Write fixed-output tests for structural validation, property/invariant evaluation, semantic rubric scoring, aggregation, and infrastructure-failure classification in `tests/unit/test_evaluation.py` (FR-017–020, SC-002–006)
- [X] T033 Implement the single three-layer evaluation runner in `.harness/evaluate.py`; enforce hard structural/safety gates and the fixed 0.85 semantic threshold without modifying cases or expected values (FR-017, FR-019–020, SC-005)
- [X] T034 Implement per-case and aggregate `evidence/eval-results.json` generation with provider/model/non-secret settings, UTC time, dataset hash, exact case/layer outcomes, failures, and credential redaction in `.harness/evaluate.py` (FR-018, FR-021, SC-005)
- [X] T035 Create `evidence/initial-generation/`, `evidence/final-generation/`, `evidence/harness-runs/`, and a blank-field-only `evidence/harness-log.md`
- [X] T036 Snapshot the first complete production source, prompt, dataset, and evaluator under `evidence/initial-generation/` before any evidence-driven repair
- [ ] T037 Complete the live evaluation of `evals/dataset.json` using the configured real model; offline validation has passed, but the captured live run is `INCOMPLETE` with 18 configuration/infrastructure blocks and no model-quality scores
- [ ] T038 Feed any actual failed model cases from `evidence/eval-results.json` into implementation repairs without weakening requirements; no model output was available in the captured run, so this remains pending a configured live evaluation
- [X] T039 Snapshot the final available source, prompt, dataset, and evaluator under `evidence/final-generation/` after offline and live-availability validation, and update `README.md`/`specs/001-reminder-agent/quickstart.md` to match actual commands

## Dependencies & Execution Order

- Setup precedes foundational work; foundation precedes all stories.
- US1 precedes US2 and US3 because both require request parsing, the output contract, and the injectable client. US2 and US3 can proceed independently after US1.
- Dataset, rubric, threshold, and case traceability are fixed before the final live evaluation. The evaluator's structural and invariant layers remain independent of semantic scoring.
- Initial generation is snapshotted before repairs. Every real failed evaluation and unchanged re-run is machine-recorded. The final snapshot follows the final validation available in the configured environment.

## Parallel Opportunities

- T002, T003, and T006 can be authored in parallel after the project root is initialized.
- Within each story, independent test files can be authored in parallel before implementation.
- US2 and US3 can be implemented in parallel after the shared US1 core, subject to separate files.
- Dataset integrity tests and fixed-output evaluator tests can be authored in parallel; the live model run waits for the finished evaluator and local offline validation.

## Implementation Strategy

1. Establish the package, local schema validator, provider adapter seam, and offline fake client.
2. Complete US1 and validate create/clarification behavior using fixed outputs.
3. Complete US2 and US3 against the unchanged contract and safety tests.
4. Freeze the 18-case dataset, rubric, and threshold; implement and test the single three-layer evaluator.
5. Snapshot the first complete generation, execute offline and live commands, repair only actual root causes, rerun identical gates, and snapshot the final generation.

## Notes

- All evaluation cases and checks must trace to FR/SC requirements. Do not remove a difficult case or change the 0.85 threshold to produce PASS.
- A missing API key or provider outage is an infrastructure failure and leaves live model-quality evaluation incomplete; it is not a fabricated application failure or a passing evaluation.
- Harness-log narrative and final human ACCEPT/REJECT fields stay blank for the student. The machine-generated JSON result is preserved as actual evidence.
- No API key, secret value, request authorization header, or local `.env` file may be committed.

## Requirement Coverage Map

| Requirement | Task coverage |
|---|---|
| FR-001–009 | T006–T016, T024, T027 |
| FR-010–013 | T011, T015, T018–T019, T022, T024, T027 |
| FR-014–015 | T013, T025, T027–T028 |
| FR-016, FR-020 | T030–T033 |
| FR-017–019 | T014, T032–T034, T037–T038 |
| FR-021 | T014, T034, T037 |
| SC-001 | T030–T031 |
| SC-002 | T010, T015, T031–T034 |
| SC-003–004 | T011, T018–T019, T024–T028, T032–T033 |
| SC-005 | T032–T034, T037–T038 |
| SC-006 | T030, T032–T033 |
