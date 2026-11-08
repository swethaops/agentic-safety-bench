# Multi-Framework Control Mapping

This document cross-references the controls implemented in agentic-safety-bench
across three frameworks commonly used in enterprise AI governance:

- **NIST AI 600-1** — Generative AI Profile of the AI Risk Management Framework
- **EU AI Act** — Regulation (EU) 2024/1689, Title III (High-Risk AI Systems)
- **ISO/IEC 42001:2023** — AI Management System standard

Use this table when preparing evidence for audits, vendor security questionnaires,
or regulatory submissions that reference any of these frameworks.

---

## Cross-reference table

| Control area | NIST AI 600-1 | EU AI Act | ISO 42001 | What the repo provides |
|---|---|---|---|---|
| Risk management documentation | GV-6.1 | Art. 9(1) — establish, implement, document and maintain a risk management system | 6.1 — actions to address risks and opportunities | `testbed/configs/hardened.yaml` encodes the risk control as machine-readable policy |
| Red-teaming / adversarial testing | MP-2.3 | Art. 9(5) — identify risks using state-of-the-art testing methods | 8.4 — AI system operation; 9.1 — monitoring | `ground_truth/tickets.json` + `ground_truth/exploits/` provide hand-verified adversarial inputs |
| Attack vector documentation | MP-5.2 | Art. 9(2)(b) — identify and analyse known and foreseeable risks | 6.1.2 — AI risk assessment | `ground_truth/flaws.md` documents P1–P4 with OWASP Agentic 2026 mapping |
| Measurement validity | MS-2.13-001 | Art. 9(7) — testing shall be appropriate to its intended purpose | 9.1 — monitoring, measurement, analysis and evaluation | Action log vs. scanner verdict comparison quantifies construct validity |
| Empirical validation | MS-2.3-002 | Art. 15(1) — robustness, accuracy and cybersecurity throughout lifecycle | 9.1 — performance evaluation | 20-run experiment per config with published raw logs |
| TEVV history | GV-1.5-003 | Art. 12 — record-keeping; Art. 18 — technical documentation | 7.5 — documented information; 10.2 — nonconformity and corrective action | `RUNS.md` — versioned per run with model, date, config, results, cost |
| Independence of evaluation | MS-1.3-003 | Art. 62 — post-market monitoring | 9.3 — management review | Vendor-neutral design; no affiliation with any evaluated scanner |
| Scope transparency | MS-2.5-001 | Art. 9(6) — testing on the basis of prior-defined metrics and probabilistic thresholds | 9.1 — documented scope | README Limitations section states: one model, one scenario, N runs |
| Control effectiveness evidence | MG-3.2 | Art. 9(5) — testing to identify the most appropriate risk management measures | 8.4 — operational planning and control | Hardened vs. vulnerable comparison shows harm rate delta under adversarial input |
| Incident response | MG-2.2 | Art. 9(4) — residual risk reduction; Art. 72 — serious incident reporting | 10.2 — nonconformity and corrective action | **Known gap** — not covered in this pilot |

---

## Notes for specific use cases

### SOC 2 Type II (AI-related trust service criteria)
The action log and RUNS.md together satisfy the **availability** and **processing integrity**
criteria for AI-assisted processes — specifically, evidence that the system behaves as
intended under adversarial conditions.

### Investor due diligence
Point investors to the results table in README.md plus the NIST control map above.
The key claim: tool-layer controls were empirically verified to reduce harm rate to zero
under adversarial input, not just described in a policy document.

### Enterprise customer security questionnaires
Most questionnaires ask: "How do you test your AI system for adversarial robustness?"
The answer, with evidence: `run_experiment.py` + `RUNS.md` + this document.
