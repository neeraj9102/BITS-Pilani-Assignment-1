# Smart Todo Constitution

## Core Principles

### I. Specification Before Implementation
The approved feature specification, clarifications, plan, and tasks are the source of truth. Each user-visible behavior and engineering constraint MUST be measurable and traceable to a specification requirement or task before production code is written.

### II. Deterministic Behavior
For the same command, input data, and persisted state, the application MUST produce the same result. Priority ordering, status transitions, filtering, error handling, and JSON serialization MUST have explicit rules and MUST NOT depend on network services or wall-clock timing.

### III. Independent Harness Controls
The harness MUST test the application from outside the production implementation. Lint, security, unit, and contract checks MUST be invoked by one runner with clear pass/fail status. Production code MUST NOT be able to edit test expectations or recorded harness results.

### IV. Safe Local Data Handling
All task data MUST be validated before mutation and persisted locally as UTF-8 JSON. Writes MUST avoid corrupting the last valid data file when a save fails. The application MUST NOT require credentials, transmit task data, or store secrets.

### V. Small CLI and Traceable Changes
The product MUST remain a small local task manager with documented commands and errors. Every implementation task MUST map to a reviewed requirement. The first generated implementation MUST be preserved before harness-driven repair, and the final implementation and genuine validation outputs MUST also be preserved.

## Engineering Constraints

- Part 1A implements task creation, reading/listing, updating, deletion, tag filtering, JSON persistence, priority sorting, and defined task-status transitions.
- Behavior at invalid inputs, duplicate identifiers, empty datasets, missing data files, and corrupted JSON MUST be specified and tested.
- A deterministic test MUST use controlled inputs and temporary data files. No test may depend on the real clock, network, or a user's personal files.
- The repository MUST exclude credentials, local `.env` files, and generated runtime data. Dependency versions and harness commands MUST be documented.

## Development Workflow

- Complete and review the Spec Kit constitution, specification, clarifications, plan, requirements checklist, tasks, and consistency analysis before implementation.
- Derive unit and contract tests from approved requirements. Keep harness code and expected results independent from production code.
- Run the same mandatory lint, security, and test gates after every repair. Preserve raw command outputs and machine-readable results; never change a recorded result by hand.
- Do not weaken the specification, remove a failing test, lower an assertion, disable a gate, or invent a failure to create evidence.
- Automated PASS requires a separate human ACCEPT/REJECT decision and a record of known limitations.

## Governance

This constitution governs Part 1A and takes precedence over implementation convenience. Amendments MUST be made through the applicable Spec Kit artifact, reviewed for impact on requirements and tests, and recorded in version history. A legitimate requirement change MUST update the specification and dependent plan, tasks, tests, and evidence. Each submitted result MUST disclose unresolved requirements and limitations. The student remains responsible for the final human acceptance decision.

**Version**: 1.0.0 | **Ratified**: 2026-11-10 | **Last Amended**: 2026-11-10
