# Data Model: Smart Todo Task Management

## Task

One independently manageable unit of work.

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `id` | string | yes | Unique, sequential `T-000001` format; never reused after deletion |
| `title` | string | yes | Trimmed, 1–200 characters |
| `description` | string | yes | Empty string when omitted; maximum 2,000 characters |
| `priority` | string | yes | `low`, `medium`, or `high`; defaults to `medium` |
| `tags` | array of strings | yes | Empty when omitted; each trimmed, non-empty, at most 32 characters, unique case-insensitively |
| `status` | string | yes | `todo`, `in_progress`, `done`, or `cancelled`; defaults to `todo` |
| `creation_order` | integer | yes | Non-negative and immutable; ascending order preserves insertion order |

## Task Store

The UTF-8 JSON document is the single durable source of truth.

| Field | Type | Constraint |
|---|---|---|
| `schema_version` | integer | Currently `1` |
| `next_id` | integer | Positive next sequential task number; advances only on successful creation |
| `next_creation_order` | integer | Non-negative next order value; advances only on successful creation |
| `tasks` | array of Task | IDs unique; order values unique and less than `next_creation_order` |

The absent-file state is equivalent to an empty store with both counters at `1`/`0`. Existing malformed or structurally invalid content is an error and must remain byte-for-byte untouched by rejected mutations. Mutations serialize a complete validated document to a sibling temporary file and atomically replace the target only after the write succeeds.

## Status lifecycle

| Current | Allowed next values |
|---|---|
| `todo` | `in_progress`, `cancelled` |
| `in_progress` | `todo`, `done`, `cancelled` |
| `done` | `in_progress` |
| `cancelled` | `todo` |

## Ordering and matching

- Default list order is ascending `creation_order`.
- Priority order is `high`, `medium`, `low`, then ascending `creation_order` within a priority.
- Tag matching trims and case-folds both the stored and requested values; multiple requested tags use AND semantics.
