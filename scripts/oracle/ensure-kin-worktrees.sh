#!/bin/bash
# KIN-only worktree ensure. Never source paperclip-env.sh (defaults to SYN).
set -euo pipefail

TOKEN_FILE="${KINWATCH_GITHUB_ENV:-/home/ubuntu/.kinwatch/github.env}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f /opt/kinwatch/scripts/oracle/ensure_kin_worktrees.py ]; then
  PY=/opt/kinwatch/scripts/oracle/ensure_kin_worktrees.py
else
  PY="${SCRIPT_DIR}/ensure_kin_worktrees.py"
fi

if [ ! -f "$TOKEN_FILE" ]; then
  echo "ERROR: missing $TOKEN_FILE" >&2
  exit 1
fi
if [ ! -f "$PY" ]; then
  echo "ERROR: missing $PY" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$TOKEN_FILE"
set +a

if [ -z "${GH_TOKEN:-}" ]; then
  echo "ERROR: GH_TOKEN not set after sourcing $TOKEN_FILE" >&2
  exit 1
fi

export KINWATCH_GITHUB_ENV="$TOKEN_FILE"
export KINWATCH_CLONE="${KINWATCH_CLONE:-/opt/kinwatch}"
export PAPERCLIP_API_BASE="${PAPERCLIP_API_BASE:-http://127.0.0.1:3100}"

exec python3 "$PY"
