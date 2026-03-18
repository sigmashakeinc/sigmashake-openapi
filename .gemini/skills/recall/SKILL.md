# Recall — Restore Session Context

Restores context from a previous session by reading the latest or a specific handoff file.

## Commands

| Command | Purpose |
|---------|---------|
| `/recall` | Show the most recent handoff |
| `/recall --list` | List all handoff files |
| `/recall <session-id>` | Show handoff for specific session |

## Usage

- Run `/recall` at session start to see where you left off
- Run `/recall --list` to see all available handoffs
- Run `/recall e340797a` to view a specific session

## How It Works

1. List handoff files in `.gemini/handoffs/`
2. Sort by timestamp (newest first)
3. Read and display the handoff content

## Example Output

```
# Session Handoff

**Date:** 2026-03-15
**Branch:** master
**Working directory:** /home/user/ss

## Completed (This Session)
- Nightly Rust toolchain with -Z threads=8
- cargo-nextest installed (2225 tests pass in 1.7s)

## Uncommitted Changes
- sigmashake_inc (55 files) — build optimizations
- sigmashake.com — log viewer UI

## Next Steps
1. Commit and push all uncommitted changes
2. Build tmux monitor tool
```
