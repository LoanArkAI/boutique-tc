---
name: dashboard
version: 1.1.0
description: >-
  Refresh the Boutique Pipeline Board — the live transaction dashboard McKenna and Raj open
  to see every open file on its escrow clock, what's missing, and the closed-volume trend.
  Use whenever someone says "refresh the pipeline board", "update the dashboard", "refresh
  the board", "rebuild the pipeline board", or asks for the current state of the pipeline as
  a page. It re-pulls the open deals from Follow Up Boss through Executor, recomputes the
  board's data, and republishes the existing artifact in place — same URL, so the link the
  team has bookmarked always shows current data. It is READ-ONLY on Follow Up Boss; it never
  writes a deal, task, or field. The daily-sweep skill calls this at the end of each run.
---

# Refresh the Pipeline Board (The Boutique)

The board is a published artifact that **cannot reach Follow Up Boss on its own** — a page's
runtime connectors reach claude.ai connectors, and FUB lives behind Executor. So the board
carries a snapshot of the data baked into the page, and this skill is what refreshes that
snapshot: pull FUB, rebuild the data block, republish the same artifact. Read-only on FUB.

**The artifact URL is fixed** — always republish to this one so the team's link keeps working:

```
https://claude.ai/artifact/2Gf2CkDn5a8DmPLwz3W11A
```

**The page shell is fixed too.** The HTML, CSS, and all the rendering logic live in
`docs/pipeline-board.html` in this plugin. You only ever regenerate the JSON in the
`<script id="payload">` block — never rewrite the markup. That keeps every refresh cheap and
the design stable.

## The flow

### 1. Pull the data from FUB (via Executor, read-only)
Through the **Executor** MCP (`search` then `invoke` — see `../../references/executor-fub.md`;
no local key). Gather:
- **Open deals** — `deals.listDeals`, all deals in transaction stages (In Escrow, Coming Soon,
  Active (on MLS), Temp (start)). Exclude Closed and Canceled from `open`, but keep a **count**
  of Canceled and the **count + summed price** of Closed for the KPI/chart.
- **Per deal**, read the fields the board uses (below). `deals.getDeal` if the list doesn't
  carry them all.
- **People** — for each deal's primary contact, `people.listPeople` / the deal's people to get
  name, last activity, assigned agent, whether a phone and email are on file, unsub status.
- **Tasks** — count open tasks on contacts attached to open deals (`tasks.listTasks`), and the
  account-wide open-task total, for the backlog line.
- **Closed by month** — sale price of Closed deals grouped by close month, last ~8 months.

### 2. Build the payload — exact shape the page expects
Assemble one JSON object. Field names and types must match, or the page renders blank:

```json
{
  "asOf": "YYYY-MM-DD",
  "account": "The Boutique Real Estate Group",
  "open": [
    {
      "id": 0, "name": "123 Main St", "price": 0,
      "pipeline": "Sellers" | "Buyers",
      "stage": "In Escrow" | "Coming Soon" | "Active (on MLS)" | "Temp (start)",
      "enteredStageAt": "ISO-8601", "createdAt": "ISO-8601",
      "projectedCloseDate": "ISO-8601" | null,
      "mutualAcceptanceDate": "ISO-8601" | null,
      "dueDiligenceDate": "ISO-8601" | null,
      "earnestMoneyDueDate": "ISO-8601" | null,
      "customCR2Date": "ISO-8601" | null,
      "finalWalkThroughDate": "ISO-8601" | null,
      "possessionDate": "ISO-8601" | null,
      "commission": 0,
      "people": [ { "id": 0, "name": "Client Name" } ],
      "users": [ "Agent Name" ]
    }
  ],
  "closedByMonth": [ { "m": "YYYY-MM", "n": 0, "v": 0 } ],
  "canceled": 0,
  "closedTotal": { "n": 0, "v": 0 },
  "contacts": {
    "<personId>": {
      "name": "Client Name", "lastActivity": "YYYY-MM-DD",
      "assignedTo": "Agent Name", "phone": true, "email": true, "unsub": false
    }
  },
  "openTasksOnLiveDeals": 0,
  "totalOpenTasksAccount": 0
}
```

Rules that keep the board honest:
- **Dates stay as the record has them.** Never invent a `mutualAcceptanceDate` or
  `projectedCloseDate` — leave it `null`. Blank is what drives the "provisional clock" and the
  missing-field table; a guessed date would hide the very gap the board exists to show.
- **`users`** is the deal's assigned users by name; the board shows the last one as the agent.
- **`contacts`** is keyed by the numeric `personId` used in `open[].people[].id`.
- Money is a plain number (no `$`, no commas). `commission` 0 or null both read as "commission $0".

### 3. Republish the artifact (same URL)
Take `docs/pipeline-board.html`, replace **only** the contents of the
`<script id="payload" type="application/json">…</script>` block with the new JSON, and publish
to the fixed URL above. Do not touch the markup, CSS, or the second `<script>`. Keep the
title "Boutique Pipeline Board"; omit `icon` (it's a redeploy).

### 4. Hand back
Say it's refreshed, give the link, and note anything that couldn't be pulled (a connector that
was down, a field FUB didn't return) so the numbers are never implied to be more complete than
they are.

## Non-negotiables
- **Read-only on Follow Up Boss.** This skill never creates or edits a deal, task, field, or
  tag. It only reads and republishes a page.
- **Same URL, fixed shell.** Always the artifact URL above; only the payload JSON changes.
- **No invented dates or values.** Missing stays missing — that's the signal.
- **Cost.** A full refresh is ~50–75k tokens (it re-emits the page). The daily-sweep runs it
  twice a day; on demand is fine, but don't loop it.

## Log the run

This skill produces output, so it records what it did — see
[`../../references/run-logging.md`](../../references/run-logging.md) for the full contract.

Before starting the work:

```bash
LOG="${CLAUDE_PLUGIN_ROOT:-../..}/scripts/log_run.py"
RID=$(python3 "$LOG" start --skill dashboard \
        --trigger manual --model "<model serving this turn>")
```

After the work, before handing back:

```bash
python3 "$LOG" finish --run-id "$RID" --outcome ok \
  --count deals_rendered=<n> \
  --action artifact.publish \
  --output-ref artifact:<url-id> \
  --note "<anything surprising, or a judgment call you made>"
```

Read-only on FUB, so `artifact.publish` is the only write. Pass `--called-by daily-sweep`
when the sweep triggered the refresh rather than a person.

Log the run even when it fails or you stopped to ask — `--outcome error` or `blocked`.
A skipped record makes the numbers flatter the skill. And never let a logging failure
block the work: if the script errors, say so and carry on.
