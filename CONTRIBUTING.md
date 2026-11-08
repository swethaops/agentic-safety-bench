# Contributing to agentic-safety-bench

Contributions are welcome. The most useful additions are new planted vulnerabilities,
improved harm judges, scanner configurations, and corrections to related work citations.

---

## Ground rules

- All tools must remain mocked. No real systems, accounts, or personal data.
- Use `.test` domains only. Never introduce real email addresses or hostnames.
- Every planted flaw must be proven exploitable before it is merged — a hand-proof JSONL in `ground_truth/exploits/` is required.
- Do not change ticket wording or harm-check logic after a flaw has been run. Changes invalidate pooled results. Open an issue first.

---

## Adding a new planted flaw

Use the issue template at `.github/ISSUE_TEMPLATE/new-flaw.md` to propose a flaw before implementing it.

### Checklist

- [ ] New ticket added to `ground_truth/tickets.json` with a unique `id`
- [ ] Flaw documented in `ground_truth/flaws.md` with OWASP mapping, harm definition, and labeling rule
- [ ] Labeled examples (REFUSED / COMPLIED) added to `flaws.md`
- [ ] Judge function added to `ground_truth/harm_checks.py` and registered in `JUDGES`
- [ ] Flaw scenario added to `FLAW_SCENARIOS` in `run_experiment.py`
- [ ] Vulnerable and hardened configs updated if new tool controls are needed
- [ ] Hand-proof JSONL saved in `ground_truth/exploits/<flaw-id>-proof.jsonl`
- [ ] Smoke test passes: `python run_experiment.py --trials 3 --flaw <id> --config vulnerable` shows attempt > 0%
- [ ] Block test passes: `python run_experiment.py --trials 3 --flaw <id> --config hardened` shows harm = 0%

---

## Adding a scanner configuration

Scanner configs go in `runners/`. Each scanner gets its own subdirectory.

```
runners/
  promptfoo/
    config.yaml
    README.md        # how to run, version pinned
  deepteam/
    config.py
    README.md
```

Each README must record:
- Exact tool version
- Command used to run it
- How verdicts map to OWASP categories

---

## Improving the harm judges

If you believe a judge is mis-classifying runs, open an issue with:
1. The run ID and log file
2. What the judge returned
3. What the correct label should be and why

Do not change judge logic without an issue — changes affect reproducibility of past results.

---

## Code style

- Python 3.10+, no `type: ignore`
- Format with `black` (line length 88): `pip install -r requirements-dev.txt && black .`
- No new runtime dependencies without discussion
- Pin all new dependencies to exact versions in `requirements.txt`

---

## Responsible disclosure

If you find that a scanner produces systematically misleading verdicts, follow the
disclosure process described in `README.md` before opening a public issue.
