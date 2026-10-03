#!/bin/bash
# Run the morning Jules scout, generate today's mission, and push to GitHub.
# Supports market parameter: TH (default) or US.

set -euo pipefail

MARKET="${1:-TH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

if [ "$MARKET" = "US" ]; then
  TASK_DIR="state/jules_us_tasks"
  LOG_FILE="$LOG_DIR/morning_scout_US.log"
else
  TASK_DIR="state/jules_tasks"
  LOG_FILE="$LOG_DIR/morning_scout.log"
fi

{
  echo "=== Morning Scout [$MARKET] Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_scout.py run --market "$MARKET"
  if git status --porcelain "$TASK_DIR/" | grep -q .; then
    git add "$TASK_DIR/"
    git commit -m "chore(jules): publish daily mission [$MARKET] for $(date +%Y-%m-%d)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Morning Scout [$MARKET] Done: $(date -Is) ==="
} >> "$LOG_FILE" 2>&1
