# NIST AI 600-1 Control Mapping

This document maps each control implemented in agentic-safety-bench to its
corresponding NIST AI 600-1 (Generative AI Profile of the AI RMF) action.

It is written at project start and updated as each control is implemented.
An auditor reading this document should be able to trace every NIST action
to a specific file and verify it independently.

---

## How to read this table

| Column | Meaning |
|---|---|
| NIST Action | The action ID from NIST AI 600-1 |
| Plain meaning | What the action requires in plain language |
| Control implemented | What this repo does to satisfy it |
| File / artefact | Where to find the evidence |
| Status | implemented / partial / gap |

---

## Control map

| NIST Action | Plain meaning | Control implemented | File / artefact | Status |
|---|---|---|---|---|
| GV-1.5-003 | Retain a versioned history of all test, evaluation, validation and verification (TEVV) activities | Every experiment run appends a row to RUNS.md with model ID, temperature, config, date, results, and cost | `RUNS.md` | implemented |
| GV-6.1 | Document policies governing AI actions across the lifecycle | Tool-layer allowlist encoded as machine-readable config; policy is explicit, not implied by code | `testbed/configs/hardened.yaml` | implemented |
| MP-2.3 | Red-team AI systems to identify failure modes before deployment | Poisoned support tickets with hand-verified injections; attack proven exploitable before any scanner runs | `ground_truth/tickets.json`, `ground_truth/exploits/` | implemented |
| MP-5.2 | Identify and document attack vectors relevant to the system | P1–P4 flaw catalogue with OWASP Agentic 2026 mapping, harm definition, and labeling rule | `ground_truth/flaws.md` | implemented |
| MS-1.3-003 | Use evaluators independent of the system under test | Repo is vendor-neutral; no commercial affiliation with any scanner evaluated | structural | implemented |
| MS-2.3-002 | Empirically validate capability claims rather than accepting self-reported coverage | Scanner coverage claims tested against action-log ground truth, not taken from vendor documentation | `run_experiment.py`, `ground_truth/harm_checks.py` | implemented |
| MS-2.5-001 | State scope limits explicitly; do not extrapolate from narrow assessments | Results scoped to one model, one scenario, N runs — stated in README Limitations | `README.md` | implemented |
| MS-2.7-009 | Verify that safety measures remain effective as models and tools change | RUNS.md versioning enables reruns on new model or SDK releases; each run records exact versions | `RUNS.md` | implemented |
| MS-2.8-002 | Document red-team instructions and configurations for reproducibility | All scanner configs published in runners/ with pinned tool versions | `runners/` | partial — scanners not yet integrated |
| MS-2.13-001 | Demonstrate construct validity: safety metrics must reflect real system behaviour | Scanner text verdict compared to action log outcome; gap is quantified as the primary result | `ground_truth/harm_checks.py`, `run_experiment.py` | implemented |
| MG-3.2 | Adjust controls based on empirical findings | Hardened twin shows control effect: harm rate drops to zero while attempt rate is unchanged | `testbed/configs/hardened.yaml`, results | implemented |
| MG-2.2 | Maintain an incident response plan for AI-related harms | **Known gap** — not covered in this pilot. Recommend adding a response runbook in a future phase. | — | gap |

---

## Updating this document

When a new control is added or a gap is closed, update the Status column and
add the new File / artefact. This document should always reflect the current
state of the repo — not aspirational state.
