---
name: draft-emails
version: 1.1.0
description: >-
  Draft the transaction emails for a Boutique Real Estate Group file — accepted-offer
  intros to escrow / lender / listing agent, the home-warranty order to Staci at FNF,
  the disclosure package to the buyer, final-walkthrough scheduling, commission
  confirmation, and the generic doc request / reminder / send notes. Use this whenever
  McKenna or Raj says "draft the intro emails", "email escrow/the lender/the other agent",
  "order the warranty", "send the disclosures", "chase [doc]", or needs any transaction
  email written for a specific file. It personalizes the brokerage's TBREG templates to
  the deal and leaves everything as a DRAFT for a human to review and send — it never
  sends. Trigger it even if they don't name a template; picking the right one is its job.
---

# Draft Emails (The Boutique — FUB templates → drafts)

Write the right transaction email for a file, fast, in the brokerage's own voice — and
stop at the draft. Nothing here reaches escrow, a lender, the other side, or a client
without Raj or McKenna sending it themselves. That guardrail exists because a transaction
email that goes out wrong (a wrong wire instruction, a premature disclosure) is not
recoverable, and because these are Raj's relationships to speak into, not the system's.

**Source of the voice and templates:** the 12 `TBREG |` templates already in Follow Up
Boss, built from McKenna's real emails. The playbook's communications section
(`docs/playbook/boutique-tc-playbook.md`, §6) lists which template fits which moment.

## Non-negotiables (why)
- **Draft only. Never send.** Leave every email in drafts for a human. Outbound to anyone
  outside the brokerage is Raj's to send.
- **No wire instructions, ever.** If an email would touch wiring or payment details, don't
  write them — flag that escrow must be verified by phone on a known number. Wire fraud is
  the single biggest loss vector in this business.
- **Real values only.** Pull names, address, dates, and amounts from the FUB deal / the
  human. If a value isn't known, leave a clearly-marked `[blank]` rather than inventing it.

## Pick the template
Match the moment to a `TBREG |` template (`GET /templates`, filter by the `TBREG` prefix):

| Moment | Template |
|---|---|
| File just opened, to the client | Listing Intro (Sellers) / Accepted Offer Intro — Buyer |
| Open escrow, to escrow / lender / listing agent | Accepted Offer Intro — Escrow / — Lender; New Transaction Intro + Doc Request — Listing Agent |
| Order home warranty (buyer-paid) | Warranty Order (to Staci/FNF) |
| Send disclosures to the buyer | Disclosure Package to Buyer |
| Schedule the final walkthrough | Final Walkthrough Scheduling |
| Confirm commission before returning to escrow | Commission Confirmation (to Agent) |
| Chase / remind / send any document | Docs Request / Docs Reminder / Send Docs (Any) |

## The flow
1. **Identify the file** — property address / client. Read the FUB deal for the real values
   (names, dates, price, escrow, agent) via the **Executor** MCP (`deals.listDeals` /
   `deals.getDeal`, `templates.listTemplates` — see `../../references/executor-fub.md`; no
   local key). If something you need isn't on the deal, ask.
2. **Choose the template(s)** from the table. If several apply (opening a file often needs
   escrow + lender + listing-agent intros at once), draft them as a set.
3. **Apply the learned voice rules** — read `Dropbox › TBREG › email-voice-rules.md` if it
   exists and follow every rule in it. This file is maintained by the `feedback-loop` skill
   from McKenna's own edits (greeting, sign-off, phrases she always cuts or adds), so honoring
   it is what makes each draft need less editing than the last. If the file is missing, skip
   this — the loop just hasn't run yet.
4. **Personalize** — fill the `[bracketed]` placeholders from the deal. For the Staci
   warranty email, that's buyer names, coverage, and price. Keep McKenna's warm
   Concierge-Team voice; don't rewrite the template's substance.
5. **Leave as drafts** — in Gmail (or hand the text back if no draft access), addressed but
   unsent. Tell the human which drafts are waiting and to whom.
6. **Say what you couldn't fill** — list any `[blank]` you left and why, so the human
   completes it before sending.

## When to stop and ask
- The email would include wiring/payment details → don't; flag phone verification.
- A recipient address is unknown or came from an untrusted forwarded email → confirm with
  the human before addressing it.
- The deal's values look stale or contradict what the human said → ask, don't guess.

## Log the run

This skill produces output, so it records what it did — see
[`../../references/run-logging.md`](../../references/run-logging.md) for the full contract.

Before starting the work:

```bash
LOG="${CLAUDE_PLUGIN_ROOT:-../..}/scripts/log_run.py"
RID=$(python3 "$LOG" start --skill draft-emails \
        --trigger manual --model "<model serving this turn>" \
        --deal-ref "<property address>")
```

After the work, before handing back:

```bash
python3 "$LOG" finish --run-id "$RID" --outcome ok \
  --count drafts_created=<n> --count templates_used=<n> \
  --action gmail.create_draft \
  --output-ref gmail:draft:<id> \
  --note "<anything surprising, or a judgment call you made>"
```

`feedback-loop` amends these records later with how far McKenna's sent version drifted from
the draft. That number is the dependent variable for this skill — it is the whole reason
this one gets logged — so the run record has to exist for it to attach to.

Log the run even when it fails or you stopped to ask — `--outcome error` or `blocked`.
A skipped record makes the numbers flatter the skill. And never let a logging failure
block the work: if the script errors, say so and carry on.
