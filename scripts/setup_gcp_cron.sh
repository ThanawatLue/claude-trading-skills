#!/bin/bash
# Install cron jobs on a GCP VM for automated market scans and signal maintenance.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== TRADING INTELLIGENCE AUTOMATION SETUP ==="
echo "This script configures crontab jobs on this GCP VM."
echo "It runs hourly dashboard scans and paper mark updates. The scan endpoint also runs the signal ledger / auto-paper follow-up."
echo "Cron timezone is fixed to Asia/Bangkok."
echo "================================================"

# Dashboard scan jobs. GCP exposes the managed dashboard on localhost:80 by default.
DASHBOARD_LOCAL_URL="${DASHBOARD_LOCAL_URL:-http://127.0.0.1:80}"
LOCK_DIR="$PROJECT_ROOT/state/locks"
mkdir -p "$LOCK_DIR"
SCAN_TH_CMD="cd \"$PROJECT_ROOT\" && mkdir -p logs \"$LOCK_DIR\" && flock -n \"$LOCK_DIR/tong_trading_scan_TH.lock\" timeout 45m curl -fsS --max-time 2640 \"$DASHBOARD_LOCAL_URL/api/run?market=TH\" >> \"$PROJECT_ROOT/logs/gcp_scan_TH.log\" 2>&1"
SCAN_US_CMD="cd \"$PROJECT_ROOT\" && mkdir -p logs \"$LOCK_DIR\" && flock -n \"$LOCK_DIR/tong_trading_scan_US.lock\" timeout 45m curl -fsS --max-time 2640 \"$DASHBOARD_LOCAL_URL/api/run?market=US\" >> \"$PROJECT_ROOT/logs/gcp_scan_US.log\" 2>&1"
CRON_TH_HOURLY="0 10-17 * * 1-5 $SCAN_TH_CMD"
CRON_US_SCAN="30 20 * * 1-5 $SCAN_US_CMD"

# The TH scan endpoint already invokes the signal pipeline after each scan.
CRON_US_PIPE="0 21 * * 1-5 cd \"$PROJECT_ROOT\" && bash scripts/run_gcp_daily_pipeline.sh US"

# Mark updates refresh open paper positions after each hourly scan.
MARKS_CMD="cd \"$PROJECT_ROOT\" && mkdir -p logs && curl -fsS -X POST --max-time 600 \"$DASHBOARD_LOCAL_URL/api/paper/update_marks\" >> \"$PROJECT_ROOT/logs/gcp_paper_marks.log\" 2>&1"
CRON_TH_MARKS="30 10-17 * * 1-5 $MARKS_CMD"
CRON_US_MARKS="30 21 * * 1-5 $MARKS_CMD"

CURRENT_CRON=$(mktemp)
CLEAN_CRON=$(mktemp)

cleanup() {
    rm -f "$CURRENT_CRON" "$CLEAN_CRON"
}
trap cleanup EXIT

ensure_cron_service() {
    # Installing a crontab does not start the cron daemon.  Keep the
    # scheduler self-healing after VM reboots or service interruptions.
    if ! command -v systemctl >/dev/null 2>&1 || ! sudo -n true 2>/dev/null; then
        echo "WARNING: systemd/passwordless sudo unavailable; cannot verify cron daemon."
        return 0
    fi

    for service in cron.service crond.service; do
        if sudo systemctl cat "$service" >/dev/null 2>&1; then
            sudo systemctl enable --now "$service"
            if sudo systemctl is-active --quiet "$service"; then
                echo "Cron service is active: $service"
                return 0
            fi
        fi
    done

    echo "ERROR: no active cron service found after installing crontab." >&2
    return 1
}

crontab -l > "$CURRENT_CRON" 2>/dev/null || true

# Replace the managed block and remove older unmanaged versions of these jobs.
awk '
    $0 == "# BEGIN TONG_TRADING_AUTOMATION" { skip = 1; next }
    $0 == "# END TONG_TRADING_AUTOMATION" { skip = 0; next }
    skip { next }
    /Automated Trading Intelligence Scans/ { next }
    /Automated Signal Ledger \/ Auto-paper Dry-run Pipeline/ { next }
    /Automated Signal Ledger \/ Auto-paper Pipeline/ { next }
    /Automated Paper Mark Updates/ { next }
    /api\/run\?market=(TH|US)/ { next }
    /run_gcp_daily_pipeline\.sh (TH|US)/ { next }
    /api\/paper\/update_marks/ { next }
    { print }
' "$CURRENT_CRON" > "$CLEAN_CRON"

{
    echo ""
    echo "# BEGIN TONG_TRADING_AUTOMATION"
    echo "CRON_TZ=Asia/Bangkok"
    echo "# Automated Trading Intelligence Scans (TH Market)"
    echo "$CRON_TH_HOURLY"
    echo "# Automated Paper Mark Updates (TH Market)"
    echo "$CRON_TH_MARKS"
    echo "# Automated Trading Intelligence Scans (US Market)"
    echo "$CRON_US_SCAN"
    echo "# Automated Signal Ledger / Auto-paper Pipeline (US Market)"
    echo "$CRON_US_PIPE"
    echo "# Automated Paper Mark Updates (US Market)"
    echo "$CRON_US_MARKS"
    echo "# END TONG_TRADING_AUTOMATION"
} >> "$CLEAN_CRON"

crontab "$CLEAN_CRON"
ensure_cron_service
echo "Cron jobs successfully installed or updated."
echo "Current crontab configuration:"
crontab -l
