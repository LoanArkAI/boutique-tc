# Boutique TC plugin

Transaction-coordination assistant for **The Boutique Real Estate Group**. It turns an accepted
contract into a fully set-up Follow Up Boss deal, drafts the transaction emails, answers what's
still missing on a file, runs the daily sweep and inbox watch, keeps a live pipeline board, and
learns McKenna's email voice over time. Additive to FUB, drafts-only outbound, broker signs off.

- **Setup:** [`INSTALL.md`](INSTALL.md) — dependencies, connectors, Executor + FUB key, scheduled tasks.
- **Source of truth:** the Boutique TC Playbook (in the `ca-rpa-processor` repo).
- **Working on the skills:** [`docs/skill-ops.md`](docs/skill-ops.md) — how we version, measure, audit and tune them.

## Documents & previews

GitHub shows these HTML files as source, not rendered. Two rendered previews are available:
**GitHub Pages** (org-private — visible to LoanArkAI members who are signed in to GitHub) and the
**claude.ai artifact** (private — the owner must Share it per-person; use this for McKenna/Raj if
they aren't GitHub org members).

| Document | Source file | GitHub Pages (org-private) | claude.ai artifact |
|---|---|---|---|
| **Setup Guide** (checklist) | [`docs/install-guide.html`](docs/install-guide.html) | https://fictional-carnival-r254m26.pages.github.io/install-guide.html | https://claude.ai/artifact/BrfXUzzQ7ZsTgga8TftELd |
| **How-to Guide** (SOP) | [`docs/how-to-guide.html`](docs/how-to-guide.html) | https://fictional-carnival-r254m26.pages.github.io/how-to-guide.html | https://claude.ai/artifact/WgTqTfouEF74TrQ7qmFAVF |
| **Pipeline Board** (dashboard) | [`docs/pipeline-board.html`](docs/pipeline-board.html) | *excluded — carries client data* | https://claude.ai/artifact/2Gf2CkDn5a8DmPLwz3W11A |

> **The Pipeline Board is excluded from GitHub Pages on purpose** — its source carries real
> client data, so it is never served on the Pages site (see `docs/_config.yml`). Its only
> rendered home is the private claude.ai artifact above.

## Skills

| Skill | What it does |
|---|---|
| `create-deal` | Accepted contract → a fully set-up FUB deal (dates, tags, tasks); also updates an existing deal |
| `dashboard` | Refresh the Pipeline Board artifact from FUB (read-only) |
| `daily-sweep` | Morning/afternoon reconcile + one digest; also refreshes the board |
| `inbox-watch` | Match new arrivals to deals and surface them (never auto-close) |
| `whats-missing` | What's blocking a deadline on one file |
| `draft-emails` | Draft the transaction emails from the `TBREG \|` templates (drafts only); applies learned voice rules |
| `feedback-loop` | Learn McKenna's voice from draft-vs-sent; maintain the shared voice-rules file |
| `setup` | First-run: connectors, FUB key, and the three scheduled tasks |

## How Follow Up Boss is reached

Through the **Executor** MCP (`.mcp.json` ships the endpoint), which holds the FUB API key in its
own vault — the key never enters Cowork, a prompt, an artifact, or this repo. See
[`references/executor-fub.md`](references/executor-fub.md) and [`executor/fub-openapi.json`](executor/fub-openapi.json).

## Guardrails

- Additive to FUB — never edits or deletes existing client or deal data.
- Drafts only outbound — every email is left for a human to send.
- The FUB key stays in the Executor vault — never printed, logged, or committed.
- Broker (Caroline) signs off at the end.

## Working on the skills

The skills are versioned software and are measured like it —
[`docs/skill-ops.md`](docs/skill-ops.md) is the framework:

- **Version** — `version:` in every `SKILL.md`, semver defined for prompts, one skill per
  behavior-changing commit, tagged `<skill>/v<semver>`, hypothesis in [`CHANGELOG.md`](CHANGELOG.md).
- **Instrument** — every run writes a record via [`scripts/log_run.py`](scripts/log_run.py).
  Full detail stays local in `runs/` (client data, gitignored); a de-identified line lands
  in [`metrics/runs.jsonl`](metrics/README.md), stamped with the skill version, git SHA and
  served model — so quality can be joined to the change that caused it.
- **Audit** — read the transcript against the skill's intent, not just its output.
- **Tune** — phrasing follows the model; the served model is recorded because it moves on its own.
- **Regenerate** — author new skills with `skill-creator` rather than by hand.

Adapted from [@agentic.james](https://www.tiktok.com/t/ZP8TdLJpD/)'s five tips for agent skills.
