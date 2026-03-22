<!-- SIGMASHAKE-ORG-POLICY:START -->
<!-- SINGLE SOURCE OF TRUTH for org-wide policy. Injected by sync-config.sh. Edit HERE, then run: ./sync-config.sh -->

## Git & Submodules
- When working with git submodules, always check branch state (`git status`, `git branch`) before making changes. Never operate on detached HEAD without explicitly reattaching first.
- For multi-repo/worktree operations, always verify you're writing to the correct directory before editing files.

## Pre-commit & Hooks
- Pre-commit hooks frequently cause friction. Before committing, run the pre-commit checks manually first (`cargo fmt`, `cargo clippy`, secret scan) so failures are caught early.
- If governance rules or deny.toml cause false positives, use targeted `gov:allow` annotations rather than broad workarounds.
- Never ban transitive dependencies (e.g., libc) in deny.toml — only ban direct dependencies.

## Rust Conventions
- Axum 0.8+ uses `{param}` syntax for path parameters (e.g., `/{id}`, `/{name}`). The old `:param` syntax is no longer valid.
- Always run `cargo clippy` and `cargo fmt` after changes before claiming success
- When fixing clippy warnings, scope fixes to the crates you changed — don't fix unrelated crates unless asked
- Never recommend replacing `cargo test` with custom tooling without benchmarking first
- **NEVER claim build/test success without running `cargo build -p <crate>` and `cargo test -p <crate>` and confirming zero errors.** Paste the final test summary line as proof.

## NO DIRECT DEPLOYS

**All deployments must go through `sigmashake-ci`.** Never run `wrangler pages deploy`, `wrangler deploy`, or any direct Cloudflare deployment command. Enforced by:
- `no-direct-deploy` governance rule (ERROR, blocks commit)
- `block-direct-deploy.sh` PreToolUse hook (blocks Bash command)

Use `sigmashake-ci deploy <target>` or the `/deploy` skill instead.

## Workflow Discipline
- When debugging deployment/infra issues, check infrastructure first (`dig`, `curl -I`, DNS, hosting config) before changing application code.
- After each logical unit of work in multi-repo sessions, commit immediately and verify git state before moving to the next task.

## CONTRACT-FIRST DEVELOPMENT

Every feature must reference a contract (OpenAPI path, protobuf service) defined in `shared/coordination/contracts/`. Never implement API endpoints, SDK methods, or service interfaces without a contract first. The contract is the single source of truth for the interface shape.

## AI-NATIVE MANDATE

AI-Native company. Every service, tool, and pipeline is built by and for AI agents.

**10-Second Rule:** Any process >10s MUST be optimized, parallelized, or made async.

**Opus-Plan → Sonnet-Execute:** Sessions use `opusplan` model — Opus 4.6 for planning (architecture, detailed instructions), Sonnet 4.6 for execution (fast code generation). Sessions start in plan mode. After plan approval (`Shift+Tab`), model auto-switches to Sonnet for 3-4x faster output.

**Token Optimization:** Prefer `Read` tool over dumping entire file contents. Use `--quiet` when you don't need diagnostic output, but **never suppress output when debugging** — full compiler errors, test failures, and stack traces are essential for diagnosing issues.

## TOKEN SERVICES (Mandatory)

Always use these tools to minimize context bloat and maximize efficiency:

| Tool | Command | Purpose |
|------|---------|---------|
| **QMD** | `ss-search "<q>"` | Local search/retrieval engine. Use instead of Grep for semantic or broad searches across the codebase. |
| **GitIngest** | `ss-ingest <path>` | Ingest repository or directory into a single LLM-friendly text file for full-context understanding. |
| **Repomix** | `ss-ingest-xml <path>`| Secure, structured XML ingestion. Preferred for full-crate deep dives. |
| **Checkpoint**| `ss-checkpoint "<sum>"`| **Mandatory.** Saves session trajectory to `STATE.md`. Run BEFORE every `/handoff` or when history gets long. |

## CONTEXT ENGINEERING

- **Summaries first:** Read `STATE.md`, `CLAUDE.md`, `ARCHITECTURE.md`, `repo_summary/` BEFORE source code.
- **Context slice:** NEVER read/rewrite whole files. Target exact struct/trait/fn/section.
- **Checkpointing:** Always maintain `STATE.md`. It is the "Off-Chain Memory" for the agent. If the context window is full, summarize the current work into a checkpoint, then ask the user to "reset context" or clear history.
- **Structural Mapping:** Use `ss-search` to find symbols before reading files. Use `ast-grep` for structural changes.

- **Architect → Skeleton → Fill:** (1) architecture + signatures only, (2) compileable skeletons with `todo!()`, (3) implement ONE fn/module per turn.
- **No MCP. Ever.** CLI tools and lean wrappers only.

## EFFICIENCY GUIDELINES

1. **Use `ss exports <crate>`** for public API signatures instead of reading full source files
2. **Sprint model routing** — `test`/`docs` scope tasks use `model: "haiku"`; all other scopes inherit sonnet from opusplan
3. **Commit messages: 1 line only** — no body, no bullet lists
4. **Board summaries: counts only** — one line per workstream; no full task tables in output
5. **Checkpoint before handoff** — `pre-compact-state.sh` hook saves trajectory; also run `ss-checkpoint` manually before `/handoff`
6. **Show full output when debugging** — never suppress compiler errors, test failures, or diagnostic output. Use `--quiet` only for commands where you don't need the output.

## NO SUPPRESSING WARNINGS

**Fix warnings/errors. Never suppress them.** No `#[allow(...)]`, `// @ts-ignore`, `# noqa`, `--cap-lints allow`, commenting out code, or deleting failing tests. Remove dead code instead of allowing it. Only `// gov:allow` (with explanation) for governance false positives. Enforced by `no-lint-suppression` (ERROR, blocks commit).

## SECURITY — ZERO TRUST

**Every layer independently verifies. Never trust upstream alone.**

- `security-scan.sh` (PostToolUse) scans edits for secrets, injection, unsafe, XSS
- Pre-commit: `cargo audit` (CVE), `cargo deny` (license + supply chain), secret scan
- **No openssl** (use rustls). **No `unsafe`** without `// SAFETY:`. **No `.unwrap()`** in prod (use `?`/`.expect()`).
- Secrets in GCP Secret Manager only. All services use mTLS + JWT. All inputs validated at boundaries.
- `deny.toml` blocks unknown registries/git sources, pins allowed licenses.

## `ss` CLI

Use `ss` instead of raw cargo/git. Key commands: `ss crates`, `ss affected <files>`, `ss search <pattern>`, `ss exports <crate>`, `ss check [files]`, `ss scaffold <type> <name>`, `ss health`, `ss bottleneck`. Run `ss --help` for full list.

**Skills:** `/pr`, `/deploy`, `/test-sprint`, `/handoff`, `/sprint ws-NNN`, `/board`.

## `ast-grep` — Structural Search & Replace

Use `sg` for multi-file renames and pattern-based code changes (AST-aware, not text). Use Edit tool for single targeted edits. Example: `sg -p 'old_name' -r 'new_name' -l rs`

## BUILD TOOLCHAIN (Nightly)

Nightly Rust with sccache, mold linker, `-Z threads=8`, cargo-nextest, cargo-hakari. See `.cargo/config.toml` for full settings. Pulse `/pulse` dashboard tracks build speed, cache hit rates, and bottlenecks in real-time.

- **Cranelift** — opt-in only: `CARGO_PROFILE_DEV_CODEGEN_BACKEND=cranelift` (C FFI crates incompatible)
- **After dependency changes:** Run `cargo hakari generate` to update `workspace-hack/Cargo.toml`

## TESTING IS MANDATORY

Every code change MUST include tests. Use `cargo nextest run -p <crate>` (parallel, 2-3x faster than `cargo test`). Enforced by governance rules: `pub-fn-tested`, `test-ratio`, `integration-test-ratio`. Pulse tracks test pass rates, durations, and flaky tests.

## COMMITS — TRUNK-BASED (NO PRs)

Push directly to `main`/`master`. No pull requests. Use `/pr` skill. Always append `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`. Never amend on hook failure — new commit. Never force push. Never skip hooks. Never commit secrets. Fix hook failures first.

## GIT PUSH — MULTI-REPO PROCEDURE

The umbrella repo has a **pre-push hook** that runs `sigmashake-ci verify` (tests + governance). To push successfully:

1. **Build first** — Run `cargo build` in sigmashake_inc before pushing. The pre-push hook has a 120s timeout per command — cold builds will timeout.
2. **Push submodule first** — Always `cd repos/sigmashake_inc && git push` before pushing the umbrella. The umbrella commit references a submodule SHA that must exist on the remote.
3. **Push umbrella second** — From the umbrella root, `git push`. If the pre-push hook fails with timeout, rebuild and retry.
4. **If stale artifacts cause errors** — Run `cargo clean` in sigmashake_inc, then `cargo build`, then retry push.
5. **Do NOT skip hooks** — Fix the underlying issue instead.

## MULTI-AGENT PARALLEL WORK

**2+ agents editing same repo → ALWAYS `isolation: "worktree"`**. Prevents merge conflicts, detached HEAD, lost changes.

## RUNBOOKS

Operational runbooks live in `shared/coordination/runbooks/rb-NNN.md`. Read the runbook and follow the steps. Pulse bottleneck detection auto-generates workstreams when operations degrade.

## PULSE — ENGINEERING OBSERVATORY

The `/pulse` dashboard provides real-time visibility into the entire development lifecycle:
- **Pipeline waterfall** — 12-phase CI/CD with per-phase timing and auto-healing
- **Lifecycle events** — deploy timing, git operations, agent sessions
- **Bottleneck detection** — auto-scores slow/failing operations, generates fix workstreams
- **Tool timing** — per-tool latency from `~/.claude/audit.log` (written by PostToolUse hook)
- **Token economics** — input/output tokens, cost estimation, model breakdown

API: `GET /api/v1/pulse/bottlenecks` for programmatic access. Pulse replaces manual speed monitoring — check the dashboard instead of guessing.

## BANNED PATTERNS

**No cron/scheduled tasks** — use SessionStart/PostToolUse/pre-commit hooks or CI stages instead. Enforced by `no-cron` governance rule + settings.local.json.

**No Docker/containers** — too slow for AI-native workflows. No Dockerfiles, docker-compose, docker commands, or container client libraries (bollard, shiplift). Use native Rust binaries, Cloudflare Workers, or direct cloud deployment. Enforced by `no-docker` governance rule + settings.local.json + deny.toml.

**No GitHub Actions** — all CI/CD runs via `sigmashake-ci`. Do NOT create, modify, or reference `.github/workflows/` files. Enforced by `no-github-actions` governance rule.

**No SQLite** — all database operations MUST go through `sigmashake-db`. No `rusqlite`, `sqlite3`, `libsqlite3-sys`, `sqlx-sqlite`, or any direct SQLite access. Direct SQLite bypasses tenant isolation, audit logging, and encryption. Enforced by `no-sqlite` governance rule (ERROR, blocks commit).

**No downgrading governance severity** — never convert ERROR → WARNING. Fix every violation.
<!-- SIGMASHAKE-ORG-POLICY:END -->
