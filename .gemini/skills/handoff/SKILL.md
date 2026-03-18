---
name: handoff
description: Save session context for the next agent to pick up
user_invocable: true
---

<prompt>
Save the current session context so the next agent can pick up where you left off. Write a handoff file to `/home/user/.gemini/projects/-home-user-ss/memory/session_handoff.md`.

## Steps

1. Review the conversation history to identify:
   - **Files edited** this session (list absolute paths)
   - **What was accomplished** (brief summary of completed work)
   - **Work in progress** (anything started but not finished)
   - **Blocked items** (anything that couldn't be completed and why)
   - **Next steps** (concrete tasks the next agent should tackle)
   - **Key decisions** (any architectural or design choices made)

2. Write the handoff file with this format:

```markdown
# Session Handoff

**Date:** [current date/time]
**Branch:** [current git branch]
**Working directory:** [cwd or submodule]

## Completed
- [bullet list of what was done]

## Files Modified
- [absolute paths of files edited/created]

## In Progress
- [anything partially done, with context on current state]

## Blocked
- [anything that couldn't proceed, with reason]

## Next Steps
- [concrete actionable tasks for the next agent]

## Key Decisions
- [any design/architecture choices the next agent should know about]

## Relevant Context
- [any gotchas, workarounds, or non-obvious details]
```

3. After writing the file, confirm to the user that the handoff was saved and summarize the key points.

## Rules
- Be specific with file paths (always absolute).
- Keep it concise — the next agent needs to get up to speed fast.
- Include enough context that the next agent doesn't need to re-read the full conversation.
- If there are uncommitted changes, note that prominently.
</prompt>
