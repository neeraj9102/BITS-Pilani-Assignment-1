# Implementation Plan: Natural Language Reminder Agent

**Branch**: `001-reminder-agent` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-reminder-agent/spec.md`

## Summary

Build a small Python reminder agent that calls a configured real model provider and returns a strict structured proposal. Keep the OpenAI Responses API adapter and add a loopback-only Ollama adapter for local inference; no OpenAI API key is available. Qwen2.5 1.5B and initial Qwen2.5 3B runs failed the fixed threshold; the 7B attempt was interrupted before scoring because of local resource pressure. Additional 3B runs exposed request-completeness, action, target-selection, and relative-time errors. Add general local guardrails for those high-confidence policy facts, preserve raw model and application outputs separately, and rerun the unchanged 18-case benchmark. Final run `live-20261110T151355.668584Z` passed all 18 structural and property checks with a 0.941667 mean against the unchanged 0.85 threshold. The model receives untrusted request text, a fixed reference time, a timezone, and read-only reminder context. The application has no calendar, notification, or other tool integration.

## Technical Context

**Language/Version**: Python 3.12 for development; project supports Python 3.11+

**Primary Dependencies**: Official OpenAI Python SDK for the optional hosted adapter; Python standard-library `urllib` for local Ollama calls; `jsonschema` for independent JSON Schema validation; `tzdata` for reliable IANA timezone data on platforms without a system database; pytest and Ruff for offline development checks

**Storage**: No application persistence. Evaluation dataset and schema are versioned JSON files; results are generated under `evidence/`.

**Testing**: pytest unit/contract tests use injected fake clients; live evaluation runs `evals/dataset.json` through the real model adapter and the same three-layer harness

**Target Platform**: Windows, macOS, or Linux with Python 3.11+; either a local Ollama service for this run or HTTPS access to OpenAI when the hosted adapter is selected

**Project Type**: Single local command-line application with external model inference

**Performance Goals**: Evaluate all 18 cases in one harness run and report per-case results; no latency target is defined by the assignment

**Constraints**: Provider/model are configured outside source control; no key is printed, saved, or committed. `OPENAI_API_KEY` is required only for OpenAI; local Ollama uses a loopback-only URL and no credentials. The model request has no tool definitions. The provider schema is independently revalidated locally.

**Scale/Scope**: One request per invocation; at least 15 dataset cases (18 planned); no stored reminders, multi-turn history, calendar integration, or notifications

## Constitution Check

| Principle / gate | Design response | Status |
|---|---|---|
| Specification before implementation | Output schema, temporal rules, safety requirements, dataset size, and threshold are fixed before code | PASS |
| Stable contract across variable wording | Strict structured output schema plus local validation; no exact generated-message matching | PASS |
| Clarify before unsafe or unsupported action | Prompt and deterministic invariant checks require clarification/rejection; no tool calls exist | PASS |
| Independent layered evaluation | One runner performs schema, property/invariant, semantic/rubric, and aggregation stages | PASS |
| Honest evidence and secret safety | Per-case machine results preserve failures; model/key configuration is separated and key values are never recorded | PASS |

No constitution violations require an exception. A real model is required for the assigned non-deterministic behavior. The evaluation runner reports a missing provider or service outage as an infrastructure failure, never as a model-quality pass.

## Design

### Application flow

1. The JSON-over-stdin CLI validates request-envelope shape and size, then supplies a reference timestamp, timezone, and optional existing-reminder context.
2. A prompt builder presents system rules and untrusted request data as separate content. No function tools are registered.
3. `REMINDER_PROVIDER=openai` uses the strict OpenAI Responses API adapter and its process-environment key. `REMINDER_PROVIDER=ollama` sends the same system/user messages and JSON Schema to the local Ollama `/api/chat` endpoint without tools or authorization headers.
4. High-confidence local request checks prevent completion when the title/date/time/target is missing or ambiguous, align explicit reschedule/snooze intent with one unique supplied target, compute relative durations from `reference_now`, and reject resolved past times.
5. The application validates the full local JSON Schema, validates timezone-aware date semantics and cross-field invariants, and returns JSON.
6. The evaluation harness stores raw model output, guarded application output, policy-adjustment notes, and evaluator results without secrets.

### Schema and API boundary

`contracts/reminder-output.schema.json` is the authoritative local JSON Schema. The provider-facing schema is closed and passed to OpenAI Structured Outputs or Ollama's JSON Schema `format`. Conditional relationships are enforced by the independent local validator. Refusals, incomplete responses, malformed output, timeouts, and provider failures are classified separately.

### Evaluation pipeline

The dataset will contain 18 cases: 4 representative creation cases, 3 date/time or boundary cases, 3 ambiguous/target-selection cases, 3 missing-information cases, 2 malformed-input cases, and 3 adversarial/guardrail cases. Every case has requirement links and expected properties or an explicit semantic rubric.

For each case the runner records:

- **Layer 1 - Structural**: JSON parse, exact keys, types/enums, timestamp with offset, and valid IANA timezone.
- **Layer 2 - Property/invariant**: status-intent/nullability mapping, required clarification/rejection, future due time, correct target, no unsupported side effect, and safe handling of adversarial input.
- **Layer 3 - Semantic/quality**: a per-case rubric scores task meaning, time meaning, or clarification usefulness without exact sentence matching. The 0-1 scores are averaged across cases.
- **Aggregate**: PASS requires every case to satisfy structure and invariants and a mean semantic score of at least 0.85. API/service errors make the run incomplete and are reported as infrastructure failures.

The evaluator does not use an LLM judge. For each case, the rubric assigns fixed weights to named criteria; each criterion produces a documented score from 0 to 1, the weighted sum gives the case score, and the arithmetic mean of case scores gives the dataset score. It compares normalized structured meaning and case-defined accepted terms, preserving an independent decision path from exact model wording.

`evidence/eval-results.json` is generated from a live harness run and includes provider, model identifier, non-secret settings, UTC execution time, request/case results, raw model output, guarded application output, policy-adjustment notes, layer metrics, score, decision, and categorized errors. It excludes API key values and authentication headers. Timestamped harness-run folders contain result snapshots so later runs do not replace earlier outcomes.

Harness output is machine-generated. `evidence/harness-log.md` will be a blank scaffold for the student to complete with narrative entries and the final human ACCEPT/REJECT decision.

## Phase 0: Research

See [research.md](research.md). OpenAI remains an optional hosted route; the current run uses the local Ollama API with JSON Schema structured output. `jsonschema` independently validates the full contract. Python `datetime`/`zoneinfo` validates timestamps and timezone rules; `tzdata` supplies IANA data where the operating system lacks it.

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

**Structure Decision**: A single `src/` package separates request handling, prompt construction, provider adapters, and validation. The dataset, schema, tests, and evaluator remain outside production modules. The provider adapter is injectable so offline tests do not require API credentials; the final dataset evaluation uses the configured real model.

## Complexity Tracking

The model adapter and evaluation layers are required by the assignment's non-deterministic application criteria. No tool-calling or calendar integration is introduced.
