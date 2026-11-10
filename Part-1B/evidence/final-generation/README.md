# Part 1B — Natural Language Reminder Agent

This is the non-deterministic AI application for BITS Pilani Assignment 1. The approved behavioral boundary is the Spec Kit feature specification at [`specs/001-reminder-agent/spec.md`](specs/001-reminder-agent/spec.md). The agent returns a structured proposal only; it does not store reminders or call calendar, messaging, or notification services. It supports the optional OpenAI hosted adapter and a local Ollama adapter; this project run uses local Ollama. High-confidence local policy checks catch missing fields, ambiguous targets, intent mismatches, invalid relative-time arithmetic, and past due proposals before an output is returned.

## Setup

See [`specs/001-reminder-agent/quickstart.md`](specs/001-reminder-agent/quickstart.md). Install with `python -m pip install -e ".[dev]"`. For the resource-compatible local evaluation path used on this PC, install Ollama, pull `qwen2.5:3b`, and set `REMINDER_PROVIDER=ollama`, `REMINDER_MODEL=qwen2.5:3b`, and `OLLAMA_BASE_URL=http://127.0.0.1:11434` in the process environment. The hosted OpenAI option needs a private local API key. Never commit a populated `.env` or expose key values in logs.

## Validation

Offline contract and unit tests use an injected fake model client and do not count as live model evaluation. Run `python .harness/run_offline.py` to capture compileall, Ruff, and pytest results under `evidence/harness-runs/`. Earlier test-first and repair outputs are preserved under `evidence/development-cycles/`. Run `python .harness/run_live.py` for the fixed evaluation dataset and actual configured model. The wrapped evaluator executes structural, property/invariant, semantic/rubric, aggregation, and failure-reporting stages; results are written to `evidence/eval-results.json` and copied into the timestamped run folder without credentials. Each case retains both the raw model output and the guarded application output, including policy adjustments.

The dataset, rubric, and 0.85 threshold are fixed before evaluation. Preserve failures and repair root causes without changing cases or gates. The student completes narrative log entries and the final human acceptance decision in `evidence/harness-log.md`.

## Spec Kit artifacts

Constitution and generated skills are under `.specify/` and `.agents/skills/`; feature requirements, clarifications, plan, tasks, schemas, and research are under `specs/001-reminder-agent/`.
