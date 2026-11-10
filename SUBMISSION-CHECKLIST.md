# Assignment 1 submission checklist

## Prepared in this repository

- [x] Part 1A Smart Todo application, specification-derived tests, and independent four-gate harness.
- [x] Part 1A initial/final source snapshots, every captured harness run, and preserved test-first outputs.
- [x] Part 1B reminder agent, prompt, strict output contract, and 18-case versioned evaluation dataset.
- [x] Part 1B structural, property/invariant, semantic scoring, aggregation, and secret-safe result capture.
- [x] Part 1B general application guardrails for missing information, ambiguous targets, action alignment, relative-time arithmetic, and past-time rejection, covered by regression tests.
- [x] Part 1B initial/final source snapshots, offline/live validation evidence, and preserved test-first/repair outputs.
- [x] Both Spec Kit constitutions and reviewed feature artifacts, plans, tasks, contracts, checklists, and quickstarts.
- [x] Both blank-field harness-log templates, reserved for student-authored narrative and final human decisions.
- [x] Root and per-part READMEs with setup and validation commands.
- [x] Demo video runbook with safe commands and truthful result guidance.
- [x] Public GitHub repository created and the complete 692-file project published: https://github.com/neeraj9102/BITS-Pilani-Assignment-1

## Still needed before submission

- [ ] Personally review the captured PASS and its per-case raw model outputs, guarded application outputs, and policy adjustments before making the human ACCEPT/REJECT decision. Earlier failed model runs and the 7B resource attempt remain archived and visible.
- [ ] Review the genuine harness/evaluation evidence and complete each `evidence/harness-log.md` with personal narrative, limitations, and the student's ACCEPT/REJECT decision. Do not invent entries or claim acceptance for an incomplete run.
- [ ] Record a short demonstration video showing both applications after the configured Part 1B run is available, then upload it to an accessible Google Drive or OneDrive location.
- [ ] Complete the official student DOCX template with personal details, problem statements, the public GitHub link, the video link after recording, and the five independently written reflection answers.
- [ ] Write the five assessed reflection answers independently from the actual implementation and evidence; upload only the reflection document to the LMS as instructed.

## Validation captured so far

- Part 1A: latest harness run `20261110T151859.974943Z` passed compileall, Ruff, Bandit, and pytest. Earlier sandbox-temp, tool-setup, and lint failures remain preserved in `Part-1A/evidence/harness-runs/`.
- Part 1B offline: latest run `offline-20261110T151330.293440Z` passed compileall, Ruff, and 66 tests.
- Part 1B live: final run `live-20261110T151355.668584Z` used the unchanged 18-case dataset (SHA-256 `65343d2d7495a7e72ed52704a056eb46a13167bf8625ce1f6d7c20fef67d9b61`) and 0.85 threshold. It passed all 18 structural checks and all 18 property checks, with mean 0.941667 and zero infrastructure failures.
- Earlier Part 1B attempts remain as actual evidence: Qwen2.5 1.5B scored 0.548611 and failed; Qwen2.5 3B before the general application guardrails scored 0.659722, 0.595833, and 0.577778 and failed; Qwen2.5 7B was interrupted before a score due to resource pressure; OpenAI was `INCOMPLETE` because no API configuration was available.
- GitHub: the public `main` branch is live at https://github.com/neeraj9102/BITS-Pilani-Assignment-1. The published tree contains 692 tracked project files. The final upload commit is `ffad1d0256ecb7a3b9f820bb61ee49d029e1e38a`.
