#!/bin/bash
# Check GitHub for pending Jules orders, pull, and execute them on GCP VM.
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
  LOG_FILE="$LOG_DIR/order_processor_US.log"
  LOCK_FILE="$LOCK_DIR/jules_order_processor_US.lock"
else
  ORDERS_DIR="state/jules_orders"
  LOG_FILE="$LOG_DIR/order_processor.log"
  LOCK_FILE="$LOCK_DIR/jules_order_processor.lock"
fi

exec 200>"$LOCK_FILE"
flock -n 200 || { echo "Order processor [$MARKET] already running. Exiting."; exit 0; }

{
  echo "=== Order Processor [$MARKET] Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_fund.py process-orders --market "$MARKET"
  if git status --porcelain "$ORDERS_DIR/" | grep -q .; then
    git add "$ORDERS_DIR/"
    git commit -m "chore(jules): record processed orders [$MARKET] $(date -Is)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Order Processor [$MARKET] Done: $(date -Is) ==="
} >> "$LOG_FILE" 2>&1
