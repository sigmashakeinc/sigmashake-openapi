#!/usr/bin/env bash
# AUTO-GENERATED STUB — DO NOT EDIT
# Source of truth: shared/gemini-config/hooks/security-scan.sh
# Regenerate with: ./sync-config.sh
set -euo pipefail

# Find umbrella root by walking up to shared/gemini-config marker
find_umbrella() {
  local dir="$1"
  while [ "$dir" != "/" ]; do
    [ -d "$dir/shared/gemini-config" ] && echo "$dir" && return 0
    dir=$(dirname "$dir")
  done
  return 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UMBRELLA=$(find_umbrella "$SCRIPT_DIR") || UMBRELLA="/home/user/ss"

# Wait for any in-progress sync to finish before running hook.
# Prevents reading half-written config during sync-config.sh.
SYNC_MARKER="$SCRIPT_DIR/../.sync-in-progress"
if [ -f "$SYNC_MARKER" ]; then
  for _i in 1 2 3 4 5; do
    [ -f "$SYNC_MARKER" ] || break
    sleep 0.1
  done
fi

exec "$UMBRELLA/shared/gemini-config/hooks/security-scan.sh" "$@"
