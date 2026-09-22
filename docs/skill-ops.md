# Skill Ops

How we version, measure, audit and tune the skills in this plugin.

Source: [@agentic.james, "How to create amazing agent skills"](https://www.tiktok.com/t/ZP8TdLJpD/) —
five tips, translated here into mechanics for this repo. His framing is the useful one:
**a skill is agentic software, so treat the skill as the independent variable and its
output as the dependent variable.** Everything below exists to make that experiment
actually runnable rather than aspirational.

The five tips become one loop:

```
   ┌── 1 VERSION ──── 2 INSTRUMENT ──── 3 AUDIT ──── 4 TUNE ──┐
   │   pin the                capture          read the      adjust for   │
   │   independent            the dependent    mechanism,    the model    │
   │   variable               variable         not just      you're on    │
   │                                           the result                 │
   └──────────────────── 5 REGENERATE ◀───────────────────────┘
                    skill-creator writes the next candidate
```

Stages 1 and 2 are infrastructure — built, in this repo, described below.
Stages 3–5 are practice — procedures, run by a human or by `skill-creator`.

---

## The one thing that makes 1 and 2 work

They are not two habits. They are one mechanism with a **join key**.

Versioning without run logs tells you the skill changed but not whether it got better.
Run logs without versioning tell you quality moved but not what moved it. The common
failure is doing both and *still* learning nothing, because the log never recorded
which version produced it — so there is no way to join the two tables.

> **Every run record stamps the skill version and the git SHA that produced it.**
> That stamp is the entire point. A log without it is a diary, not an experiment.

Concretely, `metrics/runs.jsonl` carries `skill`, `skill_version`, `git_sha` and
`model` on every line, so this question is a one-liner:

```bash
# did create-deal v1.2.0 actually reduce human corrections vs v1.1.0?
jq -s 'group_by(.skill_version)[] | {version: .[0].skill_version, runs: length,
       mean_edits: (map(.human_edits // 0) | add / length)}' \
  metrics/runs.jsonl
```

---

## 1 · Version

Git alone is not versioning. The repo has had history since day one and it told us
nothing, because nothing tied a commit to a result.

**Mechanics**

| Rule | Why |
|---|---|
| `version:` in every `SKILL.md` frontmatter | The number travels *inside* the skill, so a run can read it without git |
| Semver, with skill-specific meaning (below) | Tells a reader whether a bump can break them |
| One skill per behavior-changing commit | Two skills in one commit = confounded variables, experiment ruined |
| Tag as `<skill>/v<semver>` | `git diff create-deal/v1.1.0..create-deal/v1.2.0 -- skills/create-deal/` is the exact independent variable |
| A `CHANGELOG.md` entry stating the **hypothesis** | "Why" is the experiment; "what" is already in the diff |

**Semver for a prompt** — the usual definitions don't transfer, so:

- **MAJOR** — changes what the skill is permitted to do, or the shape of its output.
  A downstream consumer (a human habit, another skill, the board) breaks.
  *e.g. `draft-emails` starts sending instead of drafting; `create-deal` changes its tag scheme.*
- **MINOR** — new capability or new branch; everything that worked still works.
  *e.g. a new template, handling a counter-offer case.*
- **PATCH** — wording, ordering, clarity, a tightened trigger. Intended behavior unchanged.
  *e.g. rephrasing a step the model kept misreading.*

A PATCH that changes behavior was a MINOR. If you're unsure, it's a MINOR.

**Tagging a release**

```bash
git tag create-deal/v1.1.0 -m "create-deal: counter-offer date handling"
git push origin create-deal/v1.1.0
```

**The changelog entry is the lab notebook.** Not this:

> - Improved the deadline logic.

This:

> ### create-deal 1.1.0
> **Hypothesis:** the EMD deadline was being computed from the offer date rather than
> acceptance, causing McKenna to correct roughly 1 in 3 files. Stating acceptance as
> the explicit anchor, once, at the top of the date block should drive `human_edits`
> on date fields toward zero.
> **Changed:** date-anchor paragraph in the deadline section.
> **Watch:** `human_edits` on create-deal runs over the next 10 files.

Now a future reader — including a future model — can tell whether the change worked.

---

## 2 · Instrument

Every run of an output-producing skill writes a record. Two files, deliberately:

```
runs/<skill>/<run_id>.json    full record — GITIGNORED, may contain client data
metrics/runs.jsonl            one line per run — COMMITTED, de-identified
```

**Why the split.** The video doesn't address this because most skills don't touch
regulated data. Ours do. Every run of `create-deal` or `draft-emails` handles a real
client's name, address and transaction. That cannot go in git — it collides directly
with this plugin's data guardrails. But a metrics file that lives *outside* git can't
be joined against the versions it measures, which defeats the whole mechanism.

So the record is split by sensitivity, not by convenience:

> **The committed line contains identifiers, enums and numbers. Never prose.**

Free text is where names leak. `notes`, `inputs` and `output_refs` stay local; counts,
outcomes, versions and hashed references get committed. `log_run.py` enforces this with
an allowlist (`METRIC_KEYS`) rather than a redaction pass — a field is excluded unless
someone deliberately added it, which fails safe when the schema grows.

Addresses become `deal_ref: "h:a786ba087ce3"` — a truncated SHA-256, stable across runs
so you can follow one file through the pipeline, and not reversible into an address.

**Recording a run**

```bash
RID=$(scripts/log_run.py start --skill create-deal --trigger manual \
        --model "$SERVED_MODEL" --deal-ref "1247 Marine Ave")

scripts/log_run.py finish --run-id "$RID" --outcome ok \
  --count tasks_created=14 --count drafts_created=3 \
  --action fub.create_deal --action fub.create_task \
  --output-ref fub:deal:8891 \
  --note "EMD fell on a Sunday, rolled to Monday"
```

**The dependent variable arrives later than the run.** This is the second thing the
video leaves implicit and it drives the design. At the moment a skill finishes, you do
not yet know whether it was any good — that's known when McKenna edits the draft, or
sends it untouched, or has to redo the dates. So records are amendable:

```bash
scripts/log_run.py amend --run-id "$RID" \
  --human-edits 2 --edit-distance 0.11 --audit-verdict minor-deviation
```

**Our quality metric already exists.** `feedback-loop` compares what `draft-emails`
drafted against what was actually sent. That gap *is* the dependent variable for the
email skills — it just wasn't being recorded per-version. Have `feedback-loop` amend
each run with `--edit-distance` and the loop closes: voice quality becomes a number
plotted against skill version.

**Schema** — full record; committed subset marked ✓.

| Field | ✓ | Notes |
|---|:-:|---|
| `run_id` | ✓ | join key across both files |
| `skill`, `skill_version` | ✓ | **the independent variable** |
| `plugin_version`, `git_sha`, `git_dirty` | ✓ | `git_dirty: true` means uncommitted edits — the run is not reproducible, treat it as a scratch run |
| `model` | ✓ | the model that *served* the turn (see §4) |
| `trigger`, `called_by` | ✓ | `manual`, `scheduled`, `chained`, `test` |
| `deal_ref` | ✓ | hashed |
| `ts`, `ended_at`, `duration_s` | ✓ | |
| `inputs` | — | local only, free text |
| `counts` | ✓ | numeric only |
| `actions` | ✓ | bare verbs, no arguments — your guardrail audit trail |
| `output_refs` | — | local only |
| `outcome`, `error_class` | ✓ | `ok` / `partial` / `blocked` / `error` |
| `human_edits`, `edit_distance` | ✓ | **the dependent variable**, amended in later |
| `audit_verdict`, `audit_deviations` | ✓ | from §3 |
| `notes` | — | local only |

**`actions` earns its place here.** This plugin promises additive-only writes to FUB and
drafts-only outbound. A committed, de-identified list of every verb each run performed
is the evidence that the promise held — useful the first time someone asks whether the
assistant touched a field it shouldn't have.

---

## 3 · Audit

Read the transcript after a run and ask whether the agent's *actions* matched the
skill's *intent*. The output can be right for the wrong reasons, and that's the run
that bites you later.

**Rubric** — five questions, recorded as `audit_verdict`:

1. Did it honor the guardrails (additive-only, drafts-only, broker sign-off)?
2. Did it take a step the skill never authorized?
3. Did it skip a step the skill required?
4. Did it ask the human at the points the skill says to ask?
5. **Where did it improvise, and was the improvisation better than the skill?**

Question 5 is the valuable one. When a model routes around your instructions and gets a
better result, it has found something your skill doesn't know. Promote it into the skill
and bump the version.

**Sample rate:** every run for the first five after a version bump, then spot-check —
weekly, or any run where `human_edits` spikes.

`anthropic-skills:skill-creator` can run evals and variance analysis over a skill, which
covers part of this. The creator also sells a purpose-built "Skill Optimizer"; I haven't
evaluated it, so treat the rubric above as the baseline and that as an option.

---

## 4 · Tune to the model

His claim, which matches how these skills behave: **older and smaller models need more
context and more of your prescriptive judgement; newer and larger models need more goal
orientation and less.** Over-prescribing to a strong model actively hurts — it fights the
model's own planning and you get brittle literal compliance.

| | Smaller / older (e.g. Haiku) | Larger / newer (e.g. Opus, Sonnet) |
|---|---|---|
| Steps | Enumerated, ordered, explicit | Goal + constraints, let it sequence |
| Fields | Name every one literally | Name the contract, not each keystroke |
| Branches | Spell out every case | State the principle, trust the edge cases |
| Failure | Prescribe the fallback | Say what "blocked" means and to stop |
| Length | Longer — context is scaffolding | Shorter — length becomes noise |

Rewrite the same instruction both ways:

> **Prescriptive:** "Set `Close of Escrow` to acceptance + 30 days. If that lands on a
> Saturday or Sunday, move it to Monday. If it lands on a federal holiday, move it to
> the next business day. If the contract specifies a different COE, use that instead."
>
> **Goal-oriented:** "Set `Close of Escrow` from the contract, falling back to
> acceptance + 30 days. Deadlines land on business days."

Second version, wrong model, quietly files a Saturday deadline.

**The model is a second independent variable, and it moves without you touching
anything.** A session's configured model is not necessarily the one that serves a given
turn — fallbacks happen under load, and defaults change under you. So `log_run.py`
stamps the *served* model on every record. When quality drops and the skill didn't
change, check `model` before you start rewriting prose:

```bash
jq -s 'group_by(.model)[] | {model: .[0].model, runs: length,
       mean_edits: (map(.human_edits // 0) | add / length)}' metrics/runs.jsonl
```

Note in the changelog which model a version was tuned against.

---

## 5 · Regenerate

Don't hand-author a new skill. `anthropic-skills:skill-creator` is available in this
session and is the front end of the loop — it structures the skill, writes the
description for trigger accuracy (the hardest part to get right by hand), and can
benchmark the result.

Use it for new skills, and again when an existing skill has accumulated enough patches
that it reads like sediment. Feed it the changelog and the audit findings; regenerate;
bump MAJOR or MINOR; watch the metrics for ten runs.

---

## Doing it

**New skill:** generate with `skill-creator` → `version: 1.0.0` → changelog entry with the
hypothesis → wire `log_run.py` → audit the first five runs.

**Changing a skill:** write the hypothesis *first* → change one skill → bump per the
semver table → tag → audit five runs → compare `human_edits` across versions → keep or revert.

**Weekly:** `jq` the metrics by version and by model; spot-audit one transcript; promote
anything `feedback-loop` learned into the skill that should have known it.

The discipline that makes it work is the boring one: **change one thing, write down what
you expected, then look.**
