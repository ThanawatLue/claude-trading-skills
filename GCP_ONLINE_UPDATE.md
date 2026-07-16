# GCP Online Automation Update

Last updated: 2026-07-13

## What Changed

The project already had a GCP VM deployment path through GitHub Actions. This update extends it so the VM can keep the trading workflow running even when the local computer is off.

Changed files:

- `.github/workflows/deploy.yml`
- `scripts/setup_gcp_cron.sh`
- `scripts/run_gcp_daily_pipeline.sh`
- `scripts/fee_model.py`
- `dashboard/app.py`
- `state/automation_config.yaml`

## Deployment Flow

When code is pushed to `main`, GitHub Actions now:

1. SSHs into the GCP VM.
2. Finds the project checkout from `GCP_PROJECT_DIR`, `~/tong_trading`, `~/claude-trading-skills-1`, or `~/claude-trading-skills`.
3. Clones the repo into `~/claude-trading-skills-1` if no checkout exists yet.
4. Pulls the latest `main` branch.
5. Installs `uv` if it is missing from the VM PATH, then runs `uv sync`.
6. Creates runtime folders:
   - `logs/`
   - `reports/daily-signal-pipeline/`
   - `state/`
7. Makes automation scripts executable.
8. Runs `bash scripts/setup_gcp_cron.sh`.
9. Creates `dashboard.service` if missing, then restarts it.

This means the VM should receive both dashboard updates and cron automation updates after a successful push.

## Cron Jobs Installed On GCP

The cron setup script now keeps the original dashboard scans and adds follow-up daily signal pipeline jobs.
The GCP VM runs UTC, so the managed cron block uses `CRON_TZ=UTC` and encodes Bangkok times explicitly. This avoids the VM interpreting a Bangkok-looking schedule as UTC.
Each deploy replaces the managed block to prevent stale or duplicate automation jobs.

TH market:

```text
10:00-17:00 Bangkok Mon-Fri  scan dashboard hourly (03:00-10:00 UTC): /api/run?market=TH
10:30-17:30 Bangkok Mon-Fri  refresh paper marks hourly (03:30-10:30 UTC)
```

US market:

```text
20:30 Bangkok Mon-Fri  scan dashboard (13:30 UTC): /api/run?market=US
21:00 Bangkok Mon-Fri  run signal pipeline (14:00 UTC): scripts/run_gcp_daily_pipeline.sh US
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
