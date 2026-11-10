# Data Model: Natural Language Reminder Agent

## Request Envelope

One model request with deterministic time context.

| Field | Type | Constraint |
|---|---|---|
| `request` | string | Untrusted text; 1–4,000 characters after trimming |
| `reference_now` | string | ISO 8601 timestamp with explicit offset |
| `timezone` | string | Valid IANA name, or absent only when runtime configuration supplies a valid default |
| `existing_reminders` | array | Optional read-only context; each item has unique `id`, `title`, and `due_at` with explicit offset |

## Reminder Proposal

The exact object fields are `title` (1–200 character string), `due_at` (ISO 8601 with explicit UTC offset), and `timezone` (valid IANA identifier). The proposal is not persisted and creates no side effect.

## Agent Result

The top-level object has exactly `intent`, `status`, `reminder`, `target_reminder_id`, `missing_fields`, `clarification_question`, and `reason_code`. The allowed enums and status-to-field relationships are defined in [reminder-output.schema.json](contracts/reminder-output.schema.json) and `spec.md` FR-002–009. Full local validation also checks cross-field relationships and temporal semantics that the provider schema cannot express.

## Evaluation Case

Each case has a stable ID, one of six required categories, a complete request envelope, requirement trace, expected intent/status/target/reason/missing fields, optional exact time expectations, accepted task and clarification concepts, deterministic property expectations, and rubric criteria. Property names and scoring criteria are enumerated in the dataset schema and evaluator; expected behavior is machine-checkable rather than free-form prose. The fixed dataset has 18 cases and at least one case in every required category. Rubric weights sum to 1 per case; each named criterion returns a documented 0–1 score, the weighted sum is the case score, and the arithmetic mean is the dataset score. The harness does not mutate cases or the scoring threshold based on observed results.

## Case and Run Results

- **Case result**: case ID/category, raw structured output (only after credential redaction checks), structural result, named property results, rubric criterion scores, semantic score, failure category, and elapsed duration.
- **Run result**: provider, configured non-secret model identifier/settings, UTC start/end, dataset version/hash, per-case results, layer-level counts, mean semantic score, aggregate PASS/FAIL or incomplete infrastructure-failure status, and no credential material.

## Temporal rules

- Parse all reference, context, and proposal timestamps as aware datetimes.
- Interpret relative dates using the request's `reference_now` and IANA timezone, never the host clock.
- A ready proposal is strictly later than the reference instant.
- Duration snooze uses `max(reference_now, existing_due_at) + duration`.
- Invalid, missing, nonexistent, or repeated local times without a resolving offset require clarification; a past result is rejected.
