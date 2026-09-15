#!/bin/bash
# Run the morning Jules scout, generate today's mission, and push to GitHub.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

{
  echo "=== Morning Scout Start: $(date -Is) ==="
  git pull origin main || true
  uv run python scripts/jules_scout.py run
  if git status --porcelain state/jules_tasks/ | grep -q .; then
    git add state/jules_tasks/
    git commit -m "chore(jules): publish daily mission for $(date +%Y-%m-%d)" --no-verify || true
    git push origin main --no-verify || true
  fi
  echo "=== Morning Scout Done: $(date -Is) ==="
} >> "$LOG_DIR/morning_scout.log" 2>&1
