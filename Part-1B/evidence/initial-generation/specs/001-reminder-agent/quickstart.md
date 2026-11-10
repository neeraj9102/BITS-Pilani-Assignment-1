# Quickstart: Natural Language Reminder Agent

## Requirements and configuration

- Python 3.11 or later with HTTPS access for live evaluation.
- Install with `python -m pip install -e ".[dev]"`.
- Set `OPENAI_API_KEY` in the local process environment and `REMINDER_MODEL` to a model available to the account. Never paste credentials into source files, logs, evidence, or chat.

## Offline development

Run unit and contract tests with `python -m pytest`. These tests inject a fake model client and do not claim to evaluate a real model.

## Live evaluation

From `Part-1B`, run `python .harness/evaluate.py --mode live`. The runner evaluates the fixed 18-case dataset through structural validation, property/invariant validation, semantic scoring, aggregation, and failure classification. It records actual outputs under `evidence/`; API/service failures are infrastructure failures and do not count as model passes.

The fixed threshold is 0.85. Do not edit the dataset, rubric, or threshold to make a failed result pass. The machine-generated evidence excludes credentials. Complete the blank narrative fields and final human acceptance decision in `evidence/harness-log.md` yourself.
