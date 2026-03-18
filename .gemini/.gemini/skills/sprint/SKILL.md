---
name: sprint
description: Launch parallel agents to execute all unclaimed tasks in a workstream
user_invocable: true
arguments: "ws-id"
---

# /sprint — Parallel Workstream Execution

Launch one agent per unclaimed task in a workstream, each in an isolated worktree.

## Input

`$ARGUMENTS` — a workstream ID (e.g., `ws-001`). If empty, read BOARD.md and ask the user which workstream to sprint.

## Steps

### 1. Read & Validate

1. Read `shared/coordination/BOARD.md` to confirm the workstream exists and is active
2. Read `shared/coordination/workstreams/<ws-id>.md`
3. **Filter tasks to current repo** — determine which repo you're running in and filter tasks using TWO criteria (both must match):
   - **Scope tag**: `repos/sigmashake_inc` matches `backend`, `api`, `infra`, `test`; `repos/sigmashake.com` matches `frontend`, `design`, `test`; umbrella root matches all
   - **Crates/Files column**: the target files must belong to the current repo. E.g., a `test`-scoped task targeting `sigmashake_inc/crates/...` is skipped when sprinting from `sigmashake.com`, even though `test` is in both scope lists
   - When in doubt, check if the Crates/Files path starts with the current repo name
4. Parse the Tasks table — collect all rows where Status is `todo` and Claimed By is `--`, filtered by BOTH scope and target files from step 3
5. If no matching unclaimed tasks, report "nothing to sprint in this repo" and list any unclaimed tasks in other scopes
6. Read the contract file referenced in the workstream frontmatter to have the interface spec available

### 2. Claim All Tasks

Before spawning any agents, claim ALL unclaimed tasks in a single batch edit:
- Set each task's Claimed By to a unique agent label: `sprint-<ws-id>-<N>` (N = 1,2,3...)
- Set each task's Status to `in-progress`
- This prevents other sessions from claiming the same work

### 2b. Pre-Slice Context

Before spawning agents, reduce redundant file reads across agents:

1. Identify all unique crates referenced in the claimed tasks' Crates/Files column
2. For each unique crate, run: `ss exports <crate> --quiet`
3. Collect the output (public API signatures) — this will be injected into agent prompts
4. Replace the agent instruction "Read existing code in the target crates/files" with the pre-sliced signatures

This eliminates N agents each reading the same source files (saves N × file-read token cost).

### 2c. Model Routing

Assign model per task scope:
- Scope `test` or `docs` → add `model: "haiku"` to the Agent() call (cheap, fast)
- All other scopes → omit `model:` (inherits sonnet from opusplan session)

### 3. Spawn Parallel Agents

For **each claimed task**, spawn an Agent with `isolation: "worktree"` and `mode: "auto"`:

```
Agent(
  description: "<task-description>",
  model: "haiku",   # ONLY for test/docs scope; omit this line for all other scopes
  prompt: "You are executing a task from workstream <ws-id>.

## Your Task
<task description from the table>

## Scope
<scope tag from the table>

## Target Files
<crates/files from the table>

## Contract
<paste the relevant contract section — OpenAPI paths/schemas or proto service definition>

## Pre-Sliced API Context
<paste ss exports output for each relevant crate here>

## Instructions

1. Read GEMINI.md in the target repo first — internalize ALL rules before writing code
2. Read the contract reference to understand the interface shape exactly
3. Use pre-sliced API context above — do NOT re-read source files that are already summarized
4. Implement the task — follow the contract precisely, no ad-hoc field names
5. Run `cargo fmt -p <crate> --quiet` after changes
6. Run `cargo clippy -p <crate> --quiet` and fix all warnings
7. Run `ss check` to run the full governance pipeline (fmt, clippy, governance rules, deny.toml)
8. Fix ALL governance violations — never downgrade ERROR to WARNING, never suppress with #[allow(...)]
9. Run `cargo nextest run -p <crate> --quiet` (fall back to `cargo test -p <crate> --quiet`)
10. If tests fail, fix them. Never delete or skip tests.
11. Commit with message describing what was implemented
    Append: Co-Authored-By: Gemini Opus 4.6 <noreply@anthropic.com>

## Output Minimization (mandatory)
- Edit tool only — never Write on existing files
- 1-line commit messages only — no body, no bullet lists
- No prose output — code changes, test results, and errors only
- `--quiet` on ALL commands — no exceptions
- Structured output only: exit codes, JSON, diffs

## BANNED — Hard Rules (violation = rejected)
- **No SQLite** — no rusqlite, sqlite3, libsqlite3-sys, sqlx-sqlite. All DB goes through `sigmashake-db`
- **No Docker** — no Dockerfiles, docker-compose, bollard, shiplift
- **No .unwrap()** in prod code — use `?` or `.expect()` with reason
- **No unsafe** without `// SAFETY:` comment
- **No #[allow(...)]** — fix the warning, never suppress
- **No openssl** — use rustls
- **No GitHub Actions** — CI via sigmashake-ci only
- **No cron/scheduled tasks** — use hooks or CI stages

## Rules
- Only touch files in your assigned scope — do not edit files assigned to other tasks
- Use `--quiet` on all cargo commands
- If you discover follow-up work needed, note it in the commit message — do not create new tasks
- If blocked by a missing dependency from another task, implement a minimal stub/mock and note it
",
  isolation: "worktree",
  mode: "auto"
)
```

**Launch ALL agents in a single message** (parallel tool calls) for maximum concurrency.

### 4. Collect Results

After all agents complete:

1. For each agent that succeeded:
   - The worktree branch will be returned — merge it into main with `git merge <branch> --no-edit`
   - If merge conflicts occur, resolve them (the conflict is likely in shared files — prefer the agent's version for files in its scope)
   - Update the task's Status to `done` in the workstream file
2. For each agent that failed:
   - If the agent used `model: "haiku"` (test/docs scope): retry **once** with sonnet (omit the model line), prepend a 1-line error summary to the prompt
   - If the retry also fails, or the agent used sonnet: report the failure reason, mark as failed
   - Reset failed task's Claimed By to `--` and Status to `todo` only after all retry attempts are exhausted
3. If ALL tasks are now `done`:
   - Update workstream status to `complete` in frontmatter
   - Move the workstream row from Active to Recently Completed in BOARD.md

### 5. Deploy

After ALL merges succeed and all tasks for the current repo scope are `done`:

1. Run the full pre-deploy validation:
   ```bash
   ss check   # fmt, clippy, governance, deny.toml
   cargo nextest run -p <affected-crates> --quiet
   ```
2. If validation passes, trigger deployment:
   ```bash
   sigmashake-ci deploy <target>
   ```
   - `sigmashake_inc` → `sigmashake-ci deploy api`
   - `sigmashake.com` → `sigmashake-ci deploy frontend`
3. If validation fails, do NOT deploy. Report the failures and which tasks introduced them.

**Skip deploy** if any tasks failed or remain unclaimed — partial deploys are dangerous.

### 6. Report

Present a summary table:

```
Sprint Complete: ws-NNN (<workstream name>)

| Task | Agent | Result | Branch |
|------|-------|--------|--------|
| ... | sprint-ws-001-1 | merged | ... |
| ... | sprint-ws-001-2 | failed: <reason> | ... |

N/M tasks completed. <remaining> tasks unclaimed for retry.
Deploy: <deployed via sigmashake-ci | skipped: N tasks failed>
```

## Merge Strategy

Worktree agents commit on isolated branches. The merge-back sequence is:

1. `git fetch origin main` — get latest
2. `git merge origin/main --no-edit` — incorporate others' work into agent branch
3. `git checkout main`
4. `git merge <agent-branch> --no-edit` — fast-forward or merge commit
5. `git push origin main --quiet`
6. Repeat for next agent

**Serialize merges** — do them one at a time to avoid push races. If a push fails (another session pushed), pull --rebase and retry once.

## Rules

- **Always use `isolation: "worktree"`** — non-negotiable for parallel work
- Claim tasks BEFORE spawning agents — prevents duplicate work
- Each agent only touches files in its assigned scope
- Never skip pre-push hooks or deploy directly
- If the workstream has fewer than 2 unclaimed tasks, just run them sequentially (no worktree overhead needed)
