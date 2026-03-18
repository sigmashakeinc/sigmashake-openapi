# Analyze — Session & Performance Analysis

Analyze Gemini Code session performance, cost, and codebase health using `ss` CLI commands.
**Do NOT use Python, jq, or shell pipelines for analysis. Use `ss` commands only.**

## Available Commands

| Command | Purpose |
|---------|---------|
| `ss sessions` | List all sessions with token stats, cache hit rate, tool/edit counts |
| `ss sessions --active` | Sessions with activity in last 2 hours |
| `ss sessions --cost` | Include estimated cost breakdown per session |
| `ss sessions --project <name>` | Filter sessions by project name |
| `ss sessions <session-id>` | Detailed view of one session (top edited files, tool breakdown) |
| `ss health` | Workspace health check (fmt, clippy, governance, summaries) |
| `ss profile` | Benchmark full pipeline, report timing per step |
| `ss bottleneck` | Self-diagnostic: find performance bottlenecks with fix commands |
| `ss crates` | List all workspace crates with line counts |

## Steps

1. If `` is provided, interpret what the user wants to analyze.
2. Run the appropriate `ss` command(s) — use `--quiet` flags where available.
3. Present findings concisely. Highlight:
   - Anomalies (low cache hit rate <95%, high edit counts, long sessions)
   - Cost outliers
   - Performance bottlenecks
   - Actionable recommendations
4. If deeper investigation is needed, use `ss sessions <id>` for detail on specific sessions.

## Rules

- **NEVER use Python** to parse JSONL, logs, or any data files.
- **NEVER use `head`, `tail`, `grep`, `awk`, `jq`** to parse structured data — `ss` handles it.
- Use `ss` for all session/performance analysis. Use `Read` tool only for config files.
- Keep output token-efficient — summarize, don't dump raw data.
