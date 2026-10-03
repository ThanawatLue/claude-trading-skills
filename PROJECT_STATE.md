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

## 6. US Market Autonomous Fund Expansion ($1,000 USD Starting Capital)

The autonomous engine has been expanded to trade US Equities (NYSE / NASDAQ) under fair, production-grade microstructural and fiscal rules:
1. **Capital Budget & Risk Sizing:**
   - Starting Capital: **$1,000.00 USD**
   - Allocation: Max 4 concurrent positions $\rightarrow$ Max **$250.00 USD** per slot
   - Risk Cap: 1.0% portfolio risk $\rightarrow$ Max **$10.00 USD** risk per trade
   - Granularity: Single-share execution (no 100-share board lot requirement)
2. **Accurate Regulatory Fee Deduction (Sell Exits):**
   - SEC Section 31 Fee: `$27.80` per `$1,000,000` gross proceeds (min `$0.01`, rounded up to next cent)
   - FINRA Trading Activity Fee (TAF): `$0.000166` per share (min `$0.01`, max `$8.30`, rounded to nearest cent)
3. **9 Thematic Clusters:**
   - AI Infrastructure & Semiconductors, Cloud Software & Cybersecurity, Mega-Cap Tech Platforms, Biotech & GLP-1, Nuclear Energy & Clean Power, Aerospace & Defense, FinTech & Crypto Infra, Consumer Discretionary, Energy & Oil Services.
4. **State Isolation:**
   - Thai Fund: `state/jules_tasks/`, `state/jules_orders/`, `state/jules_memory/`
   - US Fund: `state/jules_us_tasks/`, `state/jules_us_orders/`, `state/jules_us_memory/`

---

## 7. Two-Tier Scale-Out Exit Engine & Volatility Optimization (Win Rate 53.3%, PF 2.04)

Empirically proven via systematic multi-dimensional grid search across 42,695 historical price bars and deployed across both Thai (SET) and US funds:
1. **The Ratchet Trap Elimination:**
   - Previous rule moved stops to Breakeven at +0.5R, causing premature stops on 40%+ of winning runners that retest pivot levels.
   - New rule: Move Stop Loss to Breakeven *only after* T1 scale-out is executed.
2. **Two-Tier Scale-Out (50% @ T1, 50% @ T2):**
   - **T1 (1.5R):** Automatically scale out 50% of the position, bank realized profit, and adjust stop to Breakeven (+0.05R buffer).
   - **T2 (2.5R):** Let the remaining 50% runner ride to 2.5R with trailing ratchet active only after 2.0R (locking 1.0R).
3. **Volatility-Adjusted Stop Floor ($\ge 4.5\%$):**
   - Minimum stop width clamped to $\ge 4.5\%$ to prevent intraday market noise whipouts and transaction fee drag.
4. **Velocity Stall Exit (4 Days):**
   - Auto-exits stagnant positions if peak MFE $< 0.3R$ after 4 trading days, increasing capital efficiency.
5. **Quantitative Results:**
   - Win Rate elevated from **41.8% to 53.3%**.
   - Profit Factor elevated to **1.95 – 2.04**.
   - Net R significantly improved from negative to **+4.59R**.

---

## 8. 360-Degree End-to-End Stress Audit & Ecosystem Hardening (All 7 Dimensions)

A comprehensive 360-degree End-to-End audit was executed across all 7 operational layers using `scripts/audit_e2e_full_spectrum.py`. All discovered loopholes were surgically patched and verified:

1. **Dimension 1: Sizing & Lot Math Edge Cases:**
   - *Odd-Lot / Single Share (`shares == 1`):* Previously, `shares_closed = min(shares - 1, max(1, int(shares * fraction)))` returned 0 shares closed while marking scale-out as completed. Patched: For single-share positions (`shares == 1`), T1 now acts as capital protection: stop is advanced to Breakeven (+0.05R) without attempting a 0-share sale, allowing the single share to run risk-free to T2 (`single_share_protected = True`).
   - *Slot Budget Bounds:* Previously, `max(1, allowed_shares)` forced a 1-share buy for expensive stocks ($280 MSFT) even when exceeding the $250 slot budget. Patched: If `allowed_shares <= 0`, sizing returns `0, $0.00` and the candidate is rejected.
   - *SET Board Lot Integrity:* Enforces strict 100-share board lot constraints and rejects odd lots.

2. **Dimension 2: Order Lifecycle & Queue Safeguards:**
   - *Chase Limit Precision:* Exact enforcement at trigger + 1.0% with invalid orders moved to `quarantine/`.
   - *Corrupted File Isolation:* Invalid YAML/JSON syntax safely moved to `quarantine/` with `.error.json` diagnostics.
   - *Pre-Market Market-Aware TTL:* Orders staged pre-market (e.g. 08:30 ICT or 18:00 ICT for US) now remain valid through the market opening execution window (11:00 ICT for TH, 15:00 UTC / 10:30 ET for US) or `now + 45m`, eliminating premature order death before the opening bell.

3. **Dimension 3: Exit Engine & Mark-to-Market Realism:**
   - *Scale-Out Double-Entry Accounting:* Fixed net PnL and exit cost calculations in `close_position` and `scale_out_position` to ensure `gross_pnl - entry_cost - exit_cost == pnl` without missing remaining entry fees or partial scale-out exit fees.
   - *Discrete Snapshot Stop Execution:* Validated resting broker stop execution at `stop_price` modeling exchange order book fills during intraday crossings.
   - *Velocity Stall Exit:* Verified strict 4-day boundary cut when MFE $< 0.3R$.

4. **Dimension 4: Multi-Market State Isolation:**
   - Strict separation between TH (฿30,000 capital, 100-share board lots, InnovestX fees) and US ($1,000 capital, single-share lots, SEC/FINRA fees).
   - Dynamic path binding in `get_orders_dirs` preventing cross-market leakage.

5. **Dimension 5: Dashboard & REST APIs:**
   - Added missing endpoints: `/api/jules/status`, `/api/jules/scout` (mission), and `/api/market-posture`.
   - Verified 6/6 endpoints return 200 OK and valid JSON.

6. **Dimension 6: Data Feeds & Resiliency:**
   - Normalization for dotted tickers (`PBR.A`, `BRK.B`) converted to hyphenated format (`PBR-A`) for yfinance compatibility.
   - Verified SQLite WAL mode and 60,000ms busy timeout preventing concurrency lockouts.

7. **Dimension 7: Cloud VM Automation & US Cron Pipeline:**
   - Upgraded `run_gcp_morning_scout.sh`, `run_gcp_auto_decision.sh`, `run_gcp_order_processor.sh`, and `run_gcp_post_market.sh` to accept market parameter (`TH` or `US`).
   - Added US autonomous fund schedules to `setup_gcp_cron.sh` (12:30 UTC scout, 13:10 UTC decide, 14:15-19:45 UTC orders, 20:15 UTC evolve).

**Verification Baseline:**
- **360-Degree E2E Audit (`audit_e2e_full_spectrum.py`):** 13/13 passed in 1.06s.
- **Jules Test Suite:** 42/42 passed in 4.17s.
- **Full Repository Test Suite:** **3,222 passed in 59.70s with 0 errors!**

---

## 9. Active Roadmap & Completed Milestones

- [x] Autonomous Decision Engine (`scripts/jules_trader.py`)
- [x] Two-Tier Scale-Out Exit Engine & Post-T1 Breakeven Ratchet
- [x] Volatility-Adjusted Stop Floor ($\ge 4.5\%$) & Velocity Stall Exit (4 Days)
- [x] Adaptive Matrix & Specialized Indicators (`scripts/adaptive_indicators.py`)
- [x] Continuous Integration & Ruff Quality Gates (100% Green, 3,222 tests passing)
- [x] US Equities Autonomous Fund Expansion ($1,000 USD fund, SEC/FINRA fees, US Thematic Clusters)
- [x] 360-Degree E2E Full-Spectrum Audit & Hardening (All 7 Dimensions)
- [x] US Market VM Cron Pipeline scripts and crontab definitions
- [x] Real-Time Multi-Channel Notification Service (`scripts/notify_service.py` - Telegram, Discord, LINE Notify)
- [x] NVDR Program Trading & Net Flow Divergence Filter (`scripts/nvdr_flow_filter.py` - Bull Trap rejection & Institutional Accumulation scoring)
- [x] Intraday Breakout & Volume Surge Scanner (`scripts/intraday_breakout_scanner.py` - ORB-30/45 with RVOL $\ge 1.5\times$ and GCP crontab schedules)
- [x] Multi-Dimensional Market Intelligence Filter & Political/News Gate (`scripts/market_intelligence_filter.py` - Real-time news sentiment red-flag scan, binary event earnings calendar gate, foreign SOE political risk gate, benchmark relative strength modifier, overhead supply 200 SMA clearance, and dollar volume liquidity floor)
- [x] Institutional Historical Backtest & Multi-Generation Replay Engine (`scripts/run_historical_backtest.py` - Dual-market 18-month simulation across 113,000+ price bars with zero lookahead bias, tick slippage, fee modeling, and multi-regime exposure testing)

