#!/bin/bash
# Run the autonomous Jules Decision Maker, select candidate, stage order, and push to GitHub.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
LOCK_DIR="$PROJECT_ROOT/state/locks"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR" "$LOCK_DIR"
cd "$PROJECT_ROOT"

exec 200>"$LOCK_DIR/jules_auto_decision.lock"
flock -n 200 || { echo "Auto decision already running. Exiting."; exit 0; }

{
  echo "=== Autonomous Decision Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_trader.py decide
  if git status --porcelain state/jules_orders/ | grep -q .; then
    git add state/jules_orders/
    git commit -m "feat(jules): stage autonomous order for $(date +%Y-%m-%d)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Autonomous Decision Done: $(date -Is) ==="
} >> "$LOG_DIR/auto_decision.log" 2>&1
