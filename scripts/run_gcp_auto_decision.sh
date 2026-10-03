#!/bin/bash
# Run the autonomous Jules Decision Maker, select candidate, stage order, and push to GitHub.
# Supports market parameter: TH (default) or US.

set -euo pipefail

MARKET="${1:-TH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
LOCK_DIR="$PROJECT_ROOT/state/locks"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR" "$LOCK_DIR"
cd "$PROJECT_ROOT"

if [ "$MARKET" = "US" ]; then
  ORDERS_DIR="state/jules_us_orders"
  LOG_FILE="$LOG_DIR/auto_decision_US.log"
  LOCK_FILE="$LOCK_DIR/jules_auto_decision_US.lock"
else
  ORDERS_DIR="state/jules_orders"
  LOG_FILE="$LOG_DIR/auto_decision.log"
  LOCK_FILE="$LOCK_DIR/jules_auto_decision.lock"
fi

exec 200>"$LOCK_FILE"
flock -n 200 || { echo "Auto decision [$MARKET] already running. Exiting."; exit 0; }

{
  echo "=== Autonomous Decision [$MARKET] Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_trader.py decide --market "$MARKET"
  if git status --porcelain "$ORDERS_DIR/" | grep -q .; then
    git add "$ORDERS_DIR/"
    git commit -m "feat(jules): stage autonomous order [$MARKET] for $(date +%Y-%m-%d)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Autonomous Decision [$MARKET] Done: $(date -Is) ==="
} >> "$LOG_FILE" 2>&1
