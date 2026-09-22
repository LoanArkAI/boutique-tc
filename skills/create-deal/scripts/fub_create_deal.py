#!/usr/bin/env python3
"""Create ONE Follow Up Boss deal, additively, from a confirmed spec.

Safety model (why this shape):
- Dry-run is the DEFAULT. Nothing is written unless you pass --commit. The human sees the
  exact payload first, because a wrong write to a live book of business is unrecoverable.
- Only POST. This script has no code path that updates or deletes an existing record.
- A refused date is simply absent from the spec's "dates" object; we never invent one.
- On the first failed call it stops and reports; it does not half-finish silently.

The SKILL.md flow builds the spec from the Q&A + RPA JSON, gets a human yes, then calls:
    python fub_create_deal.py --spec deal.json            # dry run, prints the plan
    python fub_create_deal.py --spec deal.json --commit    # actually writes

Spec file shape (all synthetic):
{
  "name": "123 Example St — Buyer (Client Last)",
  "pipelineName": "Buyers",
  "stageName": "In Escrow",
  "price": 850000,
  "personName": "Jane Client",           // optional; links/creates the contact
  "dates": {                              // omit any refused date entirely
    "mutualAcceptanceDate": "2026-10-01",
    "dueDiligenceDate": "2026-10-08",
    "customCR1": "2026-10-08",
    "customCR2Date": "2026-10-15",
    "projectedCloseDate": "2026-11-02"
  },
  "tags": ["side:buy", "cond:hoa", "cond:warranty"],
  "tasks": [
    {"name": "16 AVID — request from both agents", "dueDate": "2026-10-03", "type": "Closing"},
    {"name": "11 Home warranty — order via Staci (FNF)", "dueDate": "2026-10-08", "type": "Closing"}
  ]
}
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = "https://api.followupboss.com/v1"


def load_key(env_path: str) -> str:
    """Read FUB_API_KEY from a .env file without printing it."""
    txt = open(env_path, encoding="utf-8-sig").read()
    # Prefer NEW_FUB_API_KEY: the working key. A stale FUB_API_KEY may also sit in the file.
    for pat in (r"NEW_FUB_API_KEY\s*=\s*(fka_[A-Za-z0-9]+)", r"\bFUB_API_KEY\s*=\s*(fka_[A-Za-z0-9]+)"):
        m = re.search(pat, txt)
        if m:
            return m.group(1)
    sys.exit(f"No fka_ FUB key found in {env_path}")


def call(key: str, method: str, path: str, body: dict | None, commit: bool):
    """A single FUB call. In dry-run, prints intent and returns a stub."""
    if method != "GET" and not commit:
        print(f"  [dry-run] {method} {path}")
        print("    payload:", json.dumps(body, indent=2)[:1000])
        return {"_dryrun": True}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", "Basic " + base64.b64encode((key + ":").encode()).decode())
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"FUB {method} {path} failed: {e.code} {e.read()[:300].decode(errors='replace')}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Create one FUB deal additively from a confirmed spec.")
    ap.add_argument("--spec", required=True, help="Path to the confirmed deal spec JSON")
    ap.add_argument("--env", default=os.path.expanduser(r"~/Desktop/.env.raj"))
    ap.add_argument("--commit", action="store_true", help="Actually write (default: dry run)")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    key = load_key(args.env)

    if not args.commit:
        print("DRY RUN — nothing will be written. Re-run with --commit after the human confirms.\n")

    # 1. Duplicate guard: warn if a deal with this exact name already exists.
    existing = call(key, "GET", "/deals?limit=100", None, args.commit)
    if isinstance(existing, dict):
        names = {d.get("name") for d in existing.get("deals", [])}
        if spec["name"] in names:
            sys.exit(f"STOP: a deal named {spec['name']!r} already exists. Confirm intent before creating another.")

    # 2. Create the deal with its date fields (additive POST).
    # FUB requires numeric pipelineId + stageId (names are rejected). See fub-field-map.md.
    deal_body = {k: spec[k] for k in ("name", "pipelineId", "stageId", "price") if k in spec}
    deal_body.update(spec.get("dates", {}))
    deal = call(key, "POST", "/deals", deal_body, args.commit)
    deal_id = deal.get("id", "<dry-run>")
    print(f"deal: {deal_body.get('name')} -> id {deal_id}")

    # 3. Tags — applied to the linked person if named (tags are created on use).
    tags = spec.get("tags", [])
    if tags and spec.get("personName"):
        print(f"tags to apply to {spec['personName']}: {tags}")
        # Applying tags requires the person id; the SKILL flow resolves/creates the contact
        # and PATCHes tags there. Left to the flow so this script stays create-only.

    # 4. Tasks, each with its due date (additive POST).
    # FUB tasks attach to a PERSON (personId), not a deal — there is no dealId field.
    # The SKILL flow resolves/creates the contact and passes personId in the spec.
    person_id = spec.get("personId")
    for t in spec.get("tasks", []):
        body = {"name": t["name"], "type": t.get("type", "Closing")}
        if t.get("dueDate"):
            body["dueDate"] = t["dueDate"]
        if person_id:
            body["personId"] = person_id
        call(key, "POST", "/tasks", body, args.commit)
    print(f"tasks: {len(spec.get('tasks', []))} planned")

    print("\nDone." if args.commit else "\nDry run complete. Review, then re-run with --commit.")


if __name__ == "__main__":
    main()
