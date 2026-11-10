# Natural Language Reminder Agent Constitution

## Core Principles

### I. Specification Before Implementation
The approved feature specification, clarifications, plan, tasks, schema, and evaluation criteria are the source of truth. Every supported intent, output field, safety boundary, and acceptance property MUST be defined before application code is written.

### II. Stable Contract Across Variable Wording
The agent MAY vary its explanatory wording, but MUST return the documented structured output contract. Schema fields, types, enumerations, required fields, and machine-checkable invariants MUST remain stable across model responses.

### III. Clarify Before Unsafe or Unsupported Action
The agent MUST ask for clarification when required reminder details are missing or ambiguous. It MUST NOT invent an exact date, time, timezone, or existing reminder identifier; claim an action was scheduled; or execute a side effect that is not explicitly supported.

### IV. Independent Layered Evaluation
The evaluation harness MUST independently validate structure, deterministic properties/invariants, and semantic quality. A semantic judge MUST NOT replace structural or invariant checks. The declared scoring method and threshold MUST be fixed before final evaluation.

### V. Honest Evidence and Secret Safety
The dataset, expected properties, threshold, and safety guards MUST NOT be weakened to obtain PASS. Model/service failures MUST be distinguished from application/evaluator failures. Credentials MUST remain outside source control, and model identity/configuration MUST be recorded without secrets.

## Engineering Constraints

- The application MUST support create, reschedule, snooze, and clarification outcomes for reminder requests. Unsupported intents MUST be rejected or clarified without pretending to complete an action.
- Every successful reminder output MUST contain the required task text and a valid, timezone-aware timestamp in the agreed ISO 8601 representation. The specification MUST define how relative dates are grounded and how ambiguous timezones are handled.
- Every evaluation case MUST identify its intended intent and include ground truth, deterministic properties, or a rubric that permits an inspectable decision.
- The evaluation dataset MUST contain at least 15 meaningful cases spanning representative behavior, boundaries, ambiguity, missing fields, malformed input, and guardrails.
- No calendar, messaging, notification, or other external side effect is in scope unless the feature specification later adds and constrains it.
- Runtime configuration MUST be injectable for tests. API keys and local `.env` files MUST never be committed.

## Development Workflow

- Complete and review the Spec Kit constitution, specification, clarifications, technical plan, requirements checklist, tasks, and consistency analysis before implementation.
- Keep the dataset and evaluators independent from the application prompts and implementation. Trace every case and check to a specification requirement.
- Run one evaluation pipeline that records schema, invariant/property, and semantic/quality outcomes and computes the declared aggregate result.
- On a genuine failure, preserve the case, generated output, failed requirement, evaluator result, and repair evidence; rerun the same pipeline after repair.
- Automated PASS is followed by human ACCEPT/REJECT review. Record limitations and residual risks. Do not manufacture failures or claim a human decision for the student.

## Governance

This constitution governs Part 1B and takes precedence over implementation convenience. Amendments MUST be made through the applicable Spec Kit artifact, reviewed for impact on the contract, safety rules, dataset, and scoring method, and recorded in version history. A legitimate requirement change MUST be made upstream and must preserve the old and new evidence. Each submitted result MUST disclose unresolved requirements and model limitations. The student remains responsible for the final human acceptance decision.

**Version**: 1.0.0 | **Ratified**: 2026-11-10 | **Last Amended**: 2026-11-10
