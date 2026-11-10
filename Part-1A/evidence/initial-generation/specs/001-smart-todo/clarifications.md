# Smart Todo Clarification Record

**Feature**: `001-smart-todo`
**Reviewed**: 2026-11-10

## Clarification outcome

The feature specification has no remaining blocking ambiguity. The following defaults were resolved from the assignment scope and recorded in `spec.md` so the acceptance tests can be binary:

- One local user; command-line interaction only; no authentication, synchronization, or external service.
- Task fields, validation limits, priority order, and the permitted status-transition table are explicit.
- Multiple requested tags use AND matching; tag matching is case-insensitive and exact after trimming.
- Tied priorities preserve creation order; sequential IDs are persisted and never reused.
- Missing storage means an empty store. Invalid storage is reported without being overwritten.
- The default store stays beneath the working directory; a separate path can be supplied for isolated runs.

No user answer was required to settle these product behaviors. Technical stack decisions belong in `plan.md`.
