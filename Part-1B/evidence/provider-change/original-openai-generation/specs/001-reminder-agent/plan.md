# Implementation Plan: Natural Language Reminder Agent

**Branch**: `001-reminder-agent` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-reminder-agent/spec.md`

## Summary

Build a small Python reminder parser that calls the OpenAI Responses API and returns a strict structured proposal. The model receives untrusted request text, a fixed reference time, a timezone, and read-only reminder context. The application performs independent local schema and temporal/property checks. A single evaluation runner executes 18 meaningful cases through structural validation, invariant checks, a case-specific semantic rubric, aggregation, and inspectable result capture. The application has no calendar, notification, or other tool integration.

## Technical Context

**Language/Version**: Python 3.12 for development; project supports Python 3.11+

**Primary Dependencies**: Official OpenAI Python SDK for Responses API calls; `jsonschema` for independent JSON Schema validation; `tzdata` for reliable IANA timezone data on platforms without a system database; pytest and Ruff for offline development checks

**Storage**: No application persistence. Evaluation dataset and schema are versioned JSON files; results are generated under `evidence/`.

**Testing**: pytest unit/contract tests use injected fake clients; live evaluation runs `evals/dataset.json` through the real model adapter and the same three-layer harness

**Target Platform**: Windows, macOS, or Linux with Python 3.11+ and HTTPS access to OpenAI API for live evaluation

**Project Type**: Single local command-line application with external model inference

**Performance Goals**: Evaluate all 18 cases in one harness run and report per-case results; no latency target is defined by the assignment

**Constraints**: Provider/model are configured outside source control; no key is printed, saved, or committed. Live evaluation requires `OPENAI_API_KEY` and `REMINDER_MODEL`. Exact model availability depends on the user's API account. The provider schema must use only the supported Structured Outputs subset; the full contract is revalidated locally.

**Scale/Scope**: One request per invocation; at least 15 dataset cases (18 planned); no stored reminders, multi-turn history, calendar integration, or notifications

## Constitution Check

| Principle / gate | Design response | Status |
|---|---|---|
| Specification before implementation | Output schema, temporal rules, safety requirements, dataset size, and threshold are fixed before code | PASS |
| Stable contract across variable wording | Strict structured output schema plus local validation; no exact generated-message matching | PASS |
| Clarify before unsafe or unsupported action | Prompt and deterministic invariant checks require clarification/rejection; no tool calls exist | PASS |
| Independent layered evaluation | One runner performs schema, property/invariant, semantic/rubric, and aggregation stages | PASS |
| Honest evidence and secret safety | Per-case machine results preserve failures; model/key configuration is separated and key values are never recorded | PASS |

No constitution violations require an exception. The external model requirement is part of the assigned non-deterministic behavior. The evaluation runner will report a missing key or service outage as an infrastructure failure, never as a model-quality pass.

## Design

### Application flow

1. The JSON-over-stdin CLI validates request-envelope shape and size, then supplies a reference timestamp, timezone, and optional existing-reminder context.
2. A prompt builder presents system rules and untrusted request data as separate content. No function tools are registered.
3. The OpenAI Responses API receives a strict Structured Outputs schema for the seven-field response contract. `OPENAI_API_KEY` is read by the official SDK from the environment; `REMINDER_MODEL` selects a model available to the account.
4. The application parses the response, validates the full local JSON Schema, validates timezone-aware date semantics and cross-field invariants, and returns JSON.
5. The evaluation harness stores model output and evaluator results without secrets.

### Schema and API boundary

`contracts/reminder-output.schema.json` is the authoritative local JSON Schema. A provider-facing schema is kept compatible with OpenAI Structured Outputs, including closed objects (`additionalProperties: false`) and supported field constraints. Conditional relationships that Structured Outputs does not support are enforced by the independent local validator. Refusals, incomplete responses, malformed output, timeouts, and API failures are classified separately.

### Evaluation pipeline

The dataset will contain 18 cases: 4 representative creation cases, 3 date/time or boundary cases, 3 ambiguous/target-selection cases, 3 missing-information cases, 2 malformed-input cases, and 3 adversarial/guardrail cases. Every case has requirement links and expected properties or an explicit semantic rubric.

For each case the runner records:

- **Layer 1 - Structural**: JSON parse, exact keys, types/enums, timestamp with offset, and valid IANA timezone.
- **Layer 2 - Property/invariant**: status-intent/nullability mapping, required clarification/rejection, future due time, correct target, no unsupported side effect, and safe handling of adversarial input.
- **Layer 3 - Semantic/quality**: a per-case rubric scores task meaning, time meaning, or clarification usefulness without exact sentence matching. The 0-1 scores are averaged across cases.
- **Aggregate**: PASS requires every case to satisfy structure and invariants and a mean semantic score of at least 0.85. API/service errors make the run incomplete and are reported as infrastructure failures.

The evaluator does not use an LLM judge. For each case, the rubric assigns fixed weights to named criteria; each criterion produces a documented score from 0 to 1, the weighted sum gives the case score, and the arithmetic mean of case scores gives the dataset score. It compares normalized structured meaning and case-defined accepted terms, preserving an independent decision path from exact model wording.

`evidence/eval-results.json` is generated from a live harness run and includes provider, model identifier, non-secret settings, UTC execution time, request/case results, layer metrics, score, decision, and categorized errors. It excludes API key values and authentication headers.

Harness output is machine-generated. `evidence/harness-log.md` will be a blank scaffold for the student to complete with narrative entries and the final human ACCEPT/REJECT decision.

## Phase 0: Research

See [research.md](research.md). The official OpenAI Python SDK and Responses API provide the model call and Structured Outputs. The API's supported schema subset is narrower than full JSON Schema, so local validation remains mandatory. The `jsonschema` library independently validates the full contract. Python `datetime`/`zoneinfo` validates absolute timestamps and timezone rules; `tzdata` supplies IANA data where the operating system lacks it.

## Phase 1: Design Artifacts

- [data-model.md](data-model.md) defines the request, output, reminder context, case, and result structures.
- [contracts/reminder-output.schema.json](contracts/reminder-output.schema.json) defines the full output contract.
- [contracts/evaluation-dataset.schema.json](contracts/evaluation-dataset.schema.json) defines evaluation case structure.
- [quickstart.md](quickstart.md) documents offline tests, secret-safe configuration, and live evaluation.

## Project Structure

### Documentation (this feature)

Artifacts are under `specs/001-reminder-agent/`: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `clarifications.md`, `checklists/requirements.md`, `contracts/reminder-output.schema.json`, `contracts/evaluation-dataset.schema.json`, and `tasks.md`.

### Source Code (Part-1B root)

Production code is under `src/reminder_agent/`; the prompt is under `prompts/`; the dataset is `evals/dataset.json`; tests are under `tests/unit/` and `tests/contract/`; the single evaluation runner is `.harness/evaluate.py`; generated evidence is under `evidence/`; dependency and execution metadata are in `pyproject.toml`; user instructions are in `README.md`.

**Structure Decision**: A single `src/` package separates request handling, prompt construction, model access, and validation. The dataset, schema, tests, and evaluator remain outside production modules. The model adapter is injectable so offline tests do not require API credentials; the final dataset evaluation uses the configured real provider.

## Complexity Tracking

The model adapter and evaluation layers are required by the assignment's non-deterministic application criteria. No tool-calling or calendar integration is introduced.
