# Assignment 1 requirement analysis and execution plan

## Source authority and authorship boundary

The professor's Assignment 1 PDF defines the technical, evidence, marking, and submission requirements. The official student DOCX template defines the personal details, problem-statement, link, and reflection fields. The user's separate request authorizes technical implementation, requires accurate evidence, and reserves reflection answers for the student. Where an ordinary request conflicts with the course's explicit AI/authorship rules, the course rules govern submission content.

The PDF permits AI assistance for specification-driven development and harness development. It prohibits AI-generated reflection answers or harness-log entries and prohibits presenting AI-generated work as unaided student work. Therefore this repository keeps both narrative harness logs and the five reflection responses blank for the student. AI assistance must be disclosed accurately when the student submits.

## Marks and assessment criteria

| Component | Marks | Required evidence |
|---|---:|---|
| Part 1A: deterministic SDD and harnessing | 10 | Spec Kit artifacts and measurable criteria (3); implementation traceability (2); deterministic harness controls and tests (3); evidence, harness log, and final human review (2). |
| Part 1B: non-deterministic AI SDD and harnessing | 10 | Spec Kit artifacts and testable AI boundaries (2); schema, invariants, guardrails, and measurable criteria (2); at least 15 meaningful evaluation cases (2); one structural/property/semantic pipeline (2); evidence, harness log, and final human review (2). |
| Part 2: assessed reflection | 5 | Five evidence-based answers, one mark each, written by the student. |
| **Total** | **25** | Both applications and the reflection component are compulsory. |

## Requirements that apply to both applications

- Use the GitHub Spec Kit workflow practiced in Lab Sheet 1: problem statement, constitution, specify, clarify, plan, tasks, analyze where applicable, implement, harness, evidence-driven repair, unchanged revalidation, and human decision.
- Establish and review the specification and acceptance criteria before implementation. Record legitimate later clarifications in upstream artifacts and retain the history.
- Preserve the first implementation before harness-driven correction and preserve the final implementation after validation.
- Keep tests and evaluation checks traceable to approved requirements. Do not treat successful execution as proof of correctness.
- Preserve real harness outputs and failures, supply relevant failure evidence to the coding agent, repair root causes, and rerun the same controls.
- Do not weaken specifications, delete difficult cases, lower assertions or thresholds, disable checks, expose credentials, or edit recorded results to force PASS.
- Distinguish provider/service/configuration failures from application and model-quality failures. Disclose any residual limitation or failed requirement.
- A machine PASS does not replace the student's final human ACCEPT/REJECT decision.

## Part 1A: Smart Todo

### Required application scope

The selected sample is the deterministic Smart Todo task CLI. The scope must cover task CRUD, tag filtering, JSON persistence, priority sorting, and task-status transitions. The approved specification adds measurable constraints and binary acceptance criteria.

### Required harness controls and evidence

- Language-appropriate syntax/lint guard with an unambiguous result.
- Relevant security/SAST guard.
- Specification-derived unit and contract tests; mandatory deterministic tests pass before acceptance.
- Captured stdout/stderr and failed test/rule, expected behavior, and observed behavior.
- At least one genuine development failure/repair cycle if an actual failure occurs; never manufacture one for submission.
- Initial/final generations, Spec Kit artifacts, source, tests, harness runner/configuration, harness results, and `evidence/harness-log.md`.
- Student-authored log with the real test context, failures/repairs, rerun result, final decision, known limitations, and justification.

## Part 1B: Natural Language Reminder Agent

### Required application and specification boundaries

The selected application parses natural-language reminder requests, interprets date/time, supports create/reschedule/snooze, and asks for clarification when mandatory information is missing. Non-deterministic behavior must be testable through a stable output schema, structural invariants, behavioral properties, safety rules, a declared threshold, and a documented scoring calculation.

### Required evaluation dataset and pipeline

- `evals/dataset.json` must contain at least 15 meaningful cases, including normal/representative, boundary, ambiguous/underspecified, missing-information, malformed, and relevant adversarial/guardrail cases.
- Each case needs ground truth, deterministic expected properties, or a case-specific rubric sufficient to decide acceptability, with traceability to requirements.
- Use one pipeline: dataset → actual AI application/model call → schema validation → property/invariant checks → semantic/quality scoring → aggregate score/decision against the previously declared threshold.
- Structural and invariant checks remain independent even if a semantic judge is used.
- Preserve per-case and aggregate results, model/configuration details without secrets, and actual failures. Feed failures back to implementation/prompt/parser/guardrails and rerun without changing cases or thresholds merely to pass.
- Include initial/final generations, source, prompt if used, tests, dataset, harness, `evidence/eval-results.json`, and `evidence/harness-log.md`.
- Student-authored log must report configuration, threshold/scoring, layer results, real repair cycles, final human decision, limitations, and residual risks. Do not include credentials.

## Common repository and delivery requirements

- The GitHub repository must be public and contain the complete code for both parts, reviewed Spec Kit artifacts, runnable instructions, harnesses, datasets, and available evidence.
- Include a short demonstration video showing both applications; store it in Google Drive, OneDrive, or another accessible folder, with access available to BITS email IDs.
- Upload only the completed reflection report to the LMS. The reflection report must include the GitHub and video details.
- Submission deadline in the assignment PDF: November 15, 2026.
- Never commit API keys, credentials, or a populated local `.env` file.

## Official DOCX template fields

The student template asks for name, student ID, institutional email, public GitHub link, video link, a concise Part 1A problem statement, a Part 1B problem statement describing non-determinism/output/evaluation, and five assessed reflection responses. The five questions concern: (1) a Spec Kit decision and traceability, (2) a deterministic-harness finding, (3) non-exact evaluation criteria, (4) an actual feedback/repair cycle, and (5) human accountability and residual risk. Personal details, links, and reflection answers require the student's input.

## Execution plan and current status

1. Read the PDF and student template; translate their requirements into the per-part Spec Kit plans and this checklist. **Complete.**
2. Approve each specification/plan and establish acceptance criteria before production implementation. **Complete for both parts.**
3. Implement Part 1A and Part 1B, preserve initial generations, and build independent deterministic and non-deterministic harnesses. **Implemented.**
4. Capture actual test/evaluation failures and repairs, rerun unchanged controls, and preserve all outcomes. **Complete.** Part 1A, Part 1B offline, and the final 18-case Part 1B Ollama evaluation pass their captured gates. Earlier model failures, a resource-interrupted 7B attempt, and the OpenAI run that was incomplete without API configuration remain preserved.
5. Refresh final-generation snapshots/manifests only after the final validation run. **Complete.** Initial and final manifests were verified for both parts.
6. Have the student inspect every result, complete both harness-log narratives and final human decisions, write the five reflection responses, record the demo, complete the student template, and submit the reflection report. **Student actions pending.** The public repository is already published at https://github.com/neeraj9102/BITS-Pilani-Assignment-1; the video and reflection are not.

The status of the latest offline gates and each actual live model evaluation is maintained in [SUBMISSION-CHECKLIST.md](SUBMISSION-CHECKLIST.md). A failed live evaluation remains a failed evaluation; it is not reclassified as a pass because offline tests pass.
