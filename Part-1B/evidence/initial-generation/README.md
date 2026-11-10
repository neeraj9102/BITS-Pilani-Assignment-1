# Part 1B — Natural Language Reminder Agent

This is the non-deterministic AI application for BITS Pilani Assignment 1. The approved behavioral boundary is the Spec Kit feature specification at [`specs/001-reminder-agent/spec.md`](specs/001-reminder-agent/spec.md). The agent returns a structured proposal only; it does not store reminders or call calendar, messaging, or notification services.

## Setup

See [`specs/001-reminder-agent/quickstart.md`](specs/001-reminder-agent/quickstart.md). Install with `python -m pip install -e ".[dev]"`. Configure `OPENAI_API_KEY` and `REMINDER_MODEL` in the local process environment before live evaluation. `.env.example` contains names only. Never commit a populated `.env` or expose key values in logs.

## Validation

Offline contract and unit tests use an injected fake model client and do not count as live model evaluation. Run `python -m pytest` for those tests. Run `python .harness/evaluate.py --mode live` for the fixed evaluation dataset and actual configured model. This single runner executes structural, property/invariant, semantic/rubric, aggregation, and failure-reporting stages; results are written to `evidence/eval-results.json` without credentials.

The dataset, rubric, and 0.85 threshold are fixed before evaluation. Preserve failures and repair root causes without changing cases or gates. The student completes narrative log entries and the final human acceptance decision in `evidence/harness-log.md`.

## Spec Kit artifacts

Constitution and generated skills are under `.specify/` and `.agents/skills/`; feature requirements, clarifications, plan, tasks, schemas, and research are under `specs/001-reminder-agent/`.
