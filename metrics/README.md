# metrics/

`runs.jsonl` — one line per skill run, committed.

Every line carries `skill`, `skill_version`, `git_sha` and `model` alongside the outcome
and the human-correction counts. That join key is the point: it makes "did v1.2.0
actually beat v1.1.0" a query rather than a hunch.

Contains identifiers, enums and numbers only — never prose, names or addresses.
`scripts/log_run.py` enforces this with an allowlist, so a new field is excluded until
someone deliberately adds it.

```bash
# corrections per skill version
jq -s 'group_by(.skill, .skill_version)[] | {skill: .[0].skill,
       v: .[0].skill_version, runs: length,
       mean_edits: (map(.human_edits // 0) | add / length)}' metrics/runs.jsonl

# runs that deviated from intent
jq -c 'select(.audit_verdict | test("deviation"))' metrics/runs.jsonl

# non-reproducible runs (uncommitted skill edits)
jq -c 'select(.git_dirty)' metrics/runs.jsonl
```

See [`../docs/skill-ops.md`](../docs/skill-ops.md) §2.
