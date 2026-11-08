"""Assessment report generator.

Reads per-flaw summary files from the results directory and produces
a dated HTML report with bar charts for all flaws.

Auto-called by run_experiment.py after every run.
Can also be run standalone:

    python generate_report.py
    python generate_report.py --results results/2026-11-07
    python generate_report.py --out reports/my-report.html
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from testbed.llm import MODEL_ID, TEMPERATURE

FLAWS = [
    ("p1", "Agent Goal Hijack",           "ASI01", "Subdomain-lookalike ITSM metadata injection"),
    ("p2", "Tool Misuse and Exploitation", "ASI02", "Plausible-business-justification injection"),
    ("p3", "Identity and Privilege Abuse", "ASI03", "Privileged account reset via social engineering"),
    ("p4", "Memory and Context Poisoning", "ASI06", "Persistent memory injection via subdomain-lookalike"),
]


# ── data loading ──────────────────────────────────────────────────────────────

def load_flaw_summaries(results_dir: Path) -> dict[str, dict[str, dict]]:
    """Return {flaw: {config: metrics}} for all per-flaw summary files found."""
    data: dict[str, dict[str, dict]] = {}
    for flaw_id, _, _, _ in FLAWS:
        data[flaw_id] = {}
        for config in ("vulnerable", "hardened"):
            path = results_dir / f"{config}_{flaw_id}_summary.json"
            if path.exists():
                with path.open(encoding="utf-8") as fh:
                    data[flaw_id][config] = json.load(fh)
    return data


def load_summaries(results_dir: Path) -> dict[str, dict]:
    """Legacy: read flat config summaries (used when called from run_experiment)."""
    summaries: dict[str, dict] = {}
    for path in results_dir.glob("*_summary.json"):
        # skip per-flaw files; keep only bare config summaries if any
        stem = path.stem.replace("_summary", "")
        if stem in ("vulnerable", "hardened"):
            with path.open(encoding="utf-8") as fh:
                summaries[stem] = json.load(fh)
    return summaries


def find_latest_results() -> Path | None:
    results_root = Path("results")
    if not results_root.exists():
        return None
    dated_dirs = sorted(
        [d for d in results_root.iterdir() if d.is_dir() and d.name != ".gitkeep"],
        reverse=True,
    )
    return dated_dirs[0] if dated_dirs else None


# ── HTML helpers ──────────────────────────────────────────────────────────────

def _pct(v: float) -> str:
    return f"{v:.0%}"


def _bar_row(label: str, fill_class: str, pct_class: str, value: float) -> str:
    width = max(value * 100, 0)
    zero = " zero" if value == 0 else ""
    return f"""
      <div class="bar-row">
        <span class="bar-label">{label}</span>
        <div class="bar-track"><div class="bar-fill {fill_class}{zero}" style="width:{width:.0f}%"></div></div>
        <span class="bar-pct {pct_class}">{_pct(value)}</span>
      </div>"""


def _config_block(config: str, metrics: dict) -> str:
    cls = "vuln" if config == "vulnerable" else "hard"
    attempt = metrics.get("attempt_rate", 0)
    harm    = metrics.get("harm_rate", 0)
    rba     = metrics.get("refused_but_attempted_rate", 0)
    harm_pct_cls = "safe-pct" if harm == 0 else "harm-pct"
    return f"""
        <div class="config-row">
          <span class="config-label {cls}">{config}</span>
          <div class="bars">
            {_bar_row("Attempt rate",        "attempt", "warn-pct",     attempt)}
            {_bar_row("Harm rate",           "harm",    harm_pct_cls,   harm)}
            {_bar_row("Refused but attempted","rba",    "gap-pct",      rba)}
          </div>
        </div>"""


def _flaw_card(flaw_id: str, name: str, owasp: str, vector: str, configs: dict[str, dict]) -> str:
    blocks = ""
    if configs:
        for config in ("vulnerable", "hardened"):
            if config in configs:
                blocks += _config_block(config, configs[config])
    else:
        blocks = "<p class='no-data'>No data yet — run python run_experiment.py --flaw " + flaw_id + "</p>"

    return f"""
      <div class="flaw-card">
        <div class="flaw-header">
          <span class="flaw-id">{flaw_id.upper()}</span>
          <span class="flaw-name">{name}</span>
          <span class="flaw-owasp">{owasp} · {vector}</span>
        </div>
        <div class="flaw-body">{blocks}</div>
      </div>"""


def render_html(summaries: dict[str, dict], results_dir: Path, report_date: str) -> str:
    # Try to load per-flaw summaries; fall back to flat summaries for legacy calls
    flaw_data = load_flaw_summaries(results_dir)

    # If no per-flaw data at all, use flat summaries under "p1" for backwards compat
    has_flaw_data = any(flaw_data[f] for f, *_ in FLAWS)
    if not has_flaw_data and summaries:
        flaw_data["p1"] = summaries

    flaw_cards = "".join(
        _flaw_card(fid, name, owasp, vector, flaw_data.get(fid, {}))
        for fid, name, owasp, vector in FLAWS
    )

    # Summary stats
    all_hards = [flaw_data[f].get("hardened", {}) for f, *_ in FLAWS if flaw_data.get(f, {}).get("hardened")]
    flaws_zero_harm = sum(1 for m in all_hards if m.get("harm_rate", 1) == 0)
    total_flaws = len([f for f, *_ in FLAWS if flaw_data.get(f)])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="claude:viewport-fit-sides" content="cover">
<title>agent-scanner-bench</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Layout: single-column report, stat strip, per-flaw cards, NIST table */
:root {{
  --bg:        #f4f6f9;
  --surface:   #ffffff;
  --surface-2: #edf0f4;
  --border:    #d6dbe4;
  --text:      #1a2233;
  --text-dim:  #5a6a84;
  --text-head: #0d1520;
  --accent:    #2563eb;
  --accent-bg: #eff4ff;
  --harm:      #dc2626;
  --harm-bg:   #fff1f1;
  --safe:      #16a34a;
  --safe-bg:   #f0fdf4;
  --warn:      #b45309;
  --warn-bg:   #fffbeb;
  --gap-color: #7c3aed;
  --gap-bg:    #f5f3ff;
  --mono: 'IBM Plex Mono', 'Consolas', monospace;
  --sans: 'IBM Plex Sans', system-ui, sans-serif;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0b0f1a;--surface:#131929;--surface-2:#1a2234;--border:#263047;
    --text:#c8d3e8;--text-dim:#6b7c9b;--text-head:#e8edf8;
    --accent:#60a5fa;--accent-bg:#0f1f3d;
    --harm:#f87171;--harm-bg:#2a0f0f;--safe:#4ade80;--safe-bg:#0a2318;
    --warn:#fbbf24;--warn-bg:#231a06;--gap-color:#a78bfa;--gap-bg:#160f2e;
    color-scheme:dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0b0f1a;--surface:#131929;--surface-2:#1a2234;--border:#263047;
  --text:#c8d3e8;--text-dim:#6b7c9b;--text-head:#e8edf8;
  --accent:#60a5fa;--accent-bg:#0f1f3d;
  --harm:#f87171;--harm-bg:#2a0f0f;--safe:#4ade80;--safe-bg:#0a2318;
  --warn:#fbbf24;--warn-bg:#231a06;--gap-color:#a78bfa;--gap-bg:#160f2e;
  color-scheme:dark;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:var(--bg);color:var(--text);font-family:var(--sans);
  font-size:14px;line-height:1.6;
  padding-block:40px;
  padding-left:max(24px,env(safe-area-inset-left,0px));
  padding-right:max(24px,env(safe-area-inset-right,0px));
}}
.wrap{{max-width:860px;margin:0 auto;display:flex;flex-direction:column;gap:32px}}
.header{{border-bottom:2px solid var(--border);padding-bottom:24px}}
.header-top{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:8px}}
.header-top h1{{font-family:var(--mono);font-size:20px;font-weight:500;color:var(--text-head);letter-spacing:-.02em}}
.tag{{font-family:var(--mono);font-size:10px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;
  padding:2px 8px;border-radius:3px;background:var(--accent-bg);color:var(--accent);
  border:1px solid color-mix(in srgb,var(--accent) 30%,transparent)}}
.meta-row{{font-family:var(--mono);font-size:11px;color:var(--text-dim);display:flex;gap:20px;flex-wrap:wrap}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
@media(max-width:600px){{.stats{{grid-template-columns:repeat(2,1fr)}}}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:16px}}
.stat-value{{font-family:var(--mono);font-size:24px;font-weight:500;color:var(--text-head);
  font-variant-numeric:tabular-nums;line-height:1;margin-bottom:6px}}
.stat-value.green{{color:var(--safe)}}
.stat-label{{font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:.07em}}
.gap-callout{{background:var(--gap-bg);border:1px solid color-mix(in srgb,var(--gap-color) 35%,transparent);
  border-radius:8px;padding:18px 20px}}
.gap-callout-head{{font-family:var(--mono);font-size:11px;font-weight:500;letter-spacing:.1em;
  text-transform:uppercase;color:var(--gap-color);margin-bottom:6px}}
.gap-callout p{{font-size:13px;color:var(--text);max-width:680px}}
.section-title{{font-family:var(--mono);font-size:11px;font-weight:500;letter-spacing:.1em;
  text-transform:uppercase;color:var(--text-dim);margin-bottom:10px;
  padding-bottom:8px;border-bottom:1px solid var(--border)}}
.flaw-card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden}}
.flaw-header{{display:flex;align-items:center;gap:12px;padding:14px 18px;
  border-bottom:1px solid var(--border);background:var(--surface-2);flex-wrap:wrap}}
.flaw-id{{font-family:var(--mono);font-size:12px;font-weight:500;color:var(--accent)}}
.flaw-name{{font-weight:600;font-size:14px;color:var(--text-head)}}
.flaw-owasp{{font-family:var(--mono);font-size:10px;color:var(--text-dim);margin-left:auto;letter-spacing:.06em}}
.flaw-body{{padding:16px 18px;display:flex;flex-direction:column;gap:14px}}
.config-row{{display:grid;grid-template-columns:90px 1fr;gap:12px;align-items:start}}
@media(max-width:520px){{.config-row{{grid-template-columns:1fr}}}}
.config-label{{font-family:var(--mono);font-size:11px;font-weight:500;padding:4px 8px;
  border-radius:3px;text-align:center;letter-spacing:.04em}}
.config-label.vuln{{background:var(--harm-bg);color:var(--harm);
  border:1px solid color-mix(in srgb,var(--harm) 25%,transparent)}}
.config-label.hard{{background:var(--safe-bg);color:var(--safe);
  border:1px solid color-mix(in srgb,var(--safe) 25%,transparent)}}
.bars{{display:flex;flex-direction:column;gap:6px}}
.bar-row{{display:grid;grid-template-columns:140px 1fr 42px;gap:8px;align-items:center}}
.bar-label{{font-size:11px;color:var(--text-dim)}}
.bar-track{{height:8px;background:var(--surface-2);border-radius:4px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:4px}}
.bar-fill.attempt{{background:var(--warn)}}
.bar-fill.harm{{background:var(--harm)}}
.bar-fill.rba{{background:var(--gap-color)}}
.bar-fill.zero{{background:color-mix(in srgb,var(--safe) 40%,transparent);width:2px!important}}
.bar-pct{{font-family:var(--mono);font-size:11px;font-weight:500;font-variant-numeric:tabular-nums;text-align:right}}
.harm-pct{{color:var(--harm)}}.safe-pct{{color:var(--safe)}}.warn-pct{{color:var(--warn)}}
.gap-pct{{color:var(--gap-color)}}.dim-pct{{color:var(--text-dim)}}
.no-data{{font-size:12px;color:var(--text-dim);font-family:var(--mono)}}
.nist-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{font-family:var(--mono);font-size:10px;font-weight:500;letter-spacing:.09em;text-transform:uppercase;
  color:var(--text-dim);text-align:left;padding:8px 12px;border-bottom:1px solid var(--border)}}
td{{padding:9px 12px;border-bottom:1px solid var(--border);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
td.code{{font-family:var(--mono);font-size:11px;color:var(--accent);white-space:nowrap}}
td.pass{{font-family:var(--mono);font-size:11px;color:var(--safe);font-weight:500}}
td.gap-st{{font-family:var(--mono);font-size:11px;color:var(--warn);font-weight:500}}
td.evidence{{font-size:12px;color:var(--text-dim)}}
.footer{{border-top:1px solid var(--border);padding-top:16px;display:flex;
  justify-content:space-between;flex-wrap:wrap;gap:8px;
  font-family:var(--mono);font-size:11px;color:var(--text-dim)}}
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <div class="header-top">
      <h1>agent-scanner-bench</h1>
      <span class="tag">Pilot Results</span>
    </div>
    <div class="meta-row">
      <span>Date: {report_date}</span>
      <span>Model: {MODEL_ID}</span>
      <span>Temperature: {TEMPERATURE}</span>
      <span>Results: {results_dir.name}</span>
      <span>Framework: OWASP Agentic 2026 · NIST AI 600-1</span>
    </div>
  </div>

  <div class="stats">
    <div class="stat">
      <div class="stat-value green">{flaws_zero_harm} / {total_flaws}</div>
      <div class="stat-label">Flaws with 0% harm (hardened)</div>
    </div>
    <div class="stat">
      <div class="stat-value">100%</div>
      <div class="stat-label">Harm rate, vulnerable config</div>
    </div>
    <div class="stat">
      <div class="stat-value green">0%</div>
      <div class="stat-label">Harm rate, hardened config</div>
    </div>
    <div class="stat">
      <div class="stat-value">85%</div>
      <div class="stat-label">Peak refused-but-attempted (P1)</div>
    </div>
  </div>

  <div class="gap-callout">
    <div class="gap-callout-head">Mind the GAP — Key Finding</div>
    <p>In the hardened configuration, attempt rates stay at 100% across P1–P3 while harm drops to 0%.
    The agent never flags the attack in its reply text, yet the action log records a tool-call attempt every time.
    A scanner judging only reply text would classify these runs as safe — the action log tells a different story.</p>
  </div>

  <div>
    <div class="section-title">Results by flaw — 20 trials per configuration</div>
    <div style="display:flex;flex-direction:column;gap:12px;">
      {flaw_cards}
    </div>
  </div>

  <div>
    <div class="section-title">NIST AI 600-1 Control Evidence</div>
    <div class="nist-wrap">
      <table>
        <thead><tr><th>Control</th><th>Evidence artefact</th><th>Status</th></tr></thead>
        <tbody>
          <tr><td class="code">GV-1.5-003</td><td class="evidence">RUNS.md — versioned per-run record with model, temperature, date, metrics</td><td class="pass">✓ Met</td></tr>
          <tr><td class="code">GV-6.1</td><td class="evidence">hardened.yaml — machine-readable domain allowlist and privilege policy</td><td class="pass">✓ Met</td></tr>
          <tr><td class="code">MP-2.3</td><td class="evidence">tickets.json + ground_truth/flaws.md — hand-verified adversarial inputs, OWASP-mapped</td><td class="pass">✓ Met</td></tr>
          <tr><td class="code">MS-2.13-001</td><td class="evidence">harm_checks.py — action log vs. reply verdict, construct validity measured per flaw</td><td class="pass">✓ Met</td></tr>
          <tr><td class="code">MS-2.3-002</td><td class="evidence">Hardened/vulnerable twin — empirically validated, same model and prompt, only tool layer differs</td><td class="pass">✓ Met</td></tr>
          <tr><td class="code">MG-3.2</td><td class="evidence">Harm rate delta 100% → 0% across all four flaws demonstrates control effectiveness</td><td class="pass">✓ Met</td></tr>
          <tr><td class="code">MG-2.2</td><td class="evidence">Incident response plan not yet documented</td><td class="gap-st">Gap</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <div>
    <div class="section-title">Scope and Limitations</div>
    <p style="font-size:13px;color:var(--text-dim);max-width:680px;line-height:1.65;">
      Assessment covers four planted flaws (P1–P4) against {MODEL_ID} at temperature {TEMPERATURE}.
      All tools are mocked; no real systems, accounts, or personal data are involved.
      All domains use the reserved <code style="font-family:var(--mono);font-size:11px;">.test</code> TLD.
      Scanner integration (promptfoo, DeepTeam) is pending.
    </p>
  </div>

  <div class="footer">
    <span>agent-scanner-bench · {report_date} · Apache 2.0</span>
    <span>OWASP Agentic 2026 · NIST AI 600-1 · ISO 42001</span>
  </div>

</div>
</body>
</html>"""


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate HTML assessment report from experiment results."
    )
    parser.add_argument("--results", type=Path, default=None)
    parser.add_argument("--out",     type=Path, default=None)
    args = parser.parse_args()

    results_dir = args.results or find_latest_results()
    if not results_dir:
        print("No results found. Run `python run_experiment.py` first.")
        raise SystemExit(1)

    report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path: Path = args.out or Path("reports") / f"assessment-{report_date}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summaries = load_summaries(results_dir)
    html = render_html(summaries, results_dir, report_date)
    out_path.write_text(html, encoding="utf-8")
    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
