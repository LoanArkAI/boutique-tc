# Logging a run

Every output-producing skill records what it did. Two lines of bookkeeping per run —
one at the start, one at the end — which is what makes it possible to tell later whether
a change to a skill actually improved anything.

Framework and rationale: [`../docs/skill-ops.md`](../docs/skill-ops.md).

## Where the script is

```bash
LOG="${CLAUDE_PLUGIN_ROOT:-../..}/scripts/log_run.py"
```

`CLAUDE_PLUGIN_ROOT` is set when the plugin is installed. The `../..` fallback is correct
when the working directory is a skill folder, and `scripts/log_run.py` is correct from the
repo root. The script resolves its own paths, so only reaching it matters.

## Start — before doing the work

```bash
RID=$(python3 "$LOG" start --skill whats-missing --trigger manual \
        --model "<the model serving this turn>" --deal-ref "<address or fub:ID>")
```

- `--trigger` — `manual` (a person asked), `scheduled` (a routine fired), `chained`
  (another skill called this one; add `--called-by <skill>`), or `test`.
- `--model` — the model **actually serving this turn**, not the one the session is
  configured for. They differ under fallback, and that difference shows up in quality.
- `--deal-ref` — the address or FUB id. Hashed before anything is committed.

Hold `$RID` for the rest of the run.

## Finish — after the work, before handing back

```bash
python3 "$LOG" finish --run-id "$RID" --outcome ok \
  --count tasks_created=14 --count drafts_created=3 \
  --action fub.create_deal --action fub.create_task \
  --output-ref fub:deal:8891 \
  --note "EMD fell on a Sunday, rolled to Monday"
```

- `--outcome` — `ok`, `partial` (some of it landed), `blocked` (stopped and asked, by
  design), or `error` (something failed). A refusal the skill is *supposed* to make is
  `blocked`, not `error`.
- `--count` — **numbers only**, and these do reach the committed metrics file. They're how
  you compare versions later, so record the ones that describe the size of the job.
- `--action` — the bare verb, no arguments. This is the audit trail for the additive-only
  and drafts-only guardrails, so record every write you performed.
- `--note` — free text, stays local. Anything surprising, especially a judgment call.

## Amend — when quality becomes known

The point of the log is the correction rate, and that isn't known when the skill finishes —
it's known when a human edits the result. `feedback-loop` writes this back automatically
for the email skills; anyone can do it by hand:

```bash
python3 "$LOG" amend --run-id "$RID" --human-edits 2 --audit-verdict aligned
```

## Rules

- **Log the run even when it fails.** A failed run is data. Skipping it makes the
  numbers say the skill is better than it is, which is the one outcome worth avoiding.
- **Never put a client name, address or email body in `--count`, `--action` or
  `--output-ref`.** Those reach git. Free text belongs in `--note`, which does not.
  `log_run.py` enforces this with an allowlist, but don't lean on it.
- **Never let logging block the work.** If the script errors, mention it and carry on —
  bookkeeping failing is not a reason to leave a deal half-built.
- **One run = one invocation of the skill.** If a skill chains into another, each gets its
  own record, linked with `--called-by`.
