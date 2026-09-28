# Reaching Follow Up Boss through Executor (Cowork-native)

All FUB access goes through the **Executor** MCP — never a local file or the FUB key. Executor
holds the key in its vault and attaches it host-side; it never reaches the model, the prompt,
or the artifact. This is how every skill in this plugin talks to FUB.

## The connection
- MCP server: **`executor`** (declared in the plugin's `.mcp.json`, endpoint
  `https://executor.sh/tbreg/mcp`).
- Each user signs into Executor once and has their own connection to the
  `follow_up_boss_boutique_subset` integration (the FUB key lives in *their* Executor vault —
  set once at setup, see the `setup` skill). Nothing here handles the key.

## The call pattern: search → invoke
Executor exposes generic tools, not per-endpoint tools. To call a FUB operation:

1. **`search`** with the operation name to get its tool `id` for this user's connection, e.g.
   `search({ query: "createDeal" })` →
   `id: "tools.follow_up_boss_boutique_subset.user.<connection>.deals.createDeal"`.
   Resolve the id at run time — don't hardcode it; the `<connection>` segment differs per user.
2. **`invoke`** with that id and the input. **POST bodies wrap in `body`:**
   `invoke({ id, input: { body: { ... } } })`. GET-style ops take query params in `input`
   (or `{}`).

## FUB operations (search by these names)
| Need | Operation | Input |
|---|---|---|
| Health / whose account | `getIdentity` | `{}` |
| List deals (dup check, sweep) | `deals.listDeals` | `{ limit, sort }` |
| Create deal (additive) | `deals.createDeal` | `{ body: { name, stageId, price, mutualAcceptanceDate, dueDiligenceDate, customCR1, customCR2Date, projectedCloseDate, finalWalkThroughDate, possessionDate } }` |
| Read one deal | `deals.getDeal` | `{ dealId }` |
| Update a deal (edit dates/price; confirm first) | `deals.updateDeal` | `{ dealId, body: { ...only changed fields } }` |
| List tasks | `tasks.listTasks` | `{ limit }` |
| Create task (additive) | `tasks.createTask` | `{ body: { name, type, dueDate, personId } }` |
| Update a task (due date / mark done) | `tasks.updateTask` | `{ taskId, body: { dueDate, isCompleted } }` |
| Find/list contacts | `people.listPeople` | `{ limit, fields }` |
| Read one contact | `people.getPerson` | `{ personId, fields }` |
| Create a contact (additive) | `people.createPerson` | `{ body: { firstName, lastName, emails:[{value}], phones:[{value}], tags } }` |
| Update a contact (edit; confirm first) | `people.updatePerson` | `{ personId, body: { ...only changed fields } }` |
| List pipelines | `pipelines.listPipelines` | `{}` |
| List stages (get target stageId) | `stages.listStages` | `{ pipelineId? }` |
| List users/agents (get userId) | `users.listUsers` | `{ limit }` |
| Move a deal's stage (advance pipeline) | `deals.updateDeal` | `{ dealId, body: { stageId } }` |
| Assign a deal to agent(s) | `deals.updateDeal` | `{ dealId, body: { users:[userId] } }` |
| Assign a contact to an agent | `people.updatePerson` | `{ personId, body: { assignedUserId } }` |
| Log a note on a contact | `notes.createNote` | `{ body: { personId, subject, body } }` (GET an example first) |
| Create an appointment | `appointments.createAppointment` | `{ body: { title, start, end, personId } }` (GET an example first) |
| Update an appointment | `appointments.updateAppointment` | `{ appointmentId, body: { ...changed } }` |
| List templates | `templates.listTemplates` | `{ limit }` |
| List deal custom fields | `dealCustomFields.listDealCustomFields` | `{}` |

## Proven shapes (live-verified, deal 93)
- **`createDeal`**: `stageId` required + numeric — `pipelineId`/names are rejected. Native date
  fields post directly (no customFields wrapper). Stage IDs: Buyers In Escrow 16 / Closed 18 /
  Canceled 35; Sellers Temp 31 / Coming Soon 30 / Active 32 / In Escrow 17 / Closed 19.
- **`createTask`**: attaches by `personId` (no `dealId` field). Flow: `people.listPeople` to get
  the personId → `createDeal` → `createTask` on the person.
- Dates as `YYYY-MM-DD`.

## Guardrails (unchanged)
- Additive-first. Creating is always safe. Updating an existing deal, task, or contact is
  allowed (v1.1.0 ops), but only for the specific fields you were asked to change, and only
  after the human confirms — never blank or overwrite a field you weren't asked to touch.
  Never delete (no delete op exists in the spec).
- Confirm dates with the human before `createDeal` (refuse-over-guess).
- A read error / missing connection → say so; never fall back to a raw key or a guess.
