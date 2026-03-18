---
name: board
description: View and manage the coordination board for multi-session work
user_invocable: true
arguments: "command"
---

# /board — Coordination Board

You are managing the multi-session coordination board.

## Behavior by Arguments

### No arguments (`/board`)

1. Read `shared/coordination/BOARD.md`
2. For each active workstream, read its workstream file under `shared/coordination/workstreams/`
3. Present a **compressed** summary — counts only, no full task tables:
   - One line per active workstream: `ws-NNN: <name> — N/M done, K unclaimed`
   - If a workstream has ≤3 unclaimed tasks, list them inline; otherwise show count only
   - Recently completed: IDs + names only (e.g., `ws-030 auth-refresh, ws-031 sdk-node`)
4. If there are unclaimed tasks, suggest claiming one with `/board claim <ws-id> <task-description>`

### `claim <ws-id> <task-description>`

1. Read the workstream file `shared/coordination/workstreams/<ws-id>.md`
2. Find the task row matching `<task-description>` (fuzzy match on the Task column)
3. Write the current session ID (`$GEMINI_SESSION_ID` or generate a short identifier) into the "Claimed By" column
4. Change the "Status" column from `todo` to `in-progress`
5. Confirm the claim to the user

### `new <name>`

Create a new workstream from template. Steps:

1. Read `shared/coordination/BOARD.md` to determine the next `ws-NNN` ID
2. Ask the user for:
   - Contract type and reference (e.g., `rest:repos/sigmashake-openapi/openapi.yaml`)
   - Task breakdown (list of tasks with scope tags: backend, frontend, api, test, infra, design)
3. Create `shared/coordination/workstreams/ws-NNN.md` using this template:

```markdown
---
id: ws-NNN
name: <name>
status: planned
created: <today YYYY-MM-DD>
contracts:
  - type: <rest|grpc|other>
    ref: <path to contract file>
    tag: <tag name>
    paths: [<relevant paths>]
---

# <name>

## Goal
<one-line goal from user>

## Contract Status
- [ ] Contract defined
- [ ] Contract validated

## Tasks

| Task | Scope | Claimed By | Status | Crates/Files |
|------|-------|------------|--------|--------------|
<tasks from user input, each with Claimed By: -- and Status: todo>
| Update ARCHITECTURE.md for affected repos | docs | -- | todo | ARCHITECTURE.md, repo_summary/ |
| Update GEMINI.md if new commands/workflows added | docs | -- | todo | GEMINI.md |
| Verify all docs reference correct ports, flags, commands | docs | -- | todo | (review) |

## Decisions
<empty, populated during implementation>
```

**IMPORTANT — Documentation tasks are mandatory.** Every workstream MUST include at least one `docs`-scoped task to update ARCHITECTURE.md, GEMINI.md, and/or repo_summary/ for any repos affected by the workstream's changes. If the workstream adds new scripts, commands, flags, services, or ports, the docs task must cover those. Never mark a workstream complete without docs tasks done.

4. Add a row to the Active Workstreams table in `shared/coordination/BOARD.md`
5. Confirm creation and show the new workstream

### `done <ws-id> <task-description>`

1. Read the workstream file
2. Find the matching task row
3. Change Status from `in-progress` to `done`, keep the Claimed By value
4. If ALL tasks in the workstream are now `done`:
   - Change the workstream frontmatter `status: complete`
   - Move the row from Active Workstreams to Recently Completed in BOARD.md with today's date

### `backlog <title>`

1. Read `shared/coordination/backlog.md`
2. Determine the next BL-NNN ID by finding the highest existing ID
3. Append a new item with the given title, today's date, and ask the user for priority, description, dependencies, and scope
4. Confirm the addition

## Rules

- Always read BOARD.md before making changes
- Never remove or overwrite another session's claim
- When claiming, use Edit tool to modify only the specific task row
- Keep the board clean — move completed workstreams to the "Recently Completed" table
- After any board/workstream edit, the auto-commit hook will persist it automatically
