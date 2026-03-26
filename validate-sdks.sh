#!/usr/bin/env bash
# Validate Python and Node SDK models against the OpenAPI spec.
# Returns non-zero if either SDK has drifted from the spec.
#
# Usage:
#   ./validate-sdks.sh              # human-readable output
#   ./validate-sdks.sh --json       # JSON output
#   ./validate-sdks.sh --python     # Python SDK only
#   ./validate-sdks.sh --node       # Node SDK only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${SCRIPT_DIR}/scripts"

RUN_PYTHON=true
RUN_NODE=true
JSON_FLAG=""
EXIT_CODE=0

for arg in "$@"; do
    case "$arg" in
        --json)   JSON_FLAG="--json" ;;
        --python) RUN_NODE=false ;;
        --node)   RUN_PYTHON=false ;;
        --help|-h)
            echo "Usage: $0 [--json] [--python] [--node]"
            echo "  --json     Output as JSON"
            echo "  --python   Validate Python SDK only"
            echo "  --node     Validate Node SDK only"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

if [ "$RUN_PYTHON" = true ]; then
    if [ -z "$JSON_FLAG" ]; then
        echo "=== Python SDK ==="
    fi
    if ! python3 "${SCRIPTS_DIR}/validate_python_sdk.py" $JSON_FLAG; then
        EXIT_CODE=1
    fi
    if [ -z "$JSON_FLAG" ]; then
        echo ""
    fi
fi

if [ "$RUN_NODE" = true ]; then
    if [ -z "$JSON_FLAG" ]; then
        echo "=== Node SDK ==="
    fi
    if ! python3 "${SCRIPTS_DIR}/validate_node_sdk.py" $JSON_FLAG; then
        EXIT_CODE=1
    fi
    if [ -z "$JSON_FLAG" ]; then
        echo ""
    fi
fi

exit $EXIT_CODE
