# Reminder Agent Clarification Record

**Feature**: `001-reminder-agent`
**Reviewed**: 2026-11-10

## Clarification outcome

The feature specification has no remaining blocking product ambiguity. The following decisions are explicit in `spec.md`:

- Each request includes a reference timestamp, timezone, and optional read-only reminder context so relative time and reschedule/snooze targets are testable.
- `Asia/Kolkata` is the configured default timezone for this assignment; evaluation cases provide a fixed timestamp and timezone.
- Missing task/date/time/zone/target data, ambiguous target selection, and unresolved daylight-saving times lead to clarification.
- A due time at or before the reference timestamp is rejected.
- A duration snooze starts from the later of the reference time and the existing due time.
- The output has one fixed JSON schema and no calendar, notification, or other external side effect.
- The semantic score uses explicit case rubrics, with a 0.85 threshold and structural/safety hard gates.

No user answer was required to settle these product behaviors. Provider credentials are deployment configuration; the model provider and non-secret model settings will be recorded in the technical plan and evaluation result.
# Clarification update — 2026-11-10

- **Question resolved from assignment scope**: How is a transparent semantic score made reproducible without relying on exact generated wording or a second judge model?
- **Decision**: Each case declares fixed weights that sum to 1 over named deterministic criteria. Each criterion returns a documented 0–1 score from normalized output fields and accepted concept terms. The case score is the weighted sum; the dataset score is the arithmetic mean across cases. Structural and safety invariants remain hard gates.
- **Reason**: The assignment permits rubric-based evaluation and requires an interpretable predeclared threshold. This resolves scoring mechanics before implementation and keeps equivalent wording acceptable.

# Provider deployment update — 2026-11-10

- **Constraint**: The user has no OpenAI API access. The captured OpenAI-backed live run therefore stopped before model inference and recorded all 18 cases as infrastructure-blocked.
- **Decision**: Keep the OpenAI adapter available, add a loopback-only Ollama adapter, and use real `qwen2.5:1.5b` and `qwen2.5:3b` model runs for local evaluation on this PC.
- **Follow-up decision after evaluation**: The genuine 18-case 1.5B run completed without infrastructure errors but scored 0.548611, with one structural and 13 property failures. Keep the result archived, and evaluate `qwen2.5:3b` as a provider-model capability repair. The dataset, expected properties, rubrics, safety gates, and 0.85 threshold are unchanged. This PC reported approximately 930 MB available memory before inference, so the 3B model may have a resource limitation; any such outcome must remain visible in the evidence.
- **Follow-up decision after the 3B run**: `qwen2.5:3b` improved the mean to 0.659722 and eliminated structural failures, but 11 property failures remain. A general prompt-injection filter and unsupported external-action policy now have offline regression coverage (51 tests pass), and both live results are archived. Evaluate `qwen2.5:7b` next; preserve any memory or quality failure and keep the benchmark unchanged.
- **Follow-up after the 7B resource attempt**: The 7B model attempt was interrupted before evaluation output because status calls stalled while it loaded on the CPU/memory-constrained PC. A structured attempt record has no score or decision. Use the installed 3B model for the next unchanged live run with the revised general decision instructions; keep the 7B attempt visible as a resource limitation.
- **Follow-up after the repeated 3B evaluation**: A verbose prompt revision regressed several straightforward cases. Preserve its failed result, restore concise rules, and add general local request guardrails for missing information, unique target selection, explicit action alignment, past-time rejection, and reference-based relative durations. Keep raw model outputs and guarded application outputs separately visible. The 18-case dataset, rubric, hard gates, and 0.85 threshold remain unchanged. Final run `live-20261110T151355.668584Z` passed 18/18 structural checks and 18/18 property checks, with a 0.941667 semantic mean and zero infrastructure failures.
- **Unchanged acceptance basis**: The approved output contract, 18 evaluation cases, rubrics, safety gates, and 0.85 threshold remain unchanged. Local model outputs will be recorded as actual model results, including any failures.
- **Rationale**: The assignment requires a genuine non-deterministic model run but does not prescribe a hosted provider. The local adapter avoids introducing a fabricated fixture or transmitting reminder requests to a remote service.
