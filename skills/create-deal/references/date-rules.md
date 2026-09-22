# Deadline math

When the RPA JSON export is present, trust its dates — it already applied these rules and
recorded refusals. Only compute by hand when there is no export. Either way, the human
confirms every date before it is written.

## The rules (from the Boutique TC Playbook §3)
- **Day 0 = binding acceptance** = the last signature/initial on the last accepted document
  (the RPA, or the last counter). If two dates are plausible, that is a **refusal** — ask
  the human, never pick one.
- **Count all calendar days** from Day 0.
- **Weekend / holiday roll-forward.** A deadline that lands on a weekend or a federal
  holiday moves to the next business day. (McKenna's guide applies this to the contingency
  removals; the RPA engine currently rolls only close of escrow — when the export rolled a
  date it records `shifted_from`. When computing by hand, roll all of them and say so.)
- **Default contingency periods** (only when the contract relies on the printed default —
  counters routinely change these, so read the contract first):
  - Loan: 14 days · Appraisal: 14 days · Investigation: 7 days
  - Location on the form: RPA page 2 §L (L1–L4)
- **Close of escrow** = RPA page 1 §3B — always re-check counters.

## Deriving CR1 / CR2 (TBREG grouping)
The engine emits per-contingency removals; TBREG groups them into two removal events:
- **CR1** removes everything EXCEPT loan and appraisal → its date is the **latest of the
  non-loan/appraisal removals** (usually investigation, 7 days).
- **CR2** removes all remaining → its date is the **latest of loan and appraisal** (usually
  14 days).
These are events McKenna schedules and **always confirms with the agent before sending** —
present them as computed, not final.

## Derived, not from the contract
- **EMD** ≈ Day 3 (escrow notifies) — leave blank unless the human supplies it.
- **Final walkthrough** = close of escrow − 3 to 5 days.

## Worked example (synthetic)
Acceptance 2026-10-01, defaults, close 30 days:
- Investigation removal: +7 → 2026-10-08
- Loan / appraisal removal: +14 → 2026-10-15
- CR1 (non-loan/appraisal): 2026-10-08 · CR2 (loan+appraisal): 2026-10-15
- Close of escrow: +30 → 2026-10-31 (a Saturday → roll to Mon 2026-11-02, record shifted_from)
- Final walkthrough: ~2026-10-28
