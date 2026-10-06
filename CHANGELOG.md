# Changelog

One entry per skill version. Each entry states the **hypothesis** — what we expected the
change to do to the numbers in `metrics/runs.jsonl` — because the diff already records
what changed and only the changelog can record why. See [`docs/skill-ops.md`](docs/skill-ops.md).

Versions are per skill, tagged `<skill>/v<semver>`. The plugin version in
`.claude-plugin/plugin.json` moves independently.

---

## ooo-handoff 1.0.0 (standalone, not in the plugin) — 2026-10-06

**Hypothesis:** while McKenna is out, file traffic sits unread in her inbox until she's back,
and her daily sweep reaches no one (it only drafts, and runs on her closed laptop). An hourly
cloud routine that forwards what reached her, plus a 7am/4pm brief of her files, sent to the
coverage people she named, should put every file-related arrival and deadline in front of
someone within the hour.
**Shape:** uploaded to her claude.ai account as its own skill (`standalone-skills/ooo-handoff.zip`),
run by a Claude Code on the web routine with her Gmail, DocuSign and Executor connectors. Config
in the routine prompt; state in her mailbox (a label, and subjects in Sent). The daily brief is
lighter than `daily-sweep` — FUB dates and tasks, not the 53-item checklist.
**Guardrail:** the only thing in this repo that sends email — to the confirmed coverage
recipients only; wire/payment messages are listed, never forwarded; read-only on FUB.
**Not instrumented:** no `log_run.py`, no `metrics/runs.jsonl` record — cloud runs are
discarded, and that was accepted. Judge it by the summaries in her Sent mail.
**Watch:** a real file message classed as bulk and skipped.

---

## plugin 0.4.2 — 2026-10-06

Release housekeeping. No skill text changed except version stamps; this entry catches the
changelog up with 0.3.0–0.4.1, which shipped without entries or skill version bumps.

### create-deal 2.0.0
**Hypothesis:** files already in FUB with blank date fields stay blank, because 1.x could
only create. Letting create-deal read the existing deal and fill only the blank or changed
date fields should cut the number of open deals with missing dates, without any
`human_edits` on fields nobody asked to change.
**Changed:** step 5 splits into a new-deal path and an existing-deal update/back-fill path
(`deals.getDeal` → field-scoped `deals.updateDeal`, `people.updatePerson`). Still no deletes.
MAJOR, not MINOR: the skill went from additive-only to permitted to update existing records,
which changes what it is allowed to do (shipped in plugin 0.3.0, stamped here).
**Watch:** any run where an update touched a field outside the confirmed set — that's a revert.

### manage-file 1.0.0
**Hypothesis:** stage moves, notes, appointments and reassignments were being done by hand
in FUB after create-deal opened the file. A confirm-then-write skill for those edits should
move that work into logged runs.
**Changed:** new skill (plugin 0.4.0). Plugin 0.4.1 fixed deal stage moves to resolve
`stageId` from `listPipelines` — `listStages` returns contact stages, not deal stages.
Stamped 1.0.0 at its 0.4.1 state; this is its baseline.
**Not yet wired:** no `## Log the run` section, so its runs won't land in
`metrics/runs.jsonl` until a later MINOR adds one.

### FUB spec 1.1.0 → 1.2.0 (plugin 0.3.0–0.4.0)
`executor/fub-openapi.json` gained edit/create operations (no delete): update deals, people,
appointments and tasks; create notes and appointments; read pipelines. This is the capability create-deal 2.0.0 and
manage-file 1.0.0 depend on.

---

## plugin 0.2.0

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

### plugin (framework)
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
