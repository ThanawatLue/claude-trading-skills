#!/bin/bash
# Run post-market Jules evolutionary review, update Trader DNA, and push to GitHub.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

{
  echo "=== Post-Market Evolution Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_evolver.py run
  if git status --porcelain state/jules_memory/ | grep -q .; then
    git add state/jules_memory/
    git commit -m "chore(jules): evolve trader DNA post-market $(date +%Y-%m-%d)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Post-Market Evolution Done: $(date -Is) ==="
} >> "$LOG_DIR/post_market_evolution.log" 2>&1