# Standalone skills

Skills that ship **outside** the Boutique TC plugin, uploaded one at a time to a person's
claude.ai account (Settings → Capabilities → Skills → Upload skill).

| Skill | Upload | What it does |
|---|---|---|
| `ooo-handoff` | [`ooo-handoff.zip`](ooo-handoff.zip) | Covers McKenna while she's out of office — see [`ooo-handoff/SKILL.md`](ooo-handoff/SKILL.md) |

After editing a skill, rebuild its zip from this folder:

```bash
cd standalone-skills && rm -f ooo-handoff.zip && zip -r ooo-handoff.zip ooo-handoff
```
