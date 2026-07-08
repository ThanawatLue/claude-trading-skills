#!/bin/bash
# Run the daily signal pipeline safely from cron/systemd on a GCP VM.

set -euo pipefail

MARKET="${1:-TH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
LOCK_FILE="/tmp/tong_trading_daily_pipeline_${MARKET}.lock"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

{
  echo "=== Daily signal pipeline start: $(date -Is) market=${MARKET} ==="
  if command -v flock >/dev/null 2>&1; then
    flock -n "$LOCK_FILE" uv run python scripts/run_daily_signal_pipeline.py \
      --config state/automation_config.yaml \
      --market "$MARKET"
  else
    uv run python scripts/run_daily_signal_pipeline.py \
      --config state/automation_config.yaml \
      --market "$MARKET"
  fi
  echo "=== Daily signal pipeline done: $(date -Is) market=${MARKET} ==="
} >> "$LOG_DIR/daily_signal_pipeline_${MARKET}.log" 2>&1
