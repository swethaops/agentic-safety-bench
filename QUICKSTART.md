# Quickstart

Two paths: reproduce the benchmark, or adapt it for your own agent.

---

## Path 1 — Reproduce the benchmark

**Prerequisites:** Python 3.10+, one of the supported API keys below, < $0.10 budget for the full pilot.

```bash
git clone https://github.com/swethaops/agentic-safety-bench
cd agentic-safety-bench
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env — see Provider setup below
```

Run the full experiment (20 trials × 2 configs, all 4 flaws):

```bash
python run_experiment.py --trials 20 --flaw p1
python run_experiment.py --trials 20 --flaw p2
python run_experiment.py --trials 20 --flaw p3
python run_experiment.py --trials 20 --flaw p4
```

The HTML report is auto-generated after each run at `reports/assessment-YYYY-MM-DD.html`. No separate step needed.

Run a quick smoke test (3 trials, vulnerable only):

```bash
python run_experiment.py --trials 3 --config vulnerable --flaw p1
```

Results land in `results/YYYY-MM-DD/` and a row is appended to `RUNS.md`.

---

## Provider setup

Set `LLM_PROVIDER` in your `.env` to one of three options:

**Azure OpenAI (used for published results)**
```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano
```

**Anthropic**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**OpenAI**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## Path 2 — Adapt for your own agent

Use this path to generate audit-ready evidence for your own AI agent.

**What you replace:**

| File | What to change |
|---|---|
| `testbed/tools_mock.py` | Add mocked versions of your agent's real tools |
| `testbed/configs/hardened.yaml` | Document your current tool-layer controls |
| `ground_truth/tickets.json` | Write a poisoned input specific to your use case |
| `ground_truth/harm_checks.py` | Define what counts as harm for your tools |

**Step-by-step:**

1. **Mock your tools.** For each tool your agent can call, add a mock in `tools_mock.py`
   that logs the call and applies the allowlist/blocklist from your config.
   Nothing should touch real systems.

2. **Write your controls as config.** Open `testbed/configs/hardened.yaml` and
   document every domain allowlist, scope check, or action restriction your
   agent currently enforces. This becomes a machine-readable policy document.

3. **Write a poisoned input.** Create a ticket (or equivalent input) that
   looks legitimate but contains a hidden instruction targeting your use case.
   Use `.test` domains only — never real addresses.

4. **Define harm for your tools.** In `ground_truth/harm_checks.py`, add a
   `judge_log` rule that flags the specific tool call that would cause harm.

5. **Run and record.**
   ```bash
   python run_experiment.py --trials 20
   python generate_report.py
   ```
   The report and `RUNS.md` row are your audit evidence.

---

## What the outputs mean

| Output | Used for |
|---|---|
| `results/YYYY-MM-DD/*.jsonl` | Raw action logs — ground truth for every tool call |
| `RUNS.md` row | TEVV history (NIST AI 600-1 GV-1.5-003) |
| `reports/assessment-*.html` | Formatted evidence for audits, security reviews, investor due diligence |
| `docs/nist-controls.md` | Control-to-framework mapping for auditors |

---

## Expected cost

Costs are per-flaw (one `run_experiment.py` call, 20 trials × 2 configs).

| Scenario | Model | Approx. cost per flaw | Full pilot (4 flaws) |
|---|---|---|---|
| Smoke test (3 trials) | gpt-4.1-nano | < $0.01 | < $0.05 |
| Full pilot (20 trials × 2 configs) | gpt-4.1-nano | ~$0.02 | ~$0.08 |
| Published run (20 trials × 2 configs) | gpt-4o / claude-sonnet-5-5 | ~$0.50–$1 | ~$2–$4 |
| Your own agent (more tools, longer prompts) | any | Estimate 2–4× above | — |

Set a monthly spending cap in your provider console before running.
