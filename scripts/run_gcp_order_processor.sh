#!/bin/bash
# Check GitHub for pending Jules orders, pull, and execute them on GCP VM.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

{
  echo "=== Order Processor Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_fund.py process-orders
  if git status --porcelain state/jules_orders/ | grep -q .; then
    git add state/jules_orders/
    git commit -m "chore(jules): record processed orders $(date -Is)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Order Processor Done: $(date -Is) ==="
} >> "$LOG_DIR/order_processor.log" 2>&1
