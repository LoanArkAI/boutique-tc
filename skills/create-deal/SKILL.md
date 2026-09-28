---
name: create-deal
version: 1.1.0
description: >-
  Open a new transaction in Follow Up Boss for The Boutique Real Estate Group from an
  accepted purchase contract. Use this whenever McKenna, Raj, or the team says a deal
  went into contract, an offer was accepted, "open a file / open escrow / start a new
  deal", "we're in contract on [address]", or hands over an executed RPA / counter and
  wants it set up in FUB. It runs a short Q&A, computes the contract deadlines, and
  writes the FUB deal — date fields, conditional tags, and dated tasks — then drafts the
  intro emails and the shared deadline calendar. Trigger it even if they don't say
  "Follow Up Boss" — setting up any new transaction for this brokerage is this skill's job.
  It only ever ADDS to FUB; it never edits or deletes existing client or deal data.
---

# Create a Deal (The Boutique — FUB)

Turn an accepted contract into a fully set-up Follow Up Boss deal in one short sitting.
FUB is the filing cabinet and alarm clock; this skill reads the contract, fills the
cabinet, and sets the alarms. The person stays in the loop for every judgment call and
confirms the dates before anything is written.

**Source of truth for the process:** the Boutique TC Playbook
(`docs/playbook/boutique-tc-playbook.md`). When the process changes, the playbook changes
and this skill follows it. Read `references/fub-field-map.md` for the exact FUB fields,
tags, and the 53-item task set; read `references/date-rules.md` for the deadline math.

## Non-negotiables (why they matter)

- **Additive only.** Create new deals, fields, tags, tasks. Never edit or delete an
  existing deal, contact, or task — this is Raj's live book of business, and a wrong
  overwrite is unrecoverable. If a deal for this address already exists, stop and ask.
- **Refuse over guess on dates.** A wrong contingency-removal date can blow a contingency —
  the exact disaster this exists to prevent. If the contract is ambiguous or a date can't
  be read, leave that field blank, say why, and let the human supply it. Never write a
  date you're not sure of.
- **Confirm before writing.** Show the computed dates and the deal summary and get a yes
  before any write to FUB. The human is the last check on the math.
- **Drafts only outbound.** Any email to escrow, a lender, the other side, or a client is
  drafted for Raj to send — never sent by the skill.
- **Caroline signs off.** Nothing here records broker approval; the file goes to Caroline
  at the end (a later step, not this skill).

## What you need before starting

- The **executed contract** (RPA + any counters), or at least the key dates the human can read off it.
- FUB access: through the **Executor** MCP (`executor` server) — see `../../references/executor-fub.md`. Executor holds the FUB key in its vault; the key never reaches this skill. No `.env` file, no Python, no raw key.
- Optional: the **RPA Processor** JSON export for this contract — if present, it supplies the dates and you skip hand-entry. If absent, the human reads dates off the contract in the Q&A.

## The flow

### 1. Identify the deal — new, or an existing one to update
Get the property address and client name(s). Search FUB (`deals.listDeals` / `people.listPeople`)
for a deal at that address.
- **No match → create.** Proceed to build a new deal.
- **Match → update, don't duplicate.** Never create a second deal for the same address. Ask
  whether to update the existing one. Updating is allowed for the **date fields this skill
  manages** (acceptance, CR1/CR2, due-diligence, close, walkthrough) and for adding tasks/tags —
  because counters and amendments legitimately move dates. It is still **additive/safe**: never
  delete the deal, never overwrite client fields it doesn't manage (name, price, people), never
  clear a field to blank. Same confirm gate applies before any write.
McKenna can also just say "update the deal for [address]" directly — same path, skipping create.

### 2. Get the dates — three ways, best first
**(a) RPA JSON export** (most accurate — deterministic engine). If provided, read
`acceptance_date`, the deadline entries, and any `refusals` (see `references/fub-field-map.md`
for the shape). A `refusal` means that field stays blank — surface the reason, don't invent.

**(b) The executed contract PDF, handed to you directly.** McKenna can just drop the RPA
(and any counters) into the chat. Read the dates off it yourself: binding acceptance (last
signature), close of escrow (page 1 §3B), and the contingency periods (page 2 §L). This is
available today, before the RPA export exists. Because you are reading a document rather than
running the deterministic engine, be strict: **show every date next to the page/clause you
read it from, and if a date is handwritten-unclear or the chain has two plausible acceptance
dates, treat it as a refusal and ask — never guess.** A wrong contingency date is the failure
this whole system exists to prevent.

**(c) Ask.** If there's no export and no document, ask the human what the contract says, one
clean question at a time:
- Binding acceptance date (last signature on the RPA or last counter)
- Close of escrow (RPA page 1 §3B — remind them to check counters)
- Contingency periods if non-default (loan / appraisal / investigation days)

Then compute the removal dates with **`scripts/compute_dates.py`** — never by hand. It
applies the rules deterministically (count all days, roll weekends/US-federal-holidays
forward) and returns a ready `fub_fields` block plus each date's raw pre-roll value:
```
python scripts/compute_dates.py --acceptance 2026-10-01 --loan 14 --appraisal 14 --investigation 7 --coe 30
```
Doing the math in code, not in your head, is the point — a miscounted CR date is the failure
this prevents. `references/date-rules.md` explains the rules and the CR1/CR2 derivation.
Present every date back for confirmation (with its basis) before anything is written.

### 3. Run the conditional Q&A (the part the contract can't tell you)
These come from the MLS sheet / the human, not the contract. Ask them plainly and keep the
answers as tags — they decide which of the 53 checklist items this file actually needs:
- Which **side** are we — buyer or listing?
- **Escrow company** (is it Lighthouse?)
- **HOA?** · **Solar?** · **Trust / LLC / POA?** · **High fire zone?**
- **Year built** (drives lead-paint pre-1978 and earthquake pre-1960)
- **Home warranty** — buyer-paid? terms? (buyer names, coverage, price for the Staci order)
- **Team file?** (Raj & Christina → AAA)

`references/fub-field-map.md` maps each answer to its tag and the items it turns on/off.

### 4. Show the plan, get the go
Summarize: the deal (address, side, client, price), the confirmed dates, the tags, and the
count of tasks that will be created. Ask for a yes. This is the write gate.

### 5. Write to FUB (via Executor)
Call FUB through the **Executor** MCP — `search` the operation, then `invoke` it (see
`../../references/executor-fub.md` for ids, the `body` wrapper, and proven shapes). Two cases:

**New deal (from step 1 "create"):**
- `people.listPeople` → resolve/confirm the contact's `personId` (tasks attach to a person).
- `deals.createDeal` with `{ body: { name, stageId, price, and every confirmed date field
  (`mutualAcceptanceDate`, `dueDiligenceDate`, `customCR1`, `customCR2Date`,
  `projectedCloseDate`, `finalWalkThroughDate`) } }` — **omit any date that was refused**, never a placeholder.
- `tasks.createTask` for each side-aware item, `{ body: { name, type:"Closing", dueDate, personId } }`.
- Apply the `cond:*` / `side:*` tags to the contact.

**Existing deal (update / back-fill from step 1 "update"):**
- `deals.getDeal { dealId }` first — read what's already there so you only change what's needed.
- `deals.updateDeal { dealId, body: { ...only the date fields that changed or were blank } }` —
  send **only** the fields you are setting. Never include `name`/`price`/`people` you weren't
  asked to change, and never blank a field that already has a value. This is how you back-fill
  the deals already in FUB that have no dates yet: fill the blank date fields, leave the rest.
- Add any still-missing side-aware tasks/tags additively — don't duplicate tasks that already exist.
- To correct a contact you were asked to fix: `people.updatePerson { personId, body: { ...only
  changed fields } }` (adding to `emails`/`phones`/`tags` appends). Same field-scoped rule.

**Never delete anything** (there is no delete op). Updates are allowed but stay field-scoped and
were confirmed at the step-4 gate. If an invoke fails, stop and report the exact error; do not
retry blindly or half-finish silently.

(Local Claude Code only, offline fallback: `scripts/fub_create_deal.py` + `.env.raj` does the
same writes directly. In Cowork, always use Executor — there is no local key.)

### 6. Draft the intro emails and the calendar
- Draft the accepted-offer intros (escrow / lender / listing agent) and the warranty-to-Staci
  email from the `TBREG |` templates in FUB, personalized to this file. Leave them as drafts.
- Create the hard deadlines (CR1, CR2, close of escrow) on the shared **"Escrow Deadlines"**
  Google calendar (a dedicated calendar, NOT the primary — FUB two-way-syncs the primary and
  would duplicate). Each event carries a reminder.

### 7. Hand back
Tell the human what was created (deal link, dates, task count, which drafts are waiting),
and name anything left blank and why (the refusals). Do not move the deal stage or notify
anyone beyond this.

## When something is off
- **Two plausible acceptance dates / unreadable date** → treat as a refusal; ask the human, don't pick one.
- **Address already has a deal** → stop, confirm intent.
- **A conditional you're unsure of** (is it really a trust?) → ask; the tag drives real compliance items.
- **FUB write error** → stop, report the exact error, leave the rest unwritten rather than guessing state.

## Log the run

This skill produces output, so it records what it did — see
[`../../references/run-logging.md`](../../references/run-logging.md) for the full contract.

Before starting the work:

```bash
LOG="${CLAUDE_PLUGIN_ROOT:-../..}/scripts/log_run.py"
RID=$(python3 "$LOG" start --skill create-deal \
        --trigger manual --model "<model serving this turn>" \
        --deal-ref "<property address>")
```

After the work, before handing back:

```bash
python3 "$LOG" finish --run-id "$RID" --outcome ok \
  --count tasks_created=<n> --count drafts_created=<n> --count dates_set=<n> \
  --action fub.create_deal --action fub.create_task --action fub.add_tag --action gcal.create_event \
  --output-ref fub:deal:<id> \
  --note "<anything surprising, or a judgment call you made>"
```

Record every FUB write you performed. This skill is the one with the most write surface, so its `actions` list is the closest thing you have to proof the additive-only promise held.

A refusal you were *supposed* to make — two plausible acceptance dates, an address that already
has a deal — is `--outcome blocked`, not `error`. Those are the skill working correctly, and
counting them as failures would hide the thing you actually want to measure.

Log the run even when it fails or you stopped to ask — `--outcome error` or `blocked`.
A skipped record makes the numbers flatter the skill. And never let a logging failure
block the work: if the script errors, say so and carry on.
