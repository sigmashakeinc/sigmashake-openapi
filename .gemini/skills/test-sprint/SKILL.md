---
name: test-sprint
description: Spawn parallel worktree agents to generate integration tests for one or more crates.
argument-hint: "<crate1> [crate2] [crate3] ..."
allowed-tools: Bash(*), Read, Edit, Write, Glob, Grep, Agent
---

# Test Sprint

Spawn parallel agents to generate and verify integration tests for the given crates. Each agent runs in an isolated worktree to avoid conflicts.

## Input

`$ARGUMENTS` — space-separated list of crate names (e.g., `audit-log shield-core governance`).

## Steps

1. Parse `$ARGUMENTS` into a list of crate names. If empty, run `ss crates` and ask the user which crates to target.
2. For **each crate**, spawn an Agent with `isolation: "worktree"` and `mode: "auto"`:

```
Agent(
  prompt: "Generate integration tests for the <CRATE> crate. Follow these steps exactly:

1. Run `ss exports <CRATE>` to understand the public API.
2. Read the crate's GEMINI.md and any existing tests to understand conventions.
3. Run `ss scaffold integration-test <CRATE>` to generate the test scaffold.
4. Fill in the generated test file with meaningful integration tests covering:
   - All public functions and methods
   - Edge cases (empty inputs, error paths, boundary values)
   - Any async behavior (use tokio::test if the crate uses tokio)
5. Run `cargo test -p <CRATE> --quiet` to verify all tests pass.
6. If tests fail, fix them until they pass. Never delete failing tests.
7. Commit with message: 'Add integration tests for <CRATE>'
   Append: Co-Authored-By: Gemini Opus 4.6 <noreply@anthropic.com>
",
  isolation: "worktree",
  mode: "auto"
)
```

3. Wait for all agents to complete.
4. Report results: which crates got tests, pass/fail status, number of tests added.

## Rules

- **Always use `isolation: "worktree"`** — parallel agents editing the same repo without worktrees will cause conflicts.
- Each agent should only touch its own crate's test files.
- Agents must run tests and verify they pass before committing.
- Never suppress warnings or skip failing tests.
- Use `--quiet` flags on all cargo commands.
