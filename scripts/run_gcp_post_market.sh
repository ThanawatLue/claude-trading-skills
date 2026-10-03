#!/bin/bash
# Run post-market Jules evolutionary review, update Trader DNA, and push to GitHub.
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
  MEM_DIR="state/jules_us_memory"
  LOG_FILE="$LOG_DIR/post_market_evolution_US.log"
else
  MEM_DIR="state/jules_memory"
  LOG_FILE="$LOG_DIR/post_market_evolution.log"
fi

{
  echo "=== Post-Market Evolution [$MARKET] Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_evolver.py run --market "$MARKET"
  if git status --porcelain "$MEM_DIR/" | grep -q .; then
    git add "$MEM_DIR/"
    git commit -m "chore(jules): evolve trader DNA [$MARKET] post-market $(date +%Y-%m-%d)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Post-Market Evolution [$MARKET] Done: $(date -Is) ==="
} >> "$LOG_FILE" 2>&1