---
name: rebuild
description: Rebuild all services, restart the full stack, and launch sigmashake-agent.
user_invocable: true
argument-hint: "[--skip-agent] [--force] [--backend-only]"
allowed-tools: Bash(cargo *), Bash(cd *), Bash(source *), Bash(kill *), Bash(curl *), Bash(lsof *), Bash(cat *), Bash(sleep *), Bash(test *), Bash(echo *), Bash(tail *), Bash(./dev-full-stack.sh *), Bash(./repos/sigmashake_inc/dev-stack.sh *), Bash(./repos/sigmashake_inc/target/debug/sigmashake-agent *), Read, Glob, Grep
---

# Rebuild & Restart Full Stack + Agent

Stop all services, rebuild everything from source, restart the full stack (backend + frontend), regenerate `dev.env`, and launch the `sigmashake-agent` daemon connected to local fleet.

## Input

`$ARGUMENTS` — optional flags:
- `--skip-agent`: Skip building and launching sigmashake-agent
- `--force`: Kill stale processes on known ports before starting
- `--backend-only`: Skip frontend (trunk serve)

## Steps

### 1. Stop Everything

Stop any running services and the agent:

```bash
# Kill any running sigmashake-agent first
pkill -f 'target/debug/sigmashake-agent' 2>/dev/null || true

# Stop the full stack (frontend + backend)
cd /home/user/ss
./dev-full-stack.sh stop 2>&1 | tail -10
```

If `--force` is in `$ARGUMENTS`, also kill stale processes on all known ports:
```bash
for port in 3000 8080 8100 8200 8300 8400 8500 8600 8700 8800 8900 9000 18400 18401; do
    lsof -i ":${port}" -sTCP:LISTEN -t 2>/dev/null | xargs kill 2>/dev/null || true
done
sleep 1
```

### 2. Rebuild Backend Services

Build all 11 backend service binaries from source:

```bash
cd /home/user/ss/repos/sigmashake_inc
cargo build -p agent-api -p governance -p sigmashake-shield-daemon -p gateway-core \
  -p oidc -p account -p sigmashake-db-server -p soc-core \
  -p fleet-dev-server -p audit-dev-server -p dev-gateway \
  --quiet 2>&1 | tail -5
```

If this fails, stop and report the error. Do NOT start services with a broken build.

### 3. Build sigmashake-agent

Unless `--skip-agent` is in `$ARGUMENTS`:

```bash
cd /home/user/ss/repos/sigmashake_inc
cargo build -p sigmashake-agent --quiet 2>&1 | tail -5
```

If this fails, stop and report the error.

### 4. Start Full Stack

Use the appropriate start command based on flags:

```bash
cd /home/user/ss
```

If `--backend-only` is in `$ARGUMENTS`:
```bash
./repos/sigmashake_inc/dev-stack.sh start 2>&1 | tail -20
```

Otherwise (full stack with frontend):
```bash
./dev-full-stack.sh start 2>&1 | tail -20
```

Add `--force` flag if it was in `$ARGUMENTS`.

Wait for the start command to complete. Check exit code. If it fails, report the failure and show relevant logs:
```bash
./dev-full-stack.sh logs --errors 2>&1 | head -30
```

### 5. Source dev.env

Load the generated environment so the agent gets the correct tenant ID and fleet URL:

```bash
source /home/user/ss/dev.env
```

Verify the key variables are set:
```bash
echo "SIGMASHAKE_TENANT_ID=${SIGMASHAKE_TENANT_ID:-NOT SET}"
echo "SIGMASHAKE_FLEET_URL=${SIGMASHAKE_FLEET_URL:-NOT SET}"
echo "SIGMASHAKE_AGENT_ADMIN_ADDR=${SIGMASHAKE_AGENT_ADMIN_ADDR:-NOT SET}"
echo "SIGMASHAKE_AGENT_PROXY_ADDR=${SIGMASHAKE_AGENT_PROXY_ADDR:-NOT SET}"
```

If `SIGMASHAKE_TENANT_ID` is not set, warn and set fallback:
```bash
export SIGMASHAKE_TENANT_ID="${SIGMASHAKE_TENANT_ID:-dev-tenant}"
export SIGMASHAKE_FLEET_URL="${SIGMASHAKE_FLEET_URL:-http://localhost:8800}"
export SIGMASHAKE_AGENT_ADMIN_ADDR="${SIGMASHAKE_AGENT_ADMIN_ADDR:-127.0.0.1:18400}"
export SIGMASHAKE_AGENT_PROXY_ADDR="${SIGMASHAKE_AGENT_PROXY_ADDR:-127.0.0.1:18401}"
```

### 6. Launch sigmashake-agent

Unless `--skip-agent` is in `$ARGUMENTS`:

```bash
cd /home/user/ss/repos/sigmashake_inc
SIGMASHAKE_TENANT_ID="${SIGMASHAKE_TENANT_ID}" \
SIGMASHAKE_FLEET_URL="${SIGMASHAKE_FLEET_URL}" \
SIGMASHAKE_FLEET_ENABLED=true \
SIGMASHAKE_AGENT_ADMIN_ADDR="${SIGMASHAKE_AGENT_ADMIN_ADDR}" \
SIGMASHAKE_AGENT_PROXY_ADDR="${SIGMASHAKE_AGENT_PROXY_ADDR}" \
RUST_LOG=info \
  ./target/debug/sigmashake-agent \
  > .dev-stack/logs/sigmashake-agent.log 2>&1 &
echo $! > .dev-stack/sigmashake-agent.pid
```

Wait for the agent to become healthy (up to 15 seconds):
```bash
for i in $(seq 1 15); do
    if curl -sf "http://${SIGMASHAKE_AGENT_ADMIN_ADDR:-127.0.0.1:18400}/health" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
curl -sf "http://${SIGMASHAKE_AGENT_ADMIN_ADDR:-127.0.0.1:18400}/health" && echo " agent: healthy" || echo " agent: FAILED (check .dev-stack/logs/sigmashake-agent.log)"
```

### 7. Verify Agent Visibility in Fleet

Confirm the agent registered with fleet and is visible:

```bash
sleep 2
curl -s "http://localhost:8800/v1/fleet/agents?page=1&per_page=50" 2>&1 | head -20
```

If the response contains the agent (look for the tenant_id matching `dev-tenant`), report success. If empty or error, warn that fleet registration may take a moment.

### 8. Health Summary

Run a final health check across all services:

```bash
cd /home/user/ss
./dev-full-stack.sh status --json 2>&1
```

Report a summary table:

```
Rebuild Complete

| Service         | Port  | Status  |
|-----------------|-------|---------|
| Backend (11)    | 8080+ | healthy |
| Frontend        | 3000  | healthy |
| sigmashake-agent| 18400 | healthy |
| Fleet visible   | 8800  | yes     |

dev.env: sourced (tenant=dev-tenant)
```

## Rules

- Never start services if the build failed — always check cargo build exit code.
- Always kill the old sigmashake-agent before launching a new one.
- The agent MUST be launched with `SIGMASHAKE_TENANT_ID=dev-tenant` to match fleet-dev-server's JWT tenant claim.
- The agent admin port MUST be 18400 (not 8400, which conflicts with oidc-http).
- Use `--quiet` on all cargo commands to minimize token output.
- If any service fails health check, show its last 10 log lines for debugging.
- Do NOT deploy anything — this skill is for local development only.
