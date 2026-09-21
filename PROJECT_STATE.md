# Project State: Claude Trading Skills & Jules AI Fund

**Authoritative Project State & Operational Ledger**  
**Last Updated:** 2026-09-21 (BKK / ICT)  
**Production Host:** GCP Compute Engine `trading-dashboard` (`35.212.209.201`, `us-west1-b`)  
**Git Branch:** `main` (Latest Commit: `4892c1a`)  
**CI/CD:** GitHub Actions (`.github/workflows/ci.yml`) - 100% Passing

---

## 1. Executive Summary & Current Status

The project has transitioned from a set of discretionary Claude skills into a **Fully Autonomous Trading Intelligence & Fund Management System** for the Thai Stock Market (SET) and US markets.

- **Jules AI Autonomous Fund:** Operating with virtual starting capital of **฿30,000 THB** under strict institutional-grade risk rules (InnovestX 21.692 bps fee model, SET 100-share board lot constraints).
- **Fund Health (as of Sep 2026):** Equity ฿29,776.64 THB, 0 open positions (100% cash preserved during post-Fed rate hike market fragility), 4/4 slots available.
- **Autonomy Level:** **100% Autonomous (Zero Human Intervention Required)**. Scout, decision, order execution, ratchet monitoring, and Trader DNA evolution run on automated crontab schedules on the cloud VM.

---

## 2. Autonomous Fund Architecture (The 4-Stage Daily Loop)

```
08:30 ICT (01:30 UTC)  -->  Morning Scout (jules_scout.py)
                            - Scans SET universe via TradingView + yfinance
                            - Evaluates Adaptive Matrix & Thematic Clusters
                            - Discards toxic distribution traps (U/D < 0.85)
                            - Generates state/jules_tasks/today_mission.md (Top 4 candidates)

09:40 ICT (02:40 UTC)  -->  Autonomous Decision Maker (jules_trader.py)
                            - 20 mins pre-market: checks Market Exposure Posture
                            - Evaluates Prudence Gate (REDUCE_ONLY / CASH_PRIORITY -> HOLD_CASH)
                            - Checks Portfolio Circuit Breakers (2 losses -> -50%, 3 losses -> halt)
                            - Calculates volatility-adjusted sizing and SET tick ladders
                            - Stages order into state/jules_orders/ (with 45-min TTL)

10:15–16:45 ICT (Every 15m) -> Order Processor (jules_fund.py process-orders)
                            - Operates during ORB-15 window (skips 10:00 ATO auction)
                            - Enforces Max Chase Envelope (<= +1.0% above trigger)
                            - Validates order TTL and SET board lots
                            - Routes failing orders to Dead-Letter Queue (quarantine/)

17:05 ICT (10:05 UTC)  -->  Post-Market Evolutionary Review (jules_evolver.py)
                            - Reviews MFE Ratchet Breakeven Stops across open trades
                            - Conducts trade postmortems on closed positions
                            - Evolving Trader DNA in state/jules_memory/trader_dna.json
```

---

## 3. Quantitative & Microstructure Safeguards

1. **MFE Ratchet Breakeven Stop:**
   - At **+0.5R MFE** $\rightarrow$ Stop Loss automatically ratchets to Breakeven (0.0R / Entry Price). Winning trades never turn into capital losses.
   - At **+1.0R MFE** $\rightarrow$ Stop locks in **+0.5R profit**.
   - At **+1.5R MFE** $\rightarrow$ Stop locks in **+1.0R profit**.
2. **Resistance-Aware Exits:**
   - Target price is capped at the nearest 30-day swing high resistance if found between 1.1R and 2.0R, selling alongside institutional liquidity.
3. **ORB-15 Execution Window & Anti-Chase Envelope:**
   - Orders never execute at 10:00:00 ATO auction ("Gap & Crap" fade risk). Execution waits until 10:15–10:30 ICT.
   - Orders exceeding $+1.0\%$ above trigger are cancelled immediately to prevent negative expectancy ($E[R] = -0.14R$).
4. **SET Tick Ladder Discretization:**
   - Prices strictly mapped to SET official tick brackets (e.g. ฿10.00–฿25.00 step ฿0.10; ฿25.00–฿100.00 step ฿0.25). Float artifacts (e.g. ฿10.75) are truncated.
5. **Dead-Letter Queue (DLQ / Quarantine):**
   - Failed or malformed orders are isolated to `state/jules_orders/quarantine/` with `.error.json` to prevent poison-pill infinite retry loops.
6. **SQLite Idempotency Ledger:**
   - Tracks all autonomous decisions in `state/jules_orders/jules_decision_ledger.db` ensuring no duplicated trades.

---

## 4. Adaptive Matrix & Dynamic Indicators (Deployed Sep 2026)

Replaces generic single-stock oscillators (RSI, SMA, fixed volume) with institutional-grade filters:

1. **Recency-Weighted Up/Down Volume Ratio (`ai.calculate_recency_weighted_ud_ratio`):**
   - 60% weight on recent 5 days, 40% on prior 15 days. Rejects hidden distribution traps (`U/D < 0.85`, e.g. `ITC.BK`, `GULF.BK`).
2. **Dynamic Volatility Risk Cap (`ai.calculate_dynamic_risk_cap`):**
   - Scaled to stock ATR: $\text{Cap} = \min(8.5\%, \max(3.5\%, 1.8 \times \frac{\text{ATR}}{\text{Price}} \times 100))$.
   - Allows volatile leaders (e.g. `PSL.BK` with 6.1% risk) to pass while keeping low-beta stocks tight.
3. **Thematic Sub-Cluster Detection (`ai.detect_thematic_clusters`):**
   - Maps 11 Thai business clusters (Shipping, Hospital, Renewables, Finance, ICT, Food, etc.).
   - Awards **+15 point bonus** to leaders when $\ge 2$ stocks in the same sub-sector move concurrently.
4. **Mansfield Relative Strength vs Benchmark (`ai.calculate_mansfield_rs`):**
   - Normalized ratio against market base (MSCI Thailand `THD`). Requires $RS > 0$ and rising, rejecting bottom-rebound traps (e.g. `MCOT.BK`).
5. **Thematic Anti-Correlation:**
   - Strictly enforces **maximum 1 stock per sector / cluster** in top candidates and portfolio to eliminate correlation contagion.

---

## 5. GCP Production Infrastructure

- **Server:** GCP Compute Engine e2-micro (`35.212.209.201`).
- **Dashboard Service:** `trading-dashboard.service` (systemd, port 80, Flask + Lightweight Charts).
- **Environment:** Python 3.10 / 3.12 via `.venv` with `uv`.
- **Concurrency Locks:** All cron scripts guarded with POSIX `flock -n` in `state/locks/`.
- **Cron Jobs (UTC aligned to Bangkok ICT):**
  - `0 3-10 * * 1-5`: Hourly TH dashboard scan & signal ingestion
  - `30 3-10 * * 1-5`: Hourly paper mark updates
  - `30 1 * * 1-5` (08:30 ICT): Jules Morning Scout (`run_gcp_morning_scout.sh`)
  - `40 2 * * 1-5` (09:40 ICT): Jules Decision Engine (`run_gcp_auto_decision.sh`)
  - `15,30,45 3-9 * * 1-5` (10:15–16:45 ICT): Jules Order Processor (`run_gcp_order_processor.sh`)
  - `5 10 * * 1-5` (17:05 ICT): Jules Post-Market Evolution (`run_gcp_post_market.sh`)

---

## 6. Active Roadmap & Next Milestones

- [x] Autonomous Decision Engine (`scripts/jules_trader.py`)
- [x] MFE Ratchet Breakeven Stop & Resistance-Aware Targets
- [x] Adaptive Matrix & Specialized Indicators (`scripts/adaptive_indicators.py`)
- [x] Continuous Integration & Ruff Quality Gates (100% Green)
- [ ] Intraday Breakout Scanner (10:45–11:00 ICT) for real-time sector surges
- [ ] NVDR Program Trading & Net Flow Divergence Filter
- [ ] Expansion of Automated Testing to Webhook Notifications (LINE Notify / Discord)
