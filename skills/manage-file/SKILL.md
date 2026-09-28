---
name: manage-file
description: >-
  Take an action on an existing Follow Up Boss file for The Boutique — move a deal forward in
  the pipeline (change its stage), log a note on a contact or deal, create or reschedule an
  appointment, assign the file to an agent, mark a task done, or correct a field. Use whenever
  McKenna or Raj says "move [address] to [stage]", "advance [file]", "mark it closed", "log a
  note on [file]", "set/schedule the [inspection/walkthrough] appointment", "assign [file] to
  [Raj/Christina/McKenna]", "mark [task] done", or "fix the [field] on [file]". It reads the
  record first, confirms the exact change, then writes it through Executor. It edits — it never
  deletes anything, never sends email (drafts only), and never changes a field it wasn't asked to.
---

# Manage a File (The Boutique — pipeline & record actions)

The companion to `create-deal`: that one opens a file, this one moves it along afterward. It is
for the small, deliberate edits McKenna makes as a deal progresses — advancing the stage, noting
what happened, booking the walkthrough, routing a file to the right agent. Every write is
confirmed first and scoped to exactly what was asked.

All FUB access is through the **Executor** MCP (`search` → `invoke`; see
`../../references/executor-fub.md`; no local key). v1.2.0 ops are required (updateDeal with
stageId/users, listStages, listUsers, createNote, createAppointment/updateAppointment).

## Non-negotiables (why)
- **Confirm before every write.** Show the human the exact change (this deal → this stage; this
  note text; this appointment time; this agent) and get a yes. A wrong stage move or a note on
  the wrong file is McKenna's reputation, not a typo.
- **Field-scoped.** Send only what you're changing. Never blank a populated field, never touch
  `name`/`price`/`people` you weren't asked to change.
- **Never delete.** There is no delete op and there never will be.
- **Drafts only for email.** This skill never sends; outbound email stays in `draft-emails`.
- **Verify unproven shapes.** `createNote` / `createAppointment` shapes are best-effort (not yet
  live-verified). Before the first one, `GET` an existing note/appointment to confirm field names,
  then write. If a write fails, stop and report the exact error — don't retry blindly.

## The flow
1. **Identify the file / person.** Property address or client → the FUB deal (`deals.listDeals`
   / `deals.getDeal`) and, when the action is contact- or note-level, the `personId`
   (`people.listPeople`). If you can't pin the file confidently, ask which one.
2. **Resolve any ids the action needs** (don't hardcode):
   - Stage move → `listStages` (optionally by `pipelineId` from the deal) to get the target `stageId`.
   - Assignment → `listUsers` to get the agent's `userId` by name.
3. **Read the current record** (`getDeal` / `getPerson`) so you change only what's needed and can
   show the before/after.
4. **Confirm** the exact change with the human. This is the write gate.
5. **Write** the one action through Executor:
   - **Move stage:** `deals.updateDeal { dealId, body: { stageId } }`.
   - **Assign agent:** `deals.updateDeal { dealId, body: { users:[userId] } }` (deal) or
     `people.updatePerson { personId, body: { assignedUserId } }` (contact).
   - **Log note:** `notes.createNote { body: { personId, subject, body } }` (GET an example first).
   - **Appointment:** `appointments.createAppointment` / `appointments.updateAppointment`
     (GET an example first to confirm start/end format and invitees).
   - **Mark task done / reschedule:** `tasks.updateTask { taskId, body: { isCompleted:true } }`
     or `{ dueDate }`.
   - **Fix a field:** `updateDeal` / `updatePerson` with only that field.
6. **Report** what changed (record link, before → after), and name anything you couldn't do
   (e.g. a shape that didn't match on the GET — surface it rather than guessing).

## When to stop and ask
- Ambiguous which file/person → ask.
- A stage move that skips ahead or goes backward unexpectedly → confirm it's intended.
- An appointment/note shape that doesn't match the GET example → report it, don't force a write.
