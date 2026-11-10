# Quickstart: Natural Language Reminder Agent

## Requirements and configuration

- Python 3.11 or later.
- Install with `python -m pip install -e ".[dev]"`.
- For the resource-compatible local path used on this PC, install Ollama, run `ollama pull qwen2.5:3b`, and configure `REMINDER_PROVIDER=ollama`, `REMINDER_MODEL=qwen2.5:3b`, and `OLLAMA_BASE_URL=http://127.0.0.1:11434` in the local process environment. The final recorded run `live-20261110T151355.668584Z` passed all 18 structural and property checks and scored 0.941667 against the fixed 0.85 threshold. Earlier lower scores and the interrupted 7B attempt are preserved in `evidence/harness-runs/`.
- The optional hosted path uses `REMINDER_PROVIDER=openai`, `OPENAI_API_KEY`, and an account-accessible `REMINDER_MODEL`. Never paste credentials into source files, logs, evidence, or chat.

## Offline development

Run `python .harness/run_offline.py` to capture compileall, Ruff, and unit/contract pytest results under `evidence/harness-runs/`. These tests inject a fake model client and do not claim to evaluate a real model.

## Live evaluation

From `Part-1B`, run `python .harness/run_live.py`. The wrapper runs `.harness/evaluate.py --mode live` against the fixed 18-case dataset and captures the command result and a result snapshot under `evidence/harness-runs/`. The evaluator applies structural validation, property/invariant validation, semantic scoring, aggregation, and failure classification. Each case records the raw model output separately from the application output after request guardrails. API/service/configuration failures are infrastructure failures and do not count as model-quality results.

The fixed threshold is 0.85. Do not edit the dataset, rubric, or threshold to make a failed result pass. Machine-generated evidence redacts credentials. Complete the blank narrative fields and final human acceptance decision in `evidence/harness-log.md` yourself.
