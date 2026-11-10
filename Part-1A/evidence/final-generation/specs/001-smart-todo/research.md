# Research: Smart Todo Task Management

**Date**: 2026-11-10
**Feature**: `001-smart-todo`

## Decisions

### Python 3.11+ and standard-library runtime

- **Decision**: Implement the application as a Python CLI. Keep production dependencies in the standard library.
- **Rationale**: The task scope is local JSON CRUD and deterministic rules. `argparse`, `json`, `pathlib`, and `tempfile` cover these needs without a service framework or network dependency. Python 3.12.14 is available in the execution environment; Python 3.11+ is the portable project minimum.
- **Alternatives considered**: A web service or GUI would add interfaces the assignment does not reward and would expand the security and test surface. A database would replace the required JSON persistence.

### pytest for isolated functional and contract tests

- **Decision**: Use pytest to run unit tests and black-box CLI tests, with temporary stores for each test.
- **Rationale**: The official pytest documentation covers test discovery, assertions, exception checks, and temporary-path fixtures suitable for isolated file-backed tests.
- **Source**: [pytest documentation](https://docs.pytest.org/en/stable/getting-started.html).

### Ruff for linting and Bandit for SAST

- **Decision**: Use Ruff's `check` command for lint and Bandit's recursive scan for production source. Run both through the harness and preserve their real return codes and output.
- **Rationale**: The assignment explicitly requires language-appropriate lint and static security gates. Ruff documents `ruff check`; Bandit documents recursive AST-based scanning and machine-readable reports.
- **Sources**: [Ruff installation and CLI](https://docs.astral.sh/ruff/installation/), [Bandit command-line reference](https://bandit.readthedocs.io/en/latest/man/bandit.html).

### Atomic JSON persistence

- **Decision**: Validate the full store before mutation, serialize to a temporary sibling file, flush it, then replace the data file atomically. Never rewrite malformed input.
- **Rationale**: A failed write must not destroy the last valid store. A sibling temp file keeps replacement on the same filesystem and permits an atomic rename on supported local filesystems.
- **Alternatives considered**: Writing in place is shorter but can truncate the only store if interrupted. SQLite is out of scope because JSON persistence is explicit.

### Black-box harness boundary

- **Decision**: Invoke the CLI in subprocesses using per-run temporary data files. Keep tests and harness code outside `src/`.
- **Rationale**: Contract checks observe the actual user interface and persistence behavior without relying only on production helper functions. The runner can capture stdout, stderr, and exit codes from each gate.
- **Alternative considered**: Only unit-testing internal functions would make it easier for tests to share implementation assumptions and miss CLI/storage integration errors.

## Resolved Unknowns

- The runtime must work without network or credentials.
- The task limits and enums are fully specified in `spec.md`; no unresolved technical choice blocks implementation.
- The default path is `.data/tasks.json` under the working directory. The path is injectable to isolate tests and user runs.

## Sources

- [GitHub Spec Kit Agentic SDD reference](https://github.github.com/spec-kit/reference/agentic-sdd.html)
- [pytest documentation](https://docs.pytest.org/en/stable/getting-started.html)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [Bandit documentation](https://bandit.readthedocs.io/en/latest/)
