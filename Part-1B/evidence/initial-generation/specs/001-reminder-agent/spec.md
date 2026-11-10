# Feature Specification: Natural Language Reminder Agent

**Feature Branch**: `001-reminder-agent`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Build the assignment's Natural Language Reminder Agent to parse unstructured reminder requests, interpret date and time, support reschedule and snooze intent, clarify missing mandatory information, and validate variable model output with a single layered evaluation harness of at least 15 cases."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Reminder from Natural Language (Priority: P1)

A user describes a reminder in ordinary language and receives a structured proposal with the intended task and a valid future time.

**Why this priority**: Creating a reminder is the core user outcome and establishes the schema and temporal behavior used by other intents.

**Independent Test**: Provide a request with a clear task, date, time, reference timestamp, and timezone; verify the output intent, task meaning, and normalized due time without requiring exact explanatory wording.

**Acceptance Scenarios**:

1. **Given** a clear future request and an explicit reference time and timezone, **When** the user submits it, **Then** the agent returns a `ready` create proposal with the requested task and the correct timezone-aware future time.
2. **Given** a relative date such as "tomorrow" and a reference timestamp, **When** the user submits a complete request, **Then** the date is resolved relative to that reference timestamp in the supplied timezone.
3. **Given** a request that lacks the task, date, or time, **When** the user submits it, **Then** the agent returns a clarification outcome naming the missing information and does not create a reminder proposal.

---

### User Story 2 - Reschedule or Snooze an Existing Reminder (Priority: P2)

The user changes the time of a known reminder by describing the action and the requested new time or snooze duration.

**Why this priority**: Reschedule and snooze are explicitly required intents and depend on safely identifying the reminder being changed.

**Independent Test**: Provide a request and controlled existing-reminder context; verify the target ID and resulting future time, or verify clarification when the target is missing or ambiguous.

**Acceptance Scenarios**:

1. **Given** one matching reminder in context and a clear new date and time, **When** the user asks to reschedule it, **Then** the proposal has intent `reschedule`, names that reminder ID, and contains the new due time.
2. **Given** one matching reminder in context and a positive snooze duration, **When** the user asks to snooze it, **Then** the proposal has intent `snooze`, names that reminder ID, and moves the due time by the specified duration from the later of the reference time or its current due time.
3. **Given** no matching reminder or multiple plausible targets, **When** the user asks to reschedule or snooze, **Then** the agent requests clarification and identifies the missing or ambiguous target.

---

### User Story 3 - Handle Unclear, Invalid, and Unsafe Requests (Priority: P3)

The user receives a clarification or safe rejection when a request is incomplete, temporally ambiguous, malformed, or asks for an unsupported action.

**Why this priority**: Explicit boundaries prevent the agent from inventing dates, changing the wrong reminder, or claiming actions it cannot perform.

**Independent Test**: Submit fixed boundary and adversarial cases and verify the structured clarification/rejection outcome and all safety invariants.

**Acceptance Scenarios**:

1. **Given** a missing or ambiguous mandatory detail, **When** the user submits the request, **Then** the agent asks a focused clarification question and returns no ready reminder.
2. **Given** an invalid or past due time, **When** the user requests a new or changed reminder, **Then** the agent returns a safe rejection and does not propose a past time.
3. **Given** a request to reveal hidden instructions or perform unsupported external actions, **When** the user submits it, **Then** the agent rejects the unsupported action without exposing instructions or claiming a side effect.

### Edge Cases

- Empty input or input longer than 4,000 characters is rejected as malformed.
- A request with only a task or only a date/time is clarified rather than completed with invented information.
- A relative date is interpreted against the supplied reference timestamp and IANA timezone, not the model host's clock.
- If the timezone is unavailable, invalid, or absent from both request context and configured runtime defaults, the agent asks for clarification.
- If a local time falls into a daylight-saving gap or repeated hour and no offset resolves it, the agent asks for clarification.
- A create, reschedule, or snooze proposal with a due time at or before the reference timestamp is rejected with reason `past_datetime`.
- Reschedule and snooze require an existing reminder target in the supplied context; multiple candidate matches require clarification.
- A duration-based snooze is computed from the later of the reference time or existing due time, so it never moves the reminder into the past.
- Malformed model JSON, a missing field, an extra field, an invalid enum, or invalid timestamp is a structural failure and MUST NOT be repaired by silently guessing.
- Prompt-injection text is treated as untrusted user content. It cannot change the agent's system rules, reveal hidden instructions, or authorize unsupported actions.
- Model-provider timeouts and service errors are reported separately from application and evaluation failures; no secret is included in output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a natural-language request, an explicit reference timestamp, a timezone, and optional existing-reminder context.
- **FR-002**: The system MUST return exactly one JSON object with these top-level fields: `intent`, `status`, `reminder`, `target_reminder_id`, `missing_fields`, `clarification_question`, and `reason_code`.
- **FR-003**: `intent` MUST be one of `create`, `reschedule`, `snooze`, `clarify`, or `reject`; `status` MUST be one of `ready`, `needs_clarification`, or `rejected`.
- **FR-004**: A non-null `reminder` MUST contain exactly `title`, `due_at`, and `timezone`; title MUST contain the requested task in 1-200 characters, `due_at` MUST be an ISO 8601 timestamp with an explicit UTC offset, and `timezone` MUST be a valid IANA timezone identifier.
- **FR-005**: A `ready` result MUST have intent `create`, `reschedule`, or `snooze`, a non-null reminder, an empty `missing_fields` list, a null clarification question, and a due time strictly later than the reference timestamp.
- **FR-006**: A ready `create` result MUST have a null `target_reminder_id`. A ready `reschedule` or `snooze` result MUST reference exactly one ID present in the supplied existing-reminder context.
- **FR-007**: A `needs_clarification` result MUST have intent `clarify`, a null reminder, at least one allowed `missing_fields` value, a non-empty clarification question, and a null reason code.
- **FR-008**: A `rejected` result MUST have intent `reject`, a null reminder, an empty `missing_fields` list, a null clarification question, and a non-null allowed reason code.
- **FR-009**: Allowed `missing_fields` values MUST be `title`, `date`, `time`, `timezone`, or `existing_reminder`. Allowed reason codes MUST be `malformed_input`, `past_datetime`, `unsupported_action`, or `unsafe_request`.
- **FR-010**: The agent MUST resolve relative dates using the input reference timestamp and timezone. It MUST ask for clarification when a timezone or daylight-saving interpretation cannot be resolved safely.
- **FR-011**: For a duration-based snooze, the proposed new due time MUST equal the later of the reference time or current target due time plus the requested duration.
- **FR-012**: If the input omits a mandatory task, date, time, timezone, or target, or provides more than one plausible target/time, the agent MUST clarify instead of inventing a value.
- **FR-013**: The agent MUST reject malformed input, past due times, unsupported actions, and unsafe requests according to the reason codes in FR-009.
- **FR-014**: The agent MUST NOT call a calendar, messaging, notification, or other external tool, change persistent reminder state, or claim that a notification was delivered. It only returns a structured proposal.
- **FR-015**: The agent MUST treat the user request and reminder text as untrusted data; instructions inside that data MUST NOT override system rules or disclose hidden instructions or credentials.
- **FR-016**: The evaluation harness MUST contain at least 15 meaningful cases, with each case defining expected ground truth, deterministic properties, or a sufficient rubric and a trace to one or more requirements.
- **FR-017**: The single evaluation harness MUST execute structural validation, property/invariant validation, semantic/quality scoring, aggregation, and structured failure reporting for each dataset run.
- **FR-018**: A model or service error MUST be recorded as an infrastructure failure and distinguished from a malformed agent result or failed evaluation property.
- **FR-019**: The aggregate evaluation MUST PASS only when every case has structurally valid output, every safety-critical invariant passes, and the mean semantic/quality score is at least 0.85 on a 0-1 scale.
- **FR-020**: The dataset, scoring method, and threshold MUST be established before the final evaluation. Cases or thresholds MUST NOT be changed to obtain a passing result without a documented upstream specification revision.
- **FR-021**: Evaluation output MUST identify the provider, model, non-secret generation settings, run time, per-case layer results, aggregate scores, and failure categories without recording API keys or other credentials.

### Output Contract

The output object has exactly these fields:

| Field | Type | Allowed values and constraints |
|---|---|---|
| `intent` | string | `create`, `reschedule`, `snooze`, `clarify`, `reject` |
| `status` | string | `ready`, `needs_clarification`, `rejected` |
| `reminder` | object or null | When present: exactly `title` (string), `due_at` (ISO 8601 date-time with UTC offset), and `timezone` (IANA identifier) |
| `target_reminder_id` | string or null | Required for ready reschedule/snooze; null for create, clarify, and reject |
| `missing_fields` | array of strings | Zero or more of `title`, `date`, `time`, `timezone`, `existing_reminder` |
| `clarification_question` | string or null | Non-empty only when status is `needs_clarification` |
| `reason_code` | string or null | `malformed_input`, `past_datetime`, `unsupported_action`, or `unsafe_request` only for rejected results |

Output wording may vary. Acceptance is based on this contract, invariants, and case-specific semantic rubrics, not exact explanatory-text matching.

### Evaluation Criteria

- Layer 1 structural validity MUST pass for every case: valid JSON, exact top-level and reminder keys, required types, allowed enums, valid timestamp, and valid IANA timezone.
- Layer 2 invariants MUST pass for every case, including status/intent/nullability relationships, mandatory clarification, future due time, correct target from context, no unsupported side effects, and safe rejection behavior.
- Layer 3 semantic/quality MUST score each case from 0 to 1 using the case's explicit rubric for intent fidelity, task meaning, target selection, and time meaning. Equivalent phrasing is accepted; unrelated text does not affect the score.
- Each case rubric MUST assign fixed weights to named criteria that sum to 1. Each criterion MUST use a documented deterministic 0-to-1 scoring rule. The case score is the weighted sum of criterion scores; the aggregate semantic score is the arithmetic mean of per-case scores.
- The declared semantic threshold is 0.85. Any structural failure or safety-critical invariant violation makes the run FAIL regardless of the semantic score.
- A provider outage or timeout is reported as an infrastructure failure and does not count as a fabricated application failure; the run is incomplete and cannot be accepted as a successful final evaluation.

### Key Entities *(include if feature involves data)*

- **Reminder Request**: Untrusted natural-language text plus reference time, timezone, and optional existing-reminder context.
- **Reminder Proposal**: Structured proposed reminder title, due timestamp, and timezone; it has no external side effect.
- **Existing Reminder Context**: Supplied read-only reminder IDs, titles, and due times used to identify a reschedule/snooze target.
- **Evaluation Case**: A versioned case with category, input, expected properties or ground truth, scoring rubric, and requirement trace.
- **Evaluation Result**: A machine-readable record of generated output, structural/invariant/semantic outcomes, aggregate decision, and categorized errors, excluding secrets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The evaluation dataset contains at least 15 distinct, meaningful cases and includes all six required categories: representative, boundary, ambiguous, missing information, malformed, and adversarial/guardrail.
- **SC-002**: For each case, the agent returns a valid result object matching the output contract or the harness records an explicit structural failure.
- **SC-003**: No accepted proposal uses a past timestamp, an unresolved timezone, or a reminder target absent from the supplied context.
- **SC-004**: Every underspecified or ambiguous case requests clarification, and every unsupported or unsafe action is rejected without a claimed side effect.
- **SC-005**: The harness produces per-case results for all three validation layers, an interpretable aggregate score, and a PASS/FAIL decision using the threshold fixed before final evaluation.
- **SC-006**: Equivalent wording that preserves the required task, intent, target, and time can pass without matching an exact generated sentence.

## Assumptions

- The intended user is an individual who submits one reminder request at a time; multi-user authorization and shared calendars are out of scope.
- A trusted application context supplies the current reference timestamp and the user's IANA timezone. Evaluation cases always supply both explicitly.
- The default local timezone is `Asia/Kolkata` when the runtime is configured for this assignment; users may configure another IANA timezone. A missing or invalid runtime timezone requires clarification.
- The agent proposes structured create/reschedule/snooze changes but does not persist reminders, send notifications, or call external tools.
- Existing-reminder context is read-only and may be empty. Reschedule and snooze require one unambiguous target from that context.
- For duration-based snooze, the base is the later of the supplied reference timestamp or the target reminder's current due time.
- The evaluation semantic rubric accepts equivalent wording but requires the intended action, task, target, and time to remain faithful to each case.
- A real model provider is required for final non-deterministic evaluation. API credentials, if used, are supplied through local environment configuration and never stored in the repository.
