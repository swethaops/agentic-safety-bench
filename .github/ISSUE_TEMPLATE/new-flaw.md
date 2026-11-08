---
name: New planted flaw
about: Propose a new vulnerability to add to the testbed
title: "[FLAW] "
labels: new-flaw
---

## Summary

**Proposed flaw ID:** P___ (next available)
**OWASP Agentic 2026 mapping:** ASI0___ — ___
**One-line description:** What the attack does

## Attack vector

Describe the specific injection or manipulation technique. Include a draft of the poisoned input (use `.test` domains only — no real addresses).

## Harm definition

What tool call, with what arguments, counts as harm? Be precise — this becomes the judge function.

**Example action log entry that would be flagged:**
```json
{"tool": "...", "args": {...}, "allowed": true}
```

## Hardened control

What tool-layer control prevents the harm? Describe it in terms of the config YAML (allowlist, scope check, etc.).

## Checklist before submitting

- [ ] Attack proven exploitable by hand (not just plausible)
- [ ] Uses `.test` domains only
- [ ] No real systems, accounts, or personal data involved
- [ ] Harm definition is unambiguous (a specific tool call + args, not "harmful output")
- [ ] Hardened control is a tool-layer check, not a prompt instruction
