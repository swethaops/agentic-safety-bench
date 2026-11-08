# Scanner configurations

This directory holds runner configurations — one subdirectory per scanner tool.

Each subdirectory contains:
- The scanner's config file (e.g. `config.yaml`, `config.py`)
- A `README.md` recording the exact tool version, run command, and how verdicts map to OWASP categories

## Status

Scanner configurations are in progress. The testbed and ground truth are complete and published; scanner runs will be added here as they are executed and results verified.

If you want to contribute a scanner configuration, see [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-scanner-configuration) for the checklist and expected structure.

## Planned

| Scanner | OWASP agentic coverage claimed | Status |
|---|---|---|
| promptfoo | ASI01–ASI06 preset | Planned |
| DeepTeam | OWASP Top 10 for Agents | Planned |

Results will be published in [`RUNS.md`](../RUNS.md) with scanner version, date, and verdict-vs-action-log agreement.
