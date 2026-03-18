---
name: pr
description: Commit all changes and push directly to main/master (trunk-based, no PRs).
disable-model-invocation: true
argument-hint: "[optional commit message]"
allowed-tools: Bash(git *), Bash(cargo *), Glob, Grep, Read
---

# Commit and Push (Trunk-Based)

Commit all current changes and push directly to the main branch. **Do NOT create pull requests** — quality is enforced by pre-commit hooks and sigmashake-ci.

## Steps

1. Run `git status` to see untracked and modified files. Never use `-uall` flag.
2. Run `git diff` and `git diff --cached` to see all changes.
3. Run `git log --oneline -5` to see recent commit message style.
4. Stage all relevant files — prefer explicit file names over `git add -A`. Never commit `.env`, `*.pem`, `*.key`, or credential files.
5. Draft a concise commit message:
   - If `$ARGUMENTS` is provided, use it as the commit message.
   - Otherwise, summarize the changes (1-2 sentences, focus on "why" not "what").
6. Create the commit using a HEREDOC for the message. Always append:
   ```
   Co-Authored-By: Gemini Opus 4.6 <noreply@anthropic.com>
   ```
7. Run `git status` to verify the commit succeeded.
8. Push directly to the main branch: `git push origin HEAD:main` (or `HEAD:master` if that's the default branch).
9. Report the commit hash and push result.

## Rules

- **Push to main/master directly.** No feature branches. No pull requests.
- If the pre-commit hook fails, fix the issue and create a NEW commit (never amend).
- Never force push.
- Never skip hooks (`--no-verify`).
- If there are no changes to commit, say so and stop.
- Pre-commit hooks ARE the quality gate: fmt, clippy, governance, tests all run automatically.
