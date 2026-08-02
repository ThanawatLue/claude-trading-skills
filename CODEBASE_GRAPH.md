# Codebase Graph: Claude Trading Skills (Architecture v2.0)

## 1. Architectural Overview
The repository `claude-trading-skills` is a decentralized ecosystem of **Claude/Gemini Skills** designed for quantitative and qualitative trading workflows. It features a **7-Step Dual-Market Dashboard** and an automated **Self-Improvement Loop**.

## 2. Tech Stack & Infrastructure
- **Core Language**: Python 3.9+ (Managed via `uv`).
- **Orchestration**: Custom Python scripts (`scripts/`) and `launchd` agents for automation.
- **Web Interface**: Flask-based **Trading Intelligence Dashboard** (`dashboard/app.py`) on Port 5050.
- **Database (SQLite)**: `state/market_cache.db` (Shared Price Cache + Analysis Run Snapshots).
- **Subprocess Protocol**: Forced `UTF-8` I/O for Windows compatibility (`PYTHONIOENCODING=utf-8`).
- **Data Ecosystem**:
    - **Free Tier Focus**: Yahoo Finance (`yfinance`), Wikipedia Scrape, and Public GitHub CSVs.
    - **Paid Tier Support**: Financial Modeling Prep (FMP) and FINVIZ Elite (Optional).

## 3. Core Nodes (Logic Hubs)

### 3.1. The Dashboard Hub (`dashboard/`)
- `app.py`: Flask backend managing:
    - **Snapshots**: Stores full analysis runs in the `analysis_run` table for instant history browsing.
    - **API Pipeline**: Runs all market-specific scripts in sequence to build a coherent state.
- `templates/dashboard.html`: Single-page UI with 7-step workflow (Breadth -> Distribution -> Exposure -> VCP -> Breakout -> Duration -> Earnings).

### 3.2. Parabolic Short Pipeline (`skills/parabolic-short-trade-planner/`)
- **Phase 1 (Screening)**: `screen_parabolic.py` - Identifies overextended stocks with 5-factor scoring.
- **Phase 2 (Planning)**: `generate_pre_market_plan.py` - Evaluates Alpaca inventory and SSR rules to emit actionable trigger plans.
- **Phase 3 (Monitoring)**: `monitor_intraday_trigger.py` - Walks a bar-based FSM to detect ORL breaks, VWAP fails, or First Red Bar entries.

### 3.3. Trader Memory Core (`skills/trader-memory-core/`)
- `thesis_ingest.py`: Registers skill outputs as "Theses" (IDEA -> ACTIVE -> CLOSED).
- `thesis_review.py`: Manages periodic reviews and generates postmortem journals with MAE/MFE tracking.

## 4. Central Logic & Data Flow Patterns
1. **Snapshot Pattern**: Script Run -> JSON Report -> `app.py` -> SQLite `analysis_run` -> Frontend 📅 Dropdown.
2. **Analysis Pipeline**: `Breadth` -> `VCP Screen` -> `Exposure Coach` -> `Breakout Plan`.
3. **Market Switching**: Frontend (`currentMarket`) -> API (`?market=TH`) -> Metadata-aware `latest_file()` filtering.

## 5. Technical Constraints & DNA
- **Public Repo Security**: No absolute paths or secrets in committed code.
- **Windows Reliability**: UTF-8 encoding forced for all cross-script communication.
- **Rate Limit Resilience**: Incremental price caching in SQLite to minimize API calls.

## 6. Automation & Maintenance
- **Self-Improvement Loop**: Daily cadence to review and improve skill prompts via `scripts/run_skill_improvement_loop.py`.
- **Auto-Generation Pipeline**: Weekly log mining to identify and build new skills as PRs.
