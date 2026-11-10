# Feature Specification: Smart Todo Task Management

**Feature Branch**: `001-smart-todo`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Build the assignment's Smart Todo task CLI with CRUD, tag filtering, JSON persistence, priority sorting, task-status transitions, and an independent deterministic harness."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Tasks (Priority: P1)

A single local user creates, views, edits, and deletes tasks so their current work is captured and kept accurate.

**Why this priority**: Task CRUD is the core value and the foundation for filtering, sorting, and status management.

**Independent Test**: Start with an empty task store, perform each CRUD action, restart the program, and verify the requested fields and resulting task set.

**Acceptance Scenarios**:

1. **Given** an empty task store, **When** the user creates a task with a valid title, **Then** the task appears with a unique ID, default priority `medium`, default status `todo`, and the supplied optional fields.
2. **Given** an existing task, **When** the user requests it by ID, **Then** the displayed task matches every persisted field.
3. **Given** an existing task, **When** the user updates one or more fields, **Then** only those fields change and all other fields remain unchanged.
4. **Given** an existing task, **When** the user deletes it by ID, **Then** it no longer appears in listing or filtering.
5. **Given** an unknown task ID, **When** the user requests, updates, deletes, or transitions that task, **Then** the operation reports a not-found error and the store remains unchanged.

---

### User Story 2 - Find and Prioritize Work (Priority: P2)

The user filters tasks by tags and reviews tasks in a predictable priority order.

**Why this priority**: Filtering and ordering make a growing task list useful without adding a complex interface.

**Independent Test**: Seed tasks with mixed tags and priorities, request filtered and unfiltered lists, and compare membership and order with fixed expected results.

**Acceptance Scenarios**:

1. **Given** tasks with varied tags, **When** the user filters by one tag, **Then** only tasks containing that tag are returned, ignoring case differences.
2. **Given** tasks with varied tags, **When** the user supplies multiple tags, **Then** only tasks containing every requested tag are returned.
3. **Given** tasks with high, medium, and low priority, **When** the user lists tasks in priority order, **Then** high tasks appear first, then medium, then low, with equal-priority tasks kept in creation order.
4. **Given** no task matches a filter, **When** the user lists the filtered result, **Then** the program reports an empty result without changing stored tasks.

---

### User Story 3 - Track Task Status (Priority: P3)

The user moves a task through its allowed lifecycle and receives a clear result when a requested transition is invalid.

**Why this priority**: Status transitions distinguish active work from completed or cancelled work while keeping the workflow small and testable.

**Independent Test**: Exercise every allowed and disallowed transition from each lifecycle state and verify the final state after each attempt.

**Acceptance Scenarios**:

1. **Given** a task in `todo`, **When** the user moves it to `in_progress` or `cancelled`, **Then** the task reaches the requested state.
2. **Given** a task in `in_progress`, **When** the user moves it to `todo`, `done`, or `cancelled`, **Then** the task reaches the requested state.
3. **Given** a task in `done`, **When** the user reopens it to `in_progress`, **Then** the task reaches `in_progress`.
4. **Given** a task in `cancelled`, **When** the user restores it to `todo`, **Then** the task reaches `todo`.
5. **Given** any task state, **When** the requested transition is not in the allowed transition set, **Then** the program reports an invalid transition and leaves the task unchanged.

### Edge Cases

- A title that is empty after trimming or exceeds 200 characters is rejected without writing a task.
- An optional description may be omitted or empty and is limited to 2,000 characters.
- Tags are trimmed, non-empty, limited to 32 characters, and unique case-insensitively within one task.
- Priority accepts only `low`, `medium`, or `high`; status accepts only the states and transitions defined above.
- Creating a task when no data file exists creates a valid empty store before adding the task.
- Invalid or truncated JSON is reported as a data-store error; the original file is not overwritten.
- A failed write leaves the last valid store readable and does not report a successful mutation.
- An empty task store and an empty filter result are valid states.
- A task ID counter is not decremented or reused after deletion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a local command-line interface for task creation, reading, listing, updating, deletion, tag filtering, priority sorting, and status transition.
- **FR-002**: A task MUST contain a unique ID, a required title, optional description, priority, zero or more tags, status, and creation order.
- **FR-003**: The system MUST trim task titles and reject titles that are empty or longer than 200 characters.
- **FR-004**: The system MUST limit descriptions to 2,000 characters and each tag to 32 non-empty characters after trimming.
- **FR-005**: The system MUST accept only priorities `low`, `medium`, and `high`, defaulting a new task to `medium` when priority is omitted.
- **FR-006**: The system MUST accept only statuses `todo`, `in_progress`, `done`, and `cancelled`, defaulting new tasks to `todo`.
- **FR-007**: The system MUST use the following status transitions: `todo` to `in_progress` or `cancelled`; `in_progress` to `todo`, `done`, or `cancelled`; `done` to `in_progress`; and `cancelled` to `todo`. Any other transition MUST fail without mutation.
- **FR-008**: The system MUST assign IDs sequentially as `T-000001`, `T-000002`, and so on, based on a persisted counter. IDs MUST NOT be reused after deletion.
- **FR-009**: When listing in priority order, the system MUST order priorities as high, medium, low, then preserve creation order within each priority.
- **FR-010**: Tag matching MUST be case-insensitive and exact after trimming. When multiple tags are supplied, a task MUST contain all requested tags to match.
- **FR-011**: The system MUST persist tasks and the next ID counter in a local UTF-8 JSON file. A successful mutation MUST survive process restart with every task field and list order preserved.
- **FR-012**: A missing data file MUST be treated as an empty store. Malformed or structurally invalid JSON MUST produce a clear error without replacing or partially rewriting the invalid file.
- **FR-013**: A missing task ID, invalid field, invalid tag, or invalid transition MUST produce a non-success result and MUST leave all previously stored tasks unchanged.
- **FR-014**: A filtered list MUST return exactly the matching tasks; an empty match set MUST be represented as an empty result.
- **FR-015**: The user MUST be able to choose a data-file path for isolated use and testing. The default path MUST stay inside the application's working directory and MUST NOT inspect unrelated personal files.
- **FR-016**: The application MUST NOT make network requests or require credentials.

### Key Entities *(include if feature involves data)*

- **Task**: A unit of work with a stable ID, title, optional description, priority, tags, status, and immutable creation order.
- **Task Store**: The collection of tasks and next sequential ID value persisted as one JSON document.
- **Status Transition**: A requested change from one task status to another, accepted only when allowed by FR-007.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can create, retrieve, update, and delete 100 distinct tasks; every requested field is preserved or changed exactly as specified.
- **SC-002**: After closing and reopening the application, all 100 stored tasks retain their IDs, fields, and creation order.
- **SC-003**: For every fixed tag-filter fixture, the result contains all and only tasks matching every supplied tag, regardless of case.
- **SC-004**: For every fixed priority fixture, all high-priority tasks precede medium, all medium precede low, and ties preserve creation order.
- **SC-005**: Every transition in FR-007 succeeds, every other transition fails, and each rejected transition leaves the prior state unchanged.
- **SC-006**: Invalid task fields and malformed storage produce an observable error and never report a successful mutation.

## Assumptions

- The intended user is one person managing tasks locally; authentication, multi-user access, synchronization, and a graphical interface are out of scope.
- A task has one primary title, an optional description, a single priority, multiple tags, and one status.
- Tag filters use AND semantics when more than one tag is supplied.
- Equal-priority tasks retain their original creation order.
- The default data file is kept under the current working directory; callers may supply a different path for an isolated project or test.
- The assignment requires independent harness checks; the harness is maintained separately from production modules and does not modify expected values at runtime.
