# runs/

Full run records, one JSON file per invocation: `runs/<skill>/<run_id>.json`.

**These are gitignored.** They carry client names, addresses and file detail, which is
exactly what this plugin's guardrails keep out of the repo. The de-identified subset —
versions, outcomes, counts, hashed deal references — is committed to
[`../metrics/runs.jsonl`](../metrics/runs.jsonl) instead, so metrics can be joined
against the skill versions that produced them without any client data entering git.

Written by [`../scripts/log_run.py`](../scripts/log_run.py). Schema and rationale:
[`../docs/skill-ops.md`](../docs/skill-ops.md) §2.

Local to each machine. Back them up if you care about the history; nothing else will.
