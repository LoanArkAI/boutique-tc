# Install & Setup — Boutique TC plugin

This is the one-time setup runbook for the Boutique transaction-coordination assistant. Do it
once per person, on the computer that person will use. Plan ~15 minutes. When you're done,
McKenna can say "Create a new deal" (or drop in a contract) and everything downstream works.

> **Who runs what.** Day to day, McKenna works in **Claude Cowork** — she never touches code,
> a terminal, or the Follow Up Boss API key. This doc is the setup she (or whoever installs for
> her) walks through once.

---

## 1. What you need first (accounts & access)

Before installing, make sure these exist — the plugin connects to them, it doesn't create them:

| Dependency | Why the plugin needs it | Who provides it |
|---|---|---|
| **Claude** with **Cowork** + **connectors** | where McKenna works and where the connectors live | her Claude account |
| **Follow Up Boss** account for The Boutique | the system of record — deals, tasks, contacts, templates | Raj / FUB admin |
| **A Follow Up Boss API key** | lets the plugin read/write FUB (via Executor, never exposed) | FUB → Admin → API |
| **Executor** account (executor.sh) | the vault that holds the FUB key so it never enters Cowork | free tier is fine (≤3 users) |
| **Dropbox** "TBREG" folder | contracts in, the shared email-voice-rules file, filed docs | Raj / existing folder |

The FUB **Part A** config (the CR2 field and the 12 `TBREG |` email templates) is already loaded
in Raj's Follow Up Boss — you don't redo it.

---

## 2. Install the plugin

The plugin lives at **`dstolan/boutique-tc-plugin`** (GitHub, private). Installing it ships the
**skills** and points Claude at the **Executor MCP endpoint** — but *not* the connectors or the
scheduled tasks (those are per-person and are steps 3–5 below).

- Install it from the plugin marketplace / plugin manager in the Claude app the way you install
  any Claude plugin, selecting **boutique-tc**.
- It ships:
  - **7 skills** — `create-deal`, `dashboard`, `daily-sweep`, `inbox-watch`, `whats-missing`,
    `draft-emails`, `feedback-loop`, plus `setup`.
  - **`.mcp.json`** — the Executor endpoint `https://executor.sh/tbreg/mcp`
    (no key in it; each person authenticates as themselves in step 3).

---

## 3. Connect the Claude connectors (dependencies)

In Claude's **connector settings**, connect each of these. The skills read from them, so a
missing connector means that part goes dark.

| Connector | Required? | Used for |
|---|---|---|
| **Gmail** | **Required** | reading deal email, leaving drafts, the feedback loop (draft vs. sent) |
| **Google Calendar** | Required | the shared **"Escrow Deadlines"** calendar (CR1 / CR2 / COE) |
| **Dropbox** | Required | the TBREG contracts folder + the `email-voice-rules.md` the loop maintains |
| **DocuSign** | Recommended | envelope completions as evidence in the sweep |
| **Google Drive** | Recommended | filed working docs as evidence |

> **Privacy:** these are personal connections. Each person connects their own; nothing is
> shared through the plugin.

---

## 4. Connect Executor + add the Follow Up Boss key (once)

Follow Up Boss is reached through the **Executor** MCP, which holds the key in its own vault —
**the key never enters Cowork, a prompt, an artifact, or this repo.**

1. **Connect Executor.** When the `executor` MCP connects, sign in to the Executor workspace
   (the plugin already ships the endpoint; you authenticate as yourself). Connections are
   per-user, so each person does this once.
2. **Add the FUB key to Executor's vault, once.** In Executor, add/confirm the
   `follow_up_boss_boutique_subset` connection as an **API-key header**:
   - **Header name:** `Authorization`
   - **Prefix:** *(leave empty)*
   - **Value:** `Basic <base64>` — where `<base64>` is the base64 encoding of
     `THE_FUB_KEY:` (the key followed by a **colon**, with a blank password).
   - Example shape only (not a real key): `Basic ZmthX3lvdXJfa2V5X2hlcmU6`
   - Common gotcha: the "Expired/401" error is almost always a trailing-space or a missing
     colon — the value must be the full `Basic <base64 of key + ":">`, prefix empty.
3. **Verify.** Run the `getIdentity` health check (or `search` → `invoke getIdentity`). A **200**
   returning `account: The Boutique Real Estate Group` means it's wired.

The OpenAPI subset Executor uses is in `executor/fub-openapi.json`; the call pattern is in
`references/executor-fub.md`.

---

## 5. Register the scheduled tasks

Run the **`setup`** skill ("set up the Boutique plugin"). It confirms the connectors and the FUB
key, then registers **three** local scheduled tasks on this machine:

| Task | Runs | Does |
|---|---|---|
| **TBREG — Daily Sweep** | 7:27am & 4:27pm | reconcile files, draft the digest, **refresh the Pipeline Board** |
| **TBREG — Inbox Watch** | every 2h, business hours | match new arrivals to deals, surface (never auto-close) |
| **TBREG — Feedback Loop** | 9am on the 1st of each month | learn McKenna's voice from draft-vs-sent, update the Dropbox rules |

After they're created, click **Run now** once on each (Scheduled sidebar) to pre-approve the
connector/Executor prompts so future runs don't pause.

> **One limitation:** these are local scheduled tasks — **the Claude app must be open** for them
> to fire (a missed window runs at next launch). True always-on is a separate infrastructure
> conversation.

---

## 6. The Pipeline Board

The live dashboard (escrow clocks, what's missing, copy-and-paste commands):

```
https://claude.ai/artifact/2Gf2CkDn5a8DmPLwz3W11A
```

It's **private** — the owner must **Share** it (from the artifact's Share menu) with McKenna and
Raj before they can open the link. It refreshes on the daily sweep, or on demand: "Refresh the
pipeline board."

---

## Dependency checklist (quick reference)

- [ ] Follow Up Boss account + API key issued
- [ ] Plugin **boutique-tc** installed
- [ ] Connectors: Gmail ✱, Google Calendar ✱, Dropbox ✱, DocuSign, Google Drive
- [ ] Executor connected, FUB key in the vault, `getIdentity` returns 200
- [ ] `setup` run → 3 scheduled tasks visible, **Run now** clicked on each
- [ ] Pipeline Board shared with McKenna & Raj

✱ = required.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Executor "Expired" / 401 | Value must be `Basic <base64 of key + ":">`, **prefix empty**, no trailing space |
| A skill says a connector is missing | Connect it in Claude connector settings, then re-run |
| Scheduled task didn't run | The Claude app was closed at the window — it runs at next launch |
| `getIdentity` returns a different account | Wrong key in the vault — use The Boutique's FUB key, not another org's |
| Board link won't open for McKenna | Share the artifact with her from its Share menu |

## Guardrails (what the plugin will never do)

- **Additive to Follow Up Boss** — it creates deals, tasks, tags; it never edits or deletes
  existing client or deal data.
- **Drafts only outbound** — every email is left as a draft for a human to send.
- **The FUB key stays in the Executor vault** — never printed, logged, or placed in a prompt,
  artifact, or this repo.
- **Broker signs off** — the file goes to Caroline at the end; the plugin records nothing as
  broker-approved.
