#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if [[ -x "$REPOSITORY_ROOT/.venv/bin/python" ]]; then
    PYTHON="$REPOSITORY_ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
else
    echo "Python 3 is required to run the test gate." >&2
    exit 127
fi

exec "$PYTHON" "$SCRIPT_DIR/quality_gate.py" --profile release "$@"
