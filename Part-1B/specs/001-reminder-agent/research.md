# Research: Natural Language Reminder Agent

**Date**: 2026-11-10
**Feature**: `001-reminder-agent`

## Decisions

### Provider options: OpenAI Responses API and local Ollama

- **Decision**: Retain the official OpenAI Python SDK/Responses API adapter and add an Ollama native `/api/chat` adapter that uses the JSON Schema `format` field and only a loopback endpoint. Select the provider with `REMINDER_PROVIDER`.
- **Rationale**: The assignment requires real non-deterministic model behavior but does not prescribe a hosted provider. The user has no API access, so the local model route allows a genuine evaluation while keeping the accepted dataset and threshold intact. The OpenAI route remains available to users who configure an API account.
- **Credential/privacy boundary**: The OpenAI key is required only for `REMINDER_PROVIDER=openai`. The local route sends no authorization header and rejects non-loopback URLs. Neither route records credentials in `eval-results.json`.
- **Sources**: [OpenAI SDKs and CLI](https://developers.openai.com/api/docs/libraries), [Responses API reference](https://developers.openai.com/api/reference/python/resources/responses), [Ollama Windows documentation](https://github.com/ollama/ollama/blob/main/docs/windows.mdx), [Ollama API structured outputs](https://github.com/ollama/ollama/blob/main/docs/api.md).

### Local Qwen model for this evaluation

- **Decision**: Use `qwen2.5:3b` through Ollama for the next repeatable local live run, keeping temperature 0.2 and the existing structured output schema. A 7B attempt was interrupted before output because local queries stalled while the 4.7 GB model was loading.
- **Rationale**: The 3B model completes evaluation on this PC, although its last result failed the semantic threshold. Ollama reported about 930 MB available memory at server startup; the 7B attempt returned no case outputs or score. The next 3B run includes a general prompt decision procedure added from the observed failure pattern; cases, rubric, and threshold remain unchanged.
- **Sources**: [Ollama Qwen2.5 model page](https://ollama.com/library/qwen2.5), [Ollama Qwen2.5 3B model page](https://ollama.com/library/qwen2.5:3b), [Ollama Qwen2.5 7B model page](https://ollama.com/library/qwen2.5:7b).

### Strict Structured Outputs plus independent local validation

- **Decision**: Ask the model for the declared response contract through Responses API Structured Outputs. Validate the received result again with the complete local JSON Schema and deterministic cross-field/time invariants.
- **Rationale**: OpenAI recommends Structured Outputs over JSON mode when schema adherence is required. Strict Structured Outputs requires closed objects and supports a subset of JSON Schema; some conditional keywords are unavailable. Local validation remains necessary for the complete specification, especially intent/status relationships, future-time checks, target matching, and timezone behavior. Refusals and incomplete outputs must be detected.
- **Source**: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

### `jsonschema` for machine-checkable output contracts

- **Decision**: Use the `jsonschema` library with the contract's declared draft and explicit format/timezone validation.
- **Rationale**: The library supports multiple JSON Schema drafts and raises schema/instance errors. Its documentation notes that `format` is not enforced unless a format checker is supplied, so timestamp and timezone checks will be explicit rather than assuming `format: date-time` alone is sufficient.
- **Source**: [jsonschema validation documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/).

### Python `datetime`/`zoneinfo` with `tzdata`

- **Decision**: Parse timestamps as timezone-aware `datetime` values; resolve IANA names with `zoneinfo.ZoneInfo`; include the first-party `tzdata` package for platforms without a system IANA database.
- **Rationale**: The Python documentation identifies `zoneinfo` as IANA timezone support and recommends declaring `tzdata` for cross-platform projects because Windows may lack an IANA database. Deterministic evaluation cases provide `reference_now` and timezone; app logic never depends on the machine's current clock in a test.
- **Source**: [Python 3.12 `zoneinfo` documentation](https://docs.python.org/3.12/library/zoneinfo.html).

### Deterministic rubric instead of an LLM judge

- **Decision**: Score semantic meaning with per-case rubric fields and normalized structured values; do not add a second judge model.
- **Rationale**: The assignment permits heuristics, ground-truth comparison, semantic scoring, or rubrics. A transparent rubric is independently inspectable, avoids another model's variance and API cost, and tolerates equivalent wording by scoring required meaning rather than exact sentences.
- **Scoring**: Each case declares fixed criterion weights summing to 1. Deterministic criteria return 0-1 scores from normalized output values and accepted concept terms; the weighted sum is the case score and the dataset-wide score is the arithmetic mean. The 0.85 threshold is fixed in `spec.md`. Structural and property/invariant failures are reported separately and remain hard gates.

### Fake client for offline tests; live client for final evaluation

- **Decision**: Inject the model client so unit and contract tests can use fixed response fixtures without a key. Keep the evaluation runner's default mode live and use the actual configured model for final dataset evaluation.
- **Rationale**: Offline tests can verify prompt construction, exception classification, schema checks, invariants, metrics, and report writing without misrepresenting a fixture as a model evaluation. Live run output must identify service failures separately.

## Resolved Unknowns and External Requirement

- Feature scope, schema, ambiguity rules, and threshold are fixed in `spec.md`; no unresolved product requirement blocks planning.
- The user has no OpenAI API key. This run uses the real local Ollama provider; offline fixtures remain separate and are never included as live model outputs.
- The configured model name is recorded as non-secret evaluation metadata. No API key is required for local inference.

## Sources

- [GitHub Spec Kit Agentic SDD reference](https://github.github.com/spec-kit/reference/agentic-sdd.html)
- [OpenAI SDKs and CLI](https://developers.openai.com/api/docs/libraries)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Ollama Windows documentation](https://github.com/ollama/ollama/blob/main/docs/windows.mdx)
- [Ollama API structured outputs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Qwen2.5 3B model page](https://ollama.com/library/qwen2.5:3b)
- [jsonschema validation documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/)
- [Python 3.12 `zoneinfo`](https://docs.python.org/3.12/library/zoneinfo.html)
