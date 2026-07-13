#!/bin/bash
# Run the daily signal pipeline safely from cron/systemd on a GCP VM.

set -euo pipefail

MARKET="${1:-TH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
LOCK_FILE="/tmp/tong_trading_daily_pipeline_${MARKET}.lock"
DASHBOARD_LOCAL_URL="${DASHBOARD_LOCAL_URL:-http://127.0.0.1:80}"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

refresh_paper_marks() {
  echo "Refreshing paper marks before auto-paper: $(date -Is) market=${MARKET}"
  if ! curl -fsS -X POST --max-time 600 "$DASHBOARD_LOCAL_URL/api/paper/update_marks"; then
    echo "WARNING: pre-pipeline paper mark refresh failed; continuing pipeline."
  fi
  echo
}

run_locked_pipeline() {
  refresh_paper_marks
  uv run python scripts/run_daily_signal_pipeline.py \
    --config state/automation_config.yaml \
    --market "$MARKET"
}

{
  echo "=== Daily signal pipeline start: $(date -Is) market=${MARKET} ==="
  if command -v flock >/dev/null 2>&1; then
    (
      flock -n 9 || {
        echo "Another daily signal pipeline is already running for market=${MARKET}; skipping."
        exit 0
      }
      run_locked_pipeline
    ) 9>"$LOCK_FILE"
  else
    run_locked_pipeline
  fi
  echo "=== Daily signal pipeline done: $(date -Is) market=${MARKET} ==="
} >> "$LOG_DIR/daily_signal_pipeline_${MARKET}.log" 2>&1
