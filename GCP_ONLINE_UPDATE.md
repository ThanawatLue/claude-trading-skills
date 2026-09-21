# GCP Online Automation Update

Last updated: 2026-09-21

## What Changed

The project features a fully automated trading intelligence pipeline and autonomous fund manager on GCP Compute Engine (`35.212.209.201`). It executes the full decision and risk cycle autonomously without human intervention.

Key Active Modules:
- `scripts/jules_scout.py` (Daily Morning Scout & Adaptive Matrix Screener)
- `scripts/jules_trader.py` (Pre-market Autonomous Decision Engine & Circuit Breakers)
- `scripts/jules_fund.py` (Order Processing, Dead-Letter Queue, and Portfolio Accounting)
- `scripts/jules_evolver.py` (Post-Market Review, MFE Ratchet Breakeven Stop, Trader DNA Evolution)
- `scripts/adaptive_indicators.py` (Thematic Clusters, Recency-Weighted U/D Ratio, Dynamic ATR Caps, Mansfield RS)

## Cron Jobs Installed On GCP

The managed cron block is installed in UTC (`CRON_TZ=UTC`), corresponding to Bangkok market hours (UTC+7):

```text
# General Intelligence Scans & Paper Trade Updates
0 3-10 * * 1-5       (10:00-17:00 ICT)  TH Hourly Scan via Dashboard API
30 3-10 * * 1-5      (10:30-17:30 ICT)  TH Hourly Paper Marks Update
30 13 * * 1-5        (20:30 ICT)        US Market Scan
0 14 * * 1-5         (21:00 ICT)        US Signal Ledger Pipeline
30 14 * * 1-5        (21:30 ICT)        US Paper Marks Update

# Jules AI Autonomous Fund Loop
30 1 * * 1-5         (08:30 ICT)        Morning Scout & Adaptive Mission (run_gcp_morning_scout.sh)
40 2 * * 1-5         (09:40 ICT)        Autonomous Decision Maker (run_gcp_auto_decision.sh)
15,30,45 3-9 * * 1-5 (10:15-16:45 ICT)  Order Processor every 15m (run_gcp_order_processor.sh)
5 10 * * 1-5         (17:05 ICT)        Post-Market Evolutionary Review (run_gcp_post_market.sh)
```

## What The Pipeline Does

The GCP pipeline runs:

```bash
uv run python scripts/run_daily_signal_pipeline.py --config state/automation_config.yaml --market <TH|US>
```

It performs:

1. Ingest thesis files.
2. Ingest signal files from configured report patterns.
3. Update forward outcomes.
4. Run the configured auto-paper validation profile.
5. Write daily reports.

Current online validation config is:

```yaml
auto_paper:
  enabled: true
  execute: true
  account_size: 30000
  risk_per_trade_pct: 1
  max_position_pct: 20
  max_portfolio_heat_pct: 3
  max_new_positions: 4
  max_open_positions: 4
  fee_model:
    broker: innovestx
    commission_pct: 0.15
    trading_fee_pct: 0.005
    clearing_fee_pct: 0.001
    vat_pct: 7
    slippage_bps: 5
```

The effective estimated transaction cost is `21.692 bps` per side. The slippage value is an explicit paper-trading assumption, not a broker quote.

`execute: true` only enables simulated paper entries. The VM has no InnovestX order-submission path, so this deployment cannot place real orders.

## Current Online Verification

The dashboard is available at:

```text
http://35.212.209.201/
```

The `/api/health` endpoint reports service status `ok` and deployed commit `a622f45`. `/api/signal-results?market=TH` reports the 30,000 THB account profile and InnovestX fee model.

## Logs And Reports

Pipeline logs:

```text
logs/daily_signal_pipeline_TH.log
logs/daily_signal_pipeline_US.log
```

Daily reports:

```text
reports/daily-signal-pipeline/daily_signal_pipeline_YYYY-MM-DD.json
reports/daily-signal-pipeline/daily_signal_pipeline_YYYY-MM-DD.md
```

Dashboard service logs depend on the VM's systemd setup, usually:

```bash
sudo journalctl -u dashboard.service -n 100 --no-pager
```

## One-Time VM Checks

After pushing this update, check these on the GCP VM:

```bash
cd ~/claude-trading-skills-1
git pull origin main
bash scripts/setup_gcp_cron.sh
crontab -l
sudo systemctl status dashboard.service
```

Manual dry-run test:

```bash
cd ~/claude-trading-skills-1
bash scripts/run_gcp_daily_pipeline.sh TH
tail -n 80 logs/daily_signal_pipeline_TH.log
```

## Required Secrets / Environment

GitHub Actions needs these repository secrets:

```text
GCP_HOST
GCP_USERNAME
GCP_SSH_KEY
```

Optional repository secrets:

```text
GCP_PROJECT_DIR          use this if the VM checkout is not in a default path
GCP_DASHBOARD_SERVICE    use this if the service name is not dashboard.service
```

The VM should have any required runtime environment variables for dashboard/data sync:

```text
HF_TOKEN
HF_DB_REPO_ID
FMP_API_KEY      optional/needed by some scanners
FINVIZ_API_KEY   optional
```

## Current Limitation

The first live deployment attempt found that `~/tong_trading` did not exist on the VM and `dashboard.service` was not installed. The deployment workflow now handles those cases automatically.

Verification should be done after pushing to `main` by checking GitHub Actions and VM cron logs.
