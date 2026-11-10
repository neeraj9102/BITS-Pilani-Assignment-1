# CLI Contract: Smart Todo

## Invocation

Run with Python 3.11+: `python -m smart_todo [--data-file PATH] COMMAND`. The default store is `.data/tasks.json` beneath the current working directory. `--data-file` selects an isolated store path. No command performs network I/O.

## Commands

| Command | Arguments | Behavior |
|---|---|---|
| `add` | `TITLE [--description TEXT] [--priority low\|medium\|high] [--tag TAG ...]` | Create and print one task JSON object |
| `show` | `TASK_ID` | Print the matching task object |
| `list` | `[--tag TAG ...] [--sort priority]` | Print a JSON array; empty results are `[]`; default order is creation order |
| `update` | `TASK_ID [--title TEXT] [--description TEXT] [--priority VALUE] [--tag TAG ...] [--clear-tags]` | Replace only supplied fields and print the updated object; `--tag` replaces the complete tag list; `--clear-tags` replaces it with an empty list |
| `delete` | `TASK_ID` | Delete an existing task and print `{"deleted": "TASK_ID"}` |
| `status` | `TASK_ID STATUS` | Apply one allowed transition and print the updated object |

## Output and errors

- Successful commands write compact, valid JSON to stdout and exit `0`.
- Invalid input, unknown IDs, invalid transitions, and store errors write a concise human-readable error to stderr and exit non-zero; no rejected mutation changes the persisted store.
- `list` always returns an array, including `[]` for no matches.
- Optional scalar fields absent from an update retain their prior values. An explicitly supplied empty description is accepted; title and tag validation follow FR-003/FR-004.
- `--tag` and `--clear-tags` are mutually exclusive. Omitting both preserves existing tags.
- Duplicate tags after trimming and case-folding are rejected rather than silently merged.

## Persistent document

See [task-store.schema.json](task-store.schema.json) and [data-model.md](../data-model.md). The schema is versioned and closed to unknown fields. A missing file starts as an empty store; invalid existing JSON is not rewritten.
