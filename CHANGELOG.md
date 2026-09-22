# Changelog

One entry per skill version. Each entry states the **hypothesis** — what we expected the
change to do to the numbers in `metrics/runs.jsonl` — because the diff already records
what changed and only the changelog can record why. See [`docs/skill-ops.md`](docs/skill-ops.md).

Versions are per skill, tagged `<skill>/v<semver>`. The plugin version in
`.claude-plugin/plugin.json` moves independently.

---

## Unreleased

### create-deal, daily-sweep, dashboard, draft-emails, feedback-loop, inbox-watch, whats-missing 1.1.0
**Hypothesis:** the instrumentation from 0.2.0 measures nothing until something calls it.
Wiring `log_run.py` into each output-producing skill should take `metrics/runs.jsonl` from
empty to roughly one line per real run, which is the precondition for every comparison the
framework promises. If runs still aren't landing after two weeks of normal use, the problem
is the invocation contract, not the discipline — fix the contract.
**Changed:** a `## Log the run` section per skill, plus `references/run-logging.md` as the
shared contract. `feedback-loop` additionally amends the `draft-emails` runs it examines
with `--human-edits` / `--edit-distance`, which is what closes the loop.
MINOR, not PATCH: a new step is new behavior, even though no existing behavior changed.
**Watch:** run volume first, `draft-emails` edit-distance second.

### setup — deliberately not wired, stays 1.0.0
Runs once per machine, produces configuration rather than output, and has no dependent
variable to measure. Logging it would add noise to the metrics file without answering
any question. Revisit if setup starts failing in ways nobody can reconstruct.

### plugin 0.2.0
**Changed:** Adopted the Skill Ops framework — `version:` frontmatter on all eight
skills, run logging via `scripts/log_run.py`, and `docs/skill-ops.md`.
**Watch:** whether runs actually get logged. An instrumentation layer nobody invokes is
worse than none, because it looks like evidence.

---

## Baseline

### all skills 1.0.0
Versioning starts here. The eight skills — `create-deal`, `daily-sweep`, `dashboard`,
`draft-emails`, `feedback-loop`, `inbox-watch`, `setup`, `whats-missing` — are stamped
1.0.0 as they stood at `5fefbbe`. No behavior change; this is the zero mark that later
versions are measured against.

**Tuned against:** Claude Opus 5 / Sonnet 5 (goal-oriented phrasing). Not evaluated on
smaller models — see §4 of the framework before running these on Haiku.
