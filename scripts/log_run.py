#!/usr/bin/env python3
"""Record one skill run.

Writes two artifacts per run:

  runs/<skill>/<ts>-<run_id>.json   full record, gitignored (may contain client data)
  metrics/runs.jsonl                de-identified one-liner, COMMITTED

The committed line carries only identifiers, enums and numbers -- never prose,
names or addresses. That split is what lets the metrics file live in git next
to the skill versions it measures without leaking a client's file.

Usage
  log_run.py start  --skill create-deal --trigger manual [--deal-ref fub:123]
  log_run.py finish --run-id <id> --outcome ok --count tasks_created=14 \
                    --action fub.create_deal --output-ref fub:deal:123
  log_run.py amend  --run-id <id> --human-edits 3 --edit-distance 0.12 \
                    --audit-verdict aligned
"""
import argparse, hashlib, json, os, pathlib, re, subprocess, sys, uuid
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS, METRICS = ROOT / "runs", ROOT / "metrics" / "runs.jsonl"

# Fields allowed into the committed metrics line. Anything not listed stays local.
METRIC_KEYS = {
    "run_id", "ts", "ended_at", "duration_s", "skill", "skill_version",
    "plugin_version", "git_sha", "git_dirty", "model", "trigger", "called_by", "outcome",
    "deal_ref", "counts", "actions", "human_edits", "edit_distance",
    "audit_verdict", "audit_deviations", "error_class",
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(*args, default=""):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return default


def skill_version(skill):
    """Read `version:` out of the skill's SKILL.md frontmatter."""
    p = ROOT / "skills" / skill / "SKILL.md"
    if not p.exists():
        sys.exit(f"no such skill: {skill} ({p} missing)")
    head = p.read_text(encoding="utf-8").split("---")[1] if "---" in p.read_text(encoding="utf-8") else ""
    m = re.search(r"^version:\s*['\"]?([0-9]+\.[0-9]+\.[0-9]+)['\"]?", head, re.M)
    if not m:
        sys.exit(f"{skill} has no `version:` in SKILL.md frontmatter -- add one before logging runs")
    return m.group(1)


def plugin_version():
    try:
        return json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    except Exception:
        return "unknown"


def deal_ref(raw):
    """Opaque, stable, non-reversible. Never the address."""
    if not raw:
        return None
    if re.fullmatch(r"[a-z]+:[0-9]+", raw or ""):
        return raw                      # already an opaque system id
    return "h:" + hashlib.sha256(raw.strip().lower().encode()).hexdigest()[:12]


def path_for(run_id, skill=None):
    if skill:
        return RUNS / skill / f"{run_id}.json"
    hits = list(RUNS.glob(f"*/{run_id}.json"))
    if not hits:
        sys.exit(f"no run record for {run_id}")
    return hits[0]


def load(run_id):
    p = path_for(run_id)
    return p, json.loads(p.read_text(encoding="utf-8"))


def save(p, rec):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit_metric(rec):
    """Rewrite this run's line in metrics/runs.jsonl, allowlist-filtered."""
    line = {k: v for k, v in rec.items() if k in METRIC_KEYS and v not in (None, {}, [])}
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    kept = [l for l in (METRICS.read_text(encoding="utf-8").splitlines()
                        if METRICS.exists() else [])
            if l.strip() and json.loads(l).get("run_id") != rec["run_id"]]
    kept.append(json.dumps(line, sort_keys=True))
    METRICS.write_text("\n".join(kept) + "\n", encoding="utf-8")


def kv(pairs, numeric=False):
    out = {}
    for item in pairs or []:
        k, _, v = item.partition("=")
        out[k.strip()] = (float(v) if "." in v else int(v)) if numeric and v.strip() else v.strip()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="open a run record")
    s.add_argument("--skill", required=True)
    s.add_argument("--trigger", default="manual",
                   choices=["manual", "scheduled", "chained", "test"])
    s.add_argument("--model", default=os.environ.get("CLAUDE_MODEL", "unknown"),
                   help="the model actually SERVING the turn, not the one configured")
    s.add_argument("--deal-ref", help="opaque system id (fub:123) or any string, which is hashed")
    s.add_argument("--called-by", help="skill that chained into this one")
    s.add_argument("--input", action="append", metavar="K=V",
                   help="local-only; never reaches metrics/")

    f = sub.add_parser("finish", help="close a run record")
    f.add_argument("--run-id", required=True)
    f.add_argument("--outcome", required=True,
                   choices=["ok", "partial", "blocked", "error"])
    f.add_argument("--count", action="append", metavar="K=N",
                   help="numeric only, e.g. tasks_created=14 -- these DO reach metrics/")
    f.add_argument("--action", action="append",
                   help="bare verb, no args, e.g. fub.create_task")
    f.add_argument("--output-ref", action="append", help="pointer, not payload")
    f.add_argument("--error-class", help="short enum-ish label, no stack trace")
    f.add_argument("--note", help="local-only free text")

    a = sub.add_parser("amend", help="attach the dependent variable once a human has reviewed")
    a.add_argument("--run-id", required=True)
    a.add_argument("--human-edits", type=int, help="# of substantive human corrections")
    a.add_argument("--edit-distance", type=float, help="0..1, draft vs. sent")
    a.add_argument("--audit-verdict",
                   choices=["aligned", "minor-deviation", "major-deviation", "unreviewed"])
    a.add_argument("--audit-deviations", type=int)
    a.add_argument("--note")

    args = ap.parse_args()

    if args.cmd == "start":
        run_id = uuid.uuid4().hex[:10]
        rec = {
            "run_id": run_id, "ts": now(),
            "skill": args.skill, "skill_version": skill_version(args.skill),
            "plugin_version": plugin_version(),
            "git_sha": git("rev-parse", "--short", "HEAD", default="unknown"),
            "git_dirty": bool(git("status", "--porcelain")),
            "model": args.model, "trigger": args.trigger,
            "called_by": args.called_by,
            "deal_ref": deal_ref(args.deal_ref),
            "inputs": kv(args.input), "outcome": None,
            "audit_verdict": "unreviewed",
        }
        save(path_for(run_id, args.skill), rec)
        emit_metric(rec)
        print(run_id)

    elif args.cmd == "finish":
        p, rec = load(args.run_id)
        rec["ended_at"] = now()
        try:
            rec["duration_s"] = round(
                (datetime.fromisoformat(rec["ended_at"])
                 - datetime.fromisoformat(rec["ts"])).total_seconds())
        except Exception:
            pass
        rec["outcome"] = args.outcome
        rec["counts"] = kv(args.count, numeric=True)
        rec["actions"] = sorted(set(args.action or []))
        rec["output_refs"] = args.output_ref or []
        if args.error_class:
            rec["error_class"] = args.error_class
        if args.note:
            rec.setdefault("notes", []).append(args.note)
        save(p, rec)
        emit_metric(rec)
        print(f"{args.run_id} {rec['skill']} v{rec['skill_version']} -> {args.outcome}")

    else:  # amend
        p, rec = load(args.run_id)
        for k in ("human_edits", "edit_distance", "audit_verdict", "audit_deviations"):
            v = getattr(args, k)
            if v is not None:
                rec[k] = v
        if args.note:
            rec.setdefault("notes", []).append(args.note)
        rec["amended_at"] = now()
        save(p, rec)
        emit_metric(rec)
        print(f"{args.run_id} amended")


if __name__ == "__main__":
    main()
