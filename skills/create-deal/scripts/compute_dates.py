#!/usr/bin/env python3
"""Deterministic contract-deadline calculator for The Boutique.

Why this exists: when there's no RPA JSON export, the create-deal skill still needs the
contingency dates computed the SAME way every time — not by in-context arithmetic, which can
miscount days or miss a weekend/holiday roll. A wrong contingency-removal date can blow a
contingency, so this math is done by code and then confirmed by a human.

Rules (Boutique TC Playbook §3):
- Day 0 = binding acceptance (the human supplies it; if ambiguous, that's a refusal upstream).
- Count all CALENDAR days from Day 0.
- If a deadline lands on a weekend or US federal holiday, roll FORWARD to the next business day.
- Defaults: loan 14, appraisal 14, investigation 7, close of escrow 30 (override per contract).
- CR1 = latest of the non-loan/appraisal removals (typically investigation).
- CR2 = latest of loan and appraisal.
- Final walkthrough = close of escrow − 5 days (then rolled).

Usage:
  python compute_dates.py --acceptance 2026-10-01 --loan 14 --appraisal 14 --investigation 7 --coe 30
Outputs JSON the skill folds into the deal spec. Every date carries the raw (pre-roll) date
so the arithmetic stays checkable, and the human confirms before anything is written.
"""
import argparse
import datetime as dt
import json


def _nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year, month, weekday):
    d = dt.date(year, month, 28) + dt.timedelta(days=4)
    d = d.replace(day=1) - dt.timedelta(days=1)  # last day of month
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def federal_holidays(year):
    """US federal holidays with weekend-observed shifting (Sat->Fri, Sun->Mon)."""
    fixed = {
        dt.date(year, 1, 1): "New Year's Day",
        dt.date(year, 6, 19): "Juneteenth",
        dt.date(year, 7, 4): "Independence Day",
        dt.date(year, 11, 11): "Veterans Day",
        dt.date(year, 12, 25): "Christmas Day",
    }
    floating = {
        _nth_weekday(year, 1, 0, 3): "MLK Day",
        _nth_weekday(year, 2, 0, 3): "Washington's Birthday",
        _last_weekday(year, 5, 0): "Memorial Day",
        _nth_weekday(year, 9, 0, 1): "Labor Day",
        _nth_weekday(year, 10, 0, 2): "Columbus Day",
        _nth_weekday(year, 11, 3, 4): "Thanksgiving",
    }
    obs = set()
    for d in fixed:
        if d.weekday() == 5:
            obs.add(d - dt.timedelta(days=1))
        elif d.weekday() == 6:
            obs.add(d + dt.timedelta(days=1))
    return set(fixed) | set(floating) | obs


def _holidays_near(d):
    return federal_holidays(d.year) | federal_holidays(d.year + 1) | federal_holidays(d.year - 1)


def roll_forward(d):
    """Next business day if d is a weekend or federal holiday; else d."""
    hols = _holidays_near(d)
    while d.weekday() >= 5 or d in hols:
        d += dt.timedelta(days=1)
    return d


def _entry(acceptance, days):
    raw = acceptance + dt.timedelta(days=days)
    rolled = roll_forward(raw)
    return {"days_after_acceptance": days, "raw": raw.isoformat(), "due": rolled.isoformat(),
            "shifted_from": (raw.isoformat() if rolled != raw else None)}


def main():
    ap = argparse.ArgumentParser(description="Compute Boutique contract deadlines deterministically.")
    ap.add_argument("--acceptance", required=True, help="Binding acceptance date YYYY-MM-DD (Day 0)")
    ap.add_argument("--loan", type=int, default=14)
    ap.add_argument("--appraisal", type=int, default=14)
    ap.add_argument("--investigation", type=int, default=7)
    ap.add_argument("--coe", type=int, default=30, help="Close-of-escrow days after acceptance")
    ap.add_argument("--walkthrough-lead", type=int, default=5, help="Days before COE for final walkthrough")
    args = ap.parse_args()

    acc = dt.date.fromisoformat(args.acceptance)
    loan = _entry(acc, args.loan)
    appraisal = _entry(acc, args.appraisal)
    invest = _entry(acc, args.investigation)
    coe = _entry(acc, args.coe)
    walk_raw = dt.date.fromisoformat(coe["due"]) - dt.timedelta(days=args.walkthrough_lead)
    walk = roll_forward(walk_raw)

    # CR1 = latest of non-loan/appraisal removals (investigation here). CR2 = latest of loan/appraisal.
    cr1 = invest
    cr2 = loan if loan["due"] >= appraisal["due"] else appraisal

    out = {
        "acceptance_date": acc.isoformat(),
        "deadlines": {
            "investigation_contingency_removal": invest,
            "loan_contingency_removal": loan,
            "appraisal_contingency_removal": appraisal,
            "close_of_escrow": coe,
        },
        "fub_fields": {  # ready to fold into the deal spec's "dates"
            "mutualAcceptanceDate": acc.isoformat(),
            "dueDiligenceDate": invest["due"],
            "customCR1": cr1["due"],
            "customCR2Date": cr2["due"],
            "projectedCloseDate": coe["due"],
            "finalWalkThroughDate": walk.isoformat(),
        },
        "note": "CR1/CR2 are computed events — confirm with the agent before sending. "
                "Counters routinely change periods; verify against the executed contract.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
