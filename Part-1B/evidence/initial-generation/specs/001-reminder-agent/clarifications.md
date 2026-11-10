# Reminder Agent Clarification Record

**Feature**: `001-reminder-agent`
**Reviewed**: 2026-11-10

## Clarification outcome

The feature specification has no remaining blocking product ambiguity. The following decisions are explicit in `spec.md`:

- Each request includes a reference timestamp, timezone, and optional read-only reminder context so relative time and reschedule/snooze targets are testable.
- `Asia/Kolkata` is the configured default timezone for this assignment; evaluation cases provide a fixed timestamp and timezone.
- Missing task/date/time/zone/target data, ambiguous target selection, and unresolved daylight-saving times lead to clarification.
- A due time at or before the reference timestamp is rejected.
- A duration snooze starts from the later of the reference time and the existing due time.
- The output has one fixed JSON schema and no calendar, notification, or other external side effect.
- The semantic score uses explicit case rubrics, with a 0.85 threshold and structural/safety hard gates.

No user answer was required to settle these product behaviors. Provider credentials are deployment configuration; the model provider and non-secret model settings will be recorded in the technical plan and evaluation result.
# Clarification update — 2026-11-10

- **Question resolved from assignment scope**: How is a transparent semantic score made reproducible without relying on exact generated wording or a second judge model?
- **Decision**: Each case declares fixed weights that sum to 1 over named deterministic criteria. Each criterion returns a documented 0–1 score from normalized output fields and accepted concept terms. The case score is the weighted sum; the dataset score is the arithmetic mean across cases. Structural and safety invariants remain hard gates.
- **Reason**: The assignment permits rubric-based evaluation and requires an interpretable predeclared threshold. This resolves scoring mechanics before implementation and keeps equivalent wording acceptable.

