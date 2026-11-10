# Quickstart: Smart Todo

## Requirements

- Python 3.11 or later
- Install project and development tools from this directory: `python -m pip install -e ".[dev]"`

## Run

From `Part-1A`, create a task:

```powershell
python -m smart_todo add "Submit assignment" --priority high --tag school --tag urgent
python -m smart_todo list --tag school --sort priority
python -m smart_todo status T-000001 in_progress
```

Use `--data-file .data/check.json` before a subcommand to select an isolated store. The default store is `.data/tasks.json` under the current working directory.

## Validation

Run the independent harness with `python .harness/run_harness.py`. It executes compileall, Ruff, Bandit, and pytest gates in that order, records actual output under `evidence/harness-runs/`, continues through failures, and returns non-zero if any gate fails. The harness never rewrites its expectations from observed output.

Review the machine-generated run records. Complete the blank narrative fields and human acceptance decision in `evidence/harness-log.md` yourself.
