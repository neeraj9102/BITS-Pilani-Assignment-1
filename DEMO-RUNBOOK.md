# Demonstration video runbook

Use this as a recording outline; record your own screen and narrate what actually happens. Keep secrets and environment-variable values off screen. Do not describe an `INCOMPLETE` live evaluation as a model pass.

## 1. Smart Todo

From `Part-1A`, run:

```powershell
python -m smart_todo --data-file .data/demo-tasks.json add "Submit assignment" --priority high --tag school
python -m smart_todo --data-file .data/demo-tasks.json list --tag school --sort priority
python -m smart_todo --data-file .data/demo-tasks.json status T-000001 in_progress
python .harness/run_harness.py
```

Show the JSON responses and the four recorded gates. If the task file already contains data, use a new empty demo filename so the displayed ID is predictable.

## 2. Natural Language Reminder Agent

Before recording, install/start Ollama, pull `qwen2.5:3b`, and set `REMINDER_PROVIDER=ollama`, `REMINDER_MODEL=qwen2.5:3b`, and `OLLAMA_BASE_URL=http://127.0.0.1:11434` in the local process environment. No API key is needed for this local path. From `Part-1B`, submit a natural-language reminder through stdin:

```powershell
@'
{"request":"Remind me to submit the assignment tomorrow at 9 AM.","reference_now":"2026-11-10T10:00:00+05:30","timezone":"Asia/Kolkata","existing_reminders":[]}
'@ | python -m reminder_agent
```

Then run `python .harness/run_offline.py` and `python .harness/run_live.py`. Show the agent's structured response, raw model response, any policy adjustments, and the evaluation summary/result file. Explain the three evaluation layers and the fixed 0.85 threshold using the actual saved results; the final recorded local run passed at 0.941667, while earlier failed runs remain preserved.

## 3. Close

Show the repository README and submission checklist. State any incomplete evaluation, known limitation, or pending human decision plainly. Do not record an API key, private response headers, or a fabricated result.
