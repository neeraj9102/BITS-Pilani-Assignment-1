# Quickstart: Natural Language Reminder Agent

## Requirements and configuration

- Python 3.11 or later with HTTPS access for live evaluation.
- Install with `python -m pip install -e ".[dev]"`.
- Set `OPENAI_API_KEY` in the local process environment and `REMINDER_MODEL` to a model available to the account. Never paste credentials into source files, logs, evidence, or chat.

## Offline development

Run `python .harness/run_offline.py` to capture compileall, Ruff, and unit/contract pytest results under `evidence/harness-runs/`. These tests inject a fake model client and do not claim to evaluate a real model.

## Live evaluation

From `Part-1B`, run `python .harness/run_live.py`. The wrapper runs `.harness/evaluate.py --mode live` against the fixed 18-case dataset and captures the command result under `evidence/harness-runs/`. The evaluator applies structural validation, property/invariant validation, semantic scoring, aggregation, and failure classification; per-case results are written to `evidence/eval-results.json`. API/service/configuration failures are infrastructure failures and do not count as model-quality results.

The fixed threshold is 0.85. Do not edit the dataset, rubric, or threshold to make a failed result pass. Machine-generated evidence redacts credentials. Complete the blank narrative fields and final human acceptance decision in `evidence/harness-log.md` yourself.
