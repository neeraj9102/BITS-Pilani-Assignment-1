# Agent CLI Contract

The command reads one JSON request envelope from standard input and writes one JSON result object to standard output:

```powershell
Get-Content request.json | python -m reminder_agent
```

The request envelope contains `request` (untrusted natural-language text), `reference_now` (ISO 8601 with explicit offset), optional `timezone` (valid IANA identifier; defaults to the configured `REMINDER_TIMEZONE`, which defaults to `Asia/Kolkata`), and optional `existing_reminders` (array of `{id,title,due_at}` read-only records). Unknown envelope fields, malformed JSON, empty input, and requests longer than 4,000 characters are rejected as `malformed_input`. A missing or invalid time zone produces a structured clarification.

On a valid application response, stdout contains exactly one compact JSON object matching [reminder-output.schema.json](reminder-output.schema.json). Malformed input JSON still produces the schema-compliant `malformed_input` rejection. A model/service or local output-validation error writes a safe diagnostic to stderr and exits non-zero; diagnostic text excludes request content, API keys, and response bodies.
