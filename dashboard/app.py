"""Trading Intelligence Dashboard - Flask Backend"""

import concurrent.futures
import glob
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Load environment variables from .env manually
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DASHBOARD_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                val = val.strip().strip("'").strip('"')
                os.environ[key.strip()] = val

import hf_sync
import yfinance as yf
from flask import Flask, Response, jsonify, render_template, request

from scripts import auto_paper, run_daily_signal_pipeline, signal_ledger
from scripts.fee_model import effective_transaction_cost_bps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "skills", "paper-trade-simulator", "scripts"))
from paper_trade import (
    VALID_EMOTIONS,
)
from paper_trade import (
    add_journal as paper_journal,
)
from paper_trade import (
    check_discipline_warnings as paper_discipline_check,
)
from paper_trade import (
    close_position as paper_close,
)
from paper_trade import (
    compute_stats as paper_stats,
)
from paper_trade import (
    compute_fingerprints as paper_fingerprints,
)
from paper_trade import (
    list_positions as paper_list,
)
from paper_trade import (  # noqa: E402
    open_position as paper_open,
)
from update_marks import update_all as paper_update_marks  # noqa: E402

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
ROOT_DIR = BASE_DIR  # market breadth files land here
DB_PATH = os.path.join(BASE_DIR, "state", "market_cache.db")

# Subprocess environment: force UTF-8 I/O so emoji/unicode in scripts don't crash on Windows
# Set PYTHONPATH so spawned subprocesses can find the shared 'scripts.lib' and 'tv_client' packages
_SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}
_project_paths = [BASE_DIR, os.path.join(BASE_DIR, "scripts", "lib")]
_existing_pythonpath = os.environ.get("PYTHONPATH", "")
if _existing_pythonpath:
    _SUBPROCESS_ENV["PYTHONPATH"] = os.pathsep.join(_project_paths + [_existing_pythonpath])
else:
    _SUBPROCESS_ENV["PYTHONPATH"] = os.pathsep.join(_project_paths)


app = Flask(__name__)

# Try downloading database from HF on startup
hf_sync.download_db()

# ── Report Database ────────────────────────────────────────────────────────────

_RUN_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_run (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    market  TEXT    NOT NULL,
    run_at  TEXT    NOT NULL,
    data    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_run_market_at ON analysis_run(market, run_at DESC);
"""


def _db() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=60.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(_RUN_SCHEMA)
    return conn


def _clean_nan(obj):
    """Recursively replace NaN/Inf with None — JS JSON.parse rejects them."""
    import math

    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_nan(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def db_save_run(market: str, data: dict) -> str:
    """Save a full analysis snapshot to DB. Returns the run_at timestamp."""
    run_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with _db() as conn:
        conn.execute(
            "INSERT INTO analysis_run (market, run_at, data) VALUES (?,?,?)",
            (market, run_at, json.dumps(_clean_nan(data), ensure_ascii=False)),
        )
    hf_sync.upload_db()
    return run_at


def db_load_run(market: str, at: str | None = None) -> dict | None:
    """Load a snapshot: latest if at=None, specific timestamp otherwise.

    Defensively cleans NaN/Infinity from legacy rows so the JSON response is
    valid for browser consumers (JS JSON.parse rejects NaN).
    """
    with _db() as conn:
        if at:
            row = conn.execute(
                "SELECT data FROM analysis_run WHERE market=? AND run_at=? LIMIT 1",
                (market, at),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT data FROM analysis_run WHERE market=? ORDER BY run_at DESC LIMIT 1",
                (market,),
            ).fetchone()
    if not row:
        return None
    return _clean_nan(json.loads(row["data"]))


def db_list_runs(market: str, limit: int = 50) -> list[str]:
    """Return list of run timestamps for a market, newest first."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT run_at FROM analysis_run WHERE market=? ORDER BY run_at DESC LIMIT ?",
            (market, limit),
        ).fetchall()
    return [r["run_at"] for r in rows]


# ── File helpers (fallback when DB has no data yet) ───────────────────────────


def latest_file(pattern: str, market: str = "US") -> str | None:
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        return None
    for f in files:
        try:
            with open(f, encoding="utf-8") as j:
                data = json.load(j)
                if isinstance(data, list):
                    return f if market == "US" else None

                # Extract market from metadata
                meta = data.get("metadata", {})
                m = meta.get("market")

                # Fallback 1: canslim screening_options
                if not m:
                    m = meta.get("screening_options", {}).get("market")

                # Fallback 2: breakout_plan input_metadata or symbol suffix
                if not m:
                    input_meta = data.get("input_metadata", {})
                    src_file = input_meta.get("source_file", "")
                    if "vcp_screener_" in src_file:
                        has_th = False
                        for k in ["actionable_orders", "rejected", "watchlist"]:
                            if data.get(k):
                                for item in data[k]:
                                    sym = item.get("symbol", "")
                                    if sym.endswith(".BK"):
                                        has_th = True
                                        break
                        m = "TH" if has_th else "US"
                    else:
                        m = input_meta.get("market")

                # Default to US if not resolved
                if not m:
                    m = "US"

                if m.upper() == market.upper():
                    return f
        except Exception:
            continue
    return None


def latest_file_any(pattern: str) -> str | None:
    """Pick newest matching file that parses as valid JSON; skip corrupted ones."""
    files = sorted(glob.glob(pattern), reverse=True)
    for f in files:
        try:
            with open(f, encoding="utf-8") as j:
                json.load(j)
            return f
        except Exception as e:
            print(f"Skipping corrupted file {f}: {e}", file=sys.stderr)
            continue
    return None


def load_json(path: str) -> dict | list | None:
    """Load JSON file defensively — returns None on any error (missing or corrupted)."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"load_json error on {path}: {e}", file=sys.stderr)
        return None


def _collect_snapshot(market: str) -> dict:
    """Read all latest JSON files and build a snapshot dict."""
    breadth = load_json(
        latest_file(os.path.join(ROOT_DIR, "market_breadth_20[0-9][0-9]-*.json"), market)
    )
    vcp = load_json(latest_file(os.path.join(REPORTS_DIR, "vcp_screener_*.json"), market))
    exposure = load_json(latest_file(os.path.join(REPORTS_DIR, "exposure_posture_*.json"), market))
    ibd = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "ibd_distribution_day_monitor_*.json"))
    )
    earnings_trade = load_json(latest_file_any(os.path.join(REPORTS_DIR, "earnings_trade_*.json")))
    breakout_plan = load_json(
        latest_file(os.path.join(REPORTS_DIR, "breakout_trade_plan_*.json"), market)
    )
    uptrend = load_json(latest_file_any(os.path.join(REPORTS_DIR, "uptrend_analysis_*.json")))
    downtrend = load_json(latest_file_any(os.path.join(REPORTS_DIR, "downtrend_analysis_*.json")))
    canslim = load_json(latest_file(os.path.join(REPORTS_DIR, "canslim_screener_*.json"), market))
    thai_swing = load_json(latest_file_any(os.path.join(REPORTS_DIR, "thai_swing_*.json")))
    # NEW: TV-powered Thai skills
    thai_sector_heatmap = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "thai_sector_heatmap_*.json"))
    )
    thai_breadth = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "thai_market_breadth_*.json"))
    )
    thai_watchlists = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "thai_watchlists_*.json"))
    )
    thai_dividends = load_json(latest_file_any(os.path.join(REPORTS_DIR, "thai_dividends_*.json")))

    # NEW: TV-powered US skills
    us_sector_heatmap = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "us_sector_heatmap_*.json"))
    )
    us_breadth_tv = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "us_market_breadth_tv_*.json"))
    )
    us_watchlists = load_json(
        latest_file_any(os.path.join(REPORTS_DIR, "us_watchlists_*.json"))
    )
    us_dividends = load_json(latest_file_any(os.path.join(REPORTS_DIR, "us_dividends_*.json")))

    return {
        "market": market,
        "breadth": breadth,
        "vcp": vcp,
        "exposure": exposure,
        "ibd": ibd,
        "earnings_trade": earnings_trade,
        "breakout_plan": breakout_plan,
        "uptrend": uptrend,
        "downtrend": downtrend,
        "canslim": canslim,
        "thai_swing": thai_swing,
        "thai_sector_heatmap": thai_sector_heatmap,
        "thai_breadth": thai_breadth,
        "thai_watchlists": thai_watchlists,
        "thai_dividends": thai_dividends,
        "us_sector_heatmap": us_sector_heatmap,
        "us_breadth_tv": us_breadth_tv,
        "us_watchlists": us_watchlists,
        "us_dividends": us_dividends,
    }


def _merge_live_snapshot(stored: dict, fresh: dict) -> dict:
    """Overlay fresh report values on the last stored snapshot.

    The database snapshot remains a fallback for reports that are not present
    yet, but a report that does exist must win.  Otherwise the dashboard can
    keep showing an old DB value after a new scanner report has been written.
    """

    def merge(old, new):
        if isinstance(old, dict) and isinstance(new, dict):
            result = dict(old)
            for key, value in new.items():
                if value is not None:
                    result[key] = merge(result.get(key), value)
            return result
        return new if new is not None else old

    return merge(stored or {}, fresh or {})


def cleanup_old_files(keep_count: int = 2):
    """Keep only the latest keep_count files matching each analysis output pattern."""
    patterns = [
        # Root directory patterns
        os.path.join(ROOT_DIR, "market_breadth_20[0-9][0-9]-*.json"),
        os.path.join(ROOT_DIR, "market_breadth_20[0-9][0-9]-*.md"),
        os.path.join(ROOT_DIR, "canslim_screener_*.json"),
        os.path.join(ROOT_DIR, "canslim_screener_*.md"),
        # Reports directory patterns
        os.path.join(REPORTS_DIR, "vcp_screener_*.json"),
        os.path.join(REPORTS_DIR, "vcp_screener_*.md"),
        os.path.join(REPORTS_DIR, "exposure_posture_*.json"),
        os.path.join(REPORTS_DIR, "exposure_posture_*.md"),
        os.path.join(REPORTS_DIR, "ibd_distribution_day_monitor_*.json"),
        os.path.join(REPORTS_DIR, "ibd_distribution_day_monitor_*.md"),
        os.path.join(REPORTS_DIR, "earnings_trade_*.json"),
        os.path.join(REPORTS_DIR, "earnings_trade_*.md"),
        os.path.join(REPORTS_DIR, "breakout_trade_plan_*.json"),
        os.path.join(REPORTS_DIR, "breakout_trade_plan_*.md"),
        os.path.join(REPORTS_DIR, "uptrend_analysis_*.json"),
        os.path.join(REPORTS_DIR, "uptrend_analysis_*.md"),
        os.path.join(REPORTS_DIR, "downtrend_analysis_*.json"),
        os.path.join(REPORTS_DIR, "downtrend_analysis_*.md"),
        os.path.join(REPORTS_DIR, "canslim_screener_*.json"),
        os.path.join(REPORTS_DIR, "canslim_screener_*.md"),
        os.path.join(REPORTS_DIR, "thai_swing_*.json"),
        os.path.join(REPORTS_DIR, "thai_swing_*.md"),
        os.path.join(REPORTS_DIR, "thai_sector_heatmap_*.json"),
        os.path.join(REPORTS_DIR, "thai_sector_heatmap_*.md"),
        os.path.join(REPORTS_DIR, "thai_market_breadth_*.json"),
        os.path.join(REPORTS_DIR, "thai_market_breadth_*.md"),
        os.path.join(REPORTS_DIR, "thai_watchlists_*.json"),
        os.path.join(REPORTS_DIR, "thai_watchlists_*.md"),
        os.path.join(REPORTS_DIR, "thai_dividends_*.json"),
        os.path.join(REPORTS_DIR, "thai_dividends_*.md"),
        os.path.join(REPORTS_DIR, "us_sector_heatmap_*.json"),
        os.path.join(REPORTS_DIR, "us_sector_heatmap_*.md"),
        os.path.join(REPORTS_DIR, "us_market_breadth_tv_*.json"),
        os.path.join(REPORTS_DIR, "us_market_breadth_tv_*.md"),
        os.path.join(REPORTS_DIR, "us_watchlists_*.json"),
        os.path.join(REPORTS_DIR, "us_watchlists_*.md"),
        os.path.join(REPORTS_DIR, "us_dividends_*.json"),
        os.path.join(REPORTS_DIR, "us_dividends_*.md"),
        os.path.join(REPORTS_DIR, "skill_review_*.json"),
        os.path.join(REPORTS_DIR, "skill_review_*.md"),
    ]
    for pattern in patterns:
        files = sorted(glob.glob(pattern), reverse=True)
        if len(files) > keep_count:
            for f in files[keep_count:]:
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"Error removing {f}: {e}", file=sys.stderr)


def build_exposure_cmd(latest_mb: str, market: str) -> list[str]:
    """Build the command to run the exposure coach with all available dimensions."""
    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "skills", "exposure-coach", "scripts", "calculate_exposure.py"),
        "--market",
        market,
        "--breadth",
        latest_mb,
    ]
    latest_uptrend = latest_file_any(os.path.join(REPORTS_DIR, "uptrend_analysis_*.json"))
    if latest_uptrend:
        cmd.extend(["--uptrend", latest_uptrend])

    if market == "US":
        latest_top = latest_file_any(os.path.join(REPORTS_DIR, "market_top_*.json"))
        if latest_top:
            cmd.extend(["--top-risk", latest_top])
        else:
            latest_ibd = latest_file_any(
                os.path.join(REPORTS_DIR, "ibd_distribution_day_monitor_*.json")
            )
            if latest_ibd:
                cmd.extend(["--top-risk", latest_ibd])
    return cmd


def clean_unsuccessful_db_runs():
    """Scan SQLite analysis_run table and remove runs that are unsuccessful or incomplete."""
    try:
        db_path = DB_PATH
        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute("SELECT id, market, run_at, data FROM analysis_run").fetchall()
        to_delete = []

        for row in rows:
            run_id = row["id"]
            try:
                data = json.loads(row["data"])
            except Exception:
                to_delete.append(run_id)
                continue

            breadth = data.get("breadth")
            vcp = data.get("vcp")
            exposure = data.get("exposure")

            is_unsuccessful = False
            if not breadth or not isinstance(breadth, dict) or not breadth.get("composite"):
                is_unsuccessful = True
            elif not vcp or not isinstance(vcp, dict):
                is_unsuccessful = True
            elif (
                not exposure or not isinstance(exposure, dict) or not exposure.get("recommendation")
            ):
                is_unsuccessful = True

            if is_unsuccessful:
                to_delete.append(run_id)

        if to_delete:
            cursor.execute(
                f"DELETE FROM analysis_run WHERE id IN ({','.join(map(str, to_delete))})"
            )
            conn.commit()
            print(
                f"Cleaned up {len(to_delete)} unsuccessful/incomplete runs from database.",
                file=sys.stderr,
            )

        conn.close()
    except Exception as e:
        print(f"Error during DB cleaning: {e}", file=sys.stderr)


def run_signal_pipeline_followup(market: str) -> dict:
    """Run signal ledger/outcome/auto-paper maintenance after a fresh scan."""
    import time

    start_t = time.time()
    try:
        config = run_daily_signal_pipeline.load_config(
            os.path.join(BASE_DIR, "state", "automation_config.yaml")
        )
        config["market"] = market.upper()
        config.setdefault("analysis", {})["enabled"] = False
        result = run_daily_signal_pipeline.run_pipeline(config, write_output=True)
        try:
            hf_sync.upload_db()
        except Exception as sync_error:
            print(
                f"Warning: HF DB upload after signal pipeline failed: {sync_error}", file=sys.stderr
            )
        elapsed = round(time.time() - start_t, 1)
        auto_result = result.get("auto_paper") or {}
        signal_counts = result.get("signals") or {}
        return {
            "cmd": "run_daily_signal_pipeline.py",
            "ok": True,
            "out": (
                f"signals={signal_counts.get('total', 0)}, "
                f"completed={signal_counts.get('completed_signals', 0)}, "
                f"auto_eligible={auto_result.get('eligible', 0)}, "
                f"opened={auto_result.get('opened', 0)}"
            ),
            "err": "",
            "elapsed": elapsed,
            "reports": result.get("reports", {}),
        }
    except Exception as e:
        elapsed = round(time.time() - start_t, 1)
        return {
            "cmd": "run_daily_signal_pipeline.py",
            "ok": False,
            "out": "",
            "err": str(e),
            "elapsed": elapsed,
        }


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/health")
def api_health():
    commit = "unknown"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
    except Exception:
        pass

    return jsonify(
        {
            "status": "ok",
            "service": "tong-trading-dashboard",
            "commit": commit,
            "commit_short": commit[:7] if commit != "unknown" else commit,
            "features": {
                "signal_results": True,
                "manual_run_signal_followup": True,
            },
        }
    )


@app.route("/api/data")
def api_data():
    market = request.args.get("market", "US").upper()
    at = request.args.get("at")  # optional ISO timestamp for historical view

    if at:
        # Historical view: only DB (no fallback to files)
        snapshot = db_load_run(market, at)
        if not snapshot:
            return jsonify({"error": f"No data for {market} at {at}"}), 404
        return jsonify(_clean_nan(snapshot))

    # Live view: use the latest report files and retain the DB snapshot only as
    # a fallback for sections that are not available yet.
    snapshot = db_load_run(market)
    if snapshot:
        fresh = _collect_snapshot(market)
        return jsonify(_clean_nan(_merge_live_snapshot(snapshot, fresh)))

    return jsonify(_clean_nan(_collect_snapshot(market)))


@app.route("/api/runs")
def api_runs():
    """List past run timestamps for a market."""
    market = request.args.get("market", "US").upper()
    limit = int(request.args.get("limit", 50))
    runs = db_list_runs(market, limit)
    return jsonify({"market": market, "runs": runs})


@app.route("/api/run")
def api_run():
    """Re-run analysis scripts for a specific market, then snapshot to DB."""
    market = request.args.get("market", "US").upper()
    account_size = request.args.get("account_size", "50000")
    risk_pct = request.args.get("risk_pct", "0.5")
    target_r = request.args.get("target_r", "2.0")

    log = []

    def _run(cmd, timeout=300, extra_env=None):
        import time

        start_t = time.time()
        env = {**_SUBPROCESS_ENV, **(extra_env or {})}
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=BASE_DIR,
                timeout=timeout,
                env=env,
            )
            elapsed = round(time.time() - start_t, 1)
            return {
                "cmd": os.path.basename(cmd[1]),
                "ok": r.returncode == 0,
                "out": r.stdout[-1000:],
                "err": r.stderr[-1500:],
                "elapsed": elapsed,
            }
        except subprocess.TimeoutExpired:
            elapsed = round(time.time() - start_t, 1)
            return {
                "cmd": os.path.basename(cmd[1]),
                "ok": False,
                "out": "",
                "err": f"Timeout after {timeout}s",
                "elapsed": elapsed,
            }
        except Exception as e:
            elapsed = round(time.time() - start_t, 1)
            return {
                "cmd": os.path.basename(cmd[1]),
                "ok": False,
                "out": "",
                "err": str(e),
                "elapsed": elapsed,
            }

    # ── Phase 1: Heavy Primary Scanners (Parallel Execution) ──────────────────────
    primary_tasks = [
        # 1. Market Breadth Analyzer
        (
            [
                sys.executable,
                os.path.join(
                    BASE_DIR,
                    "skills",
                    "market-breadth-analyzer",
                    "scripts",
                    "market_breadth_analyzer.py",
                ),
                "--market",
                market,
            ],
            300,
            None,
        ),
        # 2. VCP Screener
        (
            [
                sys.executable,
                os.path.join(BASE_DIR, "skills", "vcp-screener", "scripts", "screen_vcp.py"),
                "--market",
                market,
                "--max-candidates",
                "100",
                "--top",
                "100",
            ],
            600,
            None,
        ),
        # 3. Uptrend Analyzer
        (
            [
                sys.executable,
                os.path.join(
                    BASE_DIR, "skills", "uptrend-analyzer", "scripts", "uptrend_analyzer.py"
                ),
                "--output-dir",
                REPORTS_DIR,
            ],
            120,
            None,
        ),
        # 4. Downtrend Duration Analyzer
        (
            [
                sys.executable,
                os.path.join(
                    BASE_DIR,
                    "skills",
                    "downtrend-duration-analyzer",
                    "scripts",
                    "analyze_downtrends.py",
                ),
                "--max-stocks",
                "30",
                "--output-dir",
                REPORTS_DIR,
            ],
            300,
            None,
        ),
    ]

    # 5. CANSLIM Screener (supports both US and TH markets)
    primary_tasks.append(
        (
            [
                sys.executable,
                os.path.join(
                    BASE_DIR, "skills", "canslim-screener", "scripts", "screen_canslim.py"
                ),
                "--market",
                market,
                "--max-candidates",
                "40",
                "--top",
                "40",
                "--output-dir",
                REPORTS_DIR,
            ],
            600,
            None,
        )
    )

    if market == "US":
        primary_tasks.extend(
            [
                # 6. IBD Distribution Day Monitor (US only)
                (
                    [
                        sys.executable,
                        os.path.join(
                            BASE_DIR,
                            "skills",
                            "ibd-distribution-day-monitor",
                            "scripts",
                            "ibd_monitor.py",
                        ),
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    60,
                    None,
                ),
                # 7. Earnings Trade Analyzer (US only)
                (
                    [
                        sys.executable,
                        os.path.join(
                            BASE_DIR,
                            "skills",
                            "earnings-trade-analyzer",
                            "scripts",
                            "analyze_earnings_trades.py",
                        ),
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    600,
                    None,
                ),
                # 8-11. TV-powered US skills (parallel, no API key required)
                (
                    [
                        sys.executable,
                        os.path.join(BASE_DIR, "skills", "us-sector-heatmap", "scripts", "generate_us_heatmap.py"),
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    120,
                    None,
                ),
                (
                    [
                        sys.executable,
                        os.path.join(BASE_DIR, "skills", "us-breadth-analyzer-tv", "scripts", "analyze_us_breadth_tv.py"),
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    120,
                    None,
                ),
                (
                    [
                        sys.executable,
                        os.path.join(BASE_DIR, "skills", "us-watchlist-builder", "scripts", "build_us_watchlists.py"),
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    120,
                    None,
                ),
                (
                    [
                        sys.executable,
                        os.path.join(BASE_DIR, "skills", "us-dividend-screener", "scripts", "screen_us_dividends.py"),
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    120,
                    None,
                ),
            ]
        )

    if market == "TH":
        # 6. Thai Swing Screener (TH only) — in vcp-screener skill
        thai_swing_script = os.path.join(
            BASE_DIR, "skills", "vcp-screener", "scripts", "screen_thai_swing.py"
        )
        if os.path.exists(thai_swing_script):
            primary_tasks.append(
                ([sys.executable, thai_swing_script, "--output-dir", REPORTS_DIR], 180, None)
            )
        # 7-10. TV-powered Thai skills (parallel, no API key required)
        tv_th_skills = [
            ("thai-sector-heatmap", "generate_heatmap.py"),
            ("thai-breadth-analyzer", "analyze_thai_breadth.py"),
            ("thai-watchlist-builder", "build_watchlists.py"),
            ("thai-dividend-screener", "screen_thai_dividends.py"),
        ]
        for skill_name, script_name in tv_th_skills:
            script_path = os.path.join(BASE_DIR, "skills", skill_name, "scripts", script_name)
            if os.path.exists(script_path):
                primary_tasks.append(
                    ([sys.executable, script_path, "--output-dir", REPORTS_DIR], 120, None)
                )

    print(
        f"Starting Phase 1 parallel execution with {len(primary_tasks)} independent scanners...",
        file=sys.stderr,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(primary_tasks)) as executor:
        futures = {
            executor.submit(_run, cmd, timeout, env): cmd for cmd, timeout, env in primary_tasks
        }
        for future in concurrent.futures.as_completed(futures):
            log.append(future.result())

    # ── Phase 2: Dependent Planners (Parallel Execution) ─────────────────────────
    latest_mb = latest_file(os.path.join(ROOT_DIR, "market_breadth_20[0-9][0-9]-*.json"), market)
    latest_vcp = latest_file(os.path.join(REPORTS_DIR, "vcp_screener_*.json"), market)

    dependent_tasks = []

    if latest_mb:
        # 1. Exposure Coach (needs fresh market breadth output)
        dependent_tasks.append(
            (
                build_exposure_cmd(latest_mb, market),
                60,
                None,
            )
        )
    else:
        log.append(
            {
                "cmd": "calculate_exposure.py",
                "ok": False,
                "out": "",
                "err": "No market breadth output found — run market breadth analyzer first",
            }
        )

    if latest_vcp:
        # 2. Breakout Trade Planner (needs fresh VCP screener output)
        dependent_tasks.append(
            (
                [
                    sys.executable,
                    os.path.join(
                        BASE_DIR,
                        "skills",
                        "breakout-trade-planner",
                        "scripts",
                        "plan_breakout_trades.py",
                    ),
                    "--input",
                    latest_vcp,
                    "--account-size",
                    account_size,
                    "--risk-pct",
                    risk_pct,
                    "--target-r-multiple",
                    target_r,
                    "--output-dir",
                    REPORTS_DIR,
                ],
                60,
                None,
            )
        )
    else:
        log.append(
            {
                "cmd": "plan_breakout_trades.py",
                "ok": False,
                "out": "",
                "err": "No VCP screener output found",
            }
        )

    if dependent_tasks:
        print(
            f"Starting Phase 2 parallel execution with {len(dependent_tasks)} dependent planners...",
            file=sys.stderr,
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(dependent_tasks)) as executor:
            futures = {
                executor.submit(_run, cmd, timeout, env): cmd
                for cmd, timeout, env in dependent_tasks
            }
            for future in concurrent.futures.as_completed(futures):
                log.append(future.result())
    else:
        print(
            "Phase 2 skipped — no dependent tasks (breadth and VCP both failed).", file=sys.stderr
        )

    # Save snapshot to DB if successful
    snapshot = _collect_snapshot(market)

    # Verify if the run was successful (must have valid breadth and vcp data)
    breadth = snapshot.get("breadth")
    vcp = snapshot.get("vcp")
    is_success = (
        breadth
        and isinstance(breadth, dict)
        and breadth.get("composite")
        and vcp
        and isinstance(vcp, dict)
    )

    if is_success:
        run_at = db_save_run(market, snapshot)
        status = "success"
    else:
        run_at = None
        status = "failed"
        print(
            f"Warning: Run at {datetime.now().isoformat()} was unsuccessful and not saved to DB.",
            file=sys.stderr,
        )

    signal_pipeline_result = run_signal_pipeline_followup(market)
    log.append(signal_pipeline_result)

    cleanup_old_files(keep_count=2)
    clean_unsuccessful_db_runs()

    return jsonify(
        {
            "status": status,
            "market": market,
            "run_at": run_at,
            "log": log,
            "signal_pipeline": signal_pipeline_result,
        }
    )


@app.route("/api/run/stream")
def api_run_stream():
    """Re-run analysis scripts and stream progress via SSE."""
    market = request.args.get("market", "US").upper()
    account_size = request.args.get("account_size", "50000")
    risk_pct = request.args.get("risk_pct", "0.5")
    target_r = request.args.get("target_r", "2.0")

    def g():
        log = []

        def _run(cmd, timeout=300, extra_env=None):
            import time

            start_t = time.time()
            env = {**_SUBPROCESS_ENV, **(extra_env or {})}
            try:
                r = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=BASE_DIR,
                    timeout=timeout,
                    env=env,
                )
                elapsed = round(time.time() - start_t, 1)
                return {
                    "cmd": os.path.basename(cmd[1]),
                    "ok": r.returncode == 0,
                    "out": r.stdout[-1000:],
                    "err": r.stderr[-1500:],
                    "elapsed": elapsed,
                }
            except subprocess.TimeoutExpired:
                elapsed = round(time.time() - start_t, 1)
                return {
                    "cmd": os.path.basename(cmd[1]),
                    "ok": False,
                    "out": "",
                    "err": f"Timeout after {timeout}s",
                    "elapsed": elapsed,
                }
            except Exception as e:
                elapsed = round(time.time() - start_t, 1)
                return {
                    "cmd": os.path.basename(cmd[1]),
                    "ok": False,
                    "out": "",
                    "err": str(e),
                    "elapsed": elapsed,
                }

        # ── Phase 1: Heavy Primary Scanners (Parallel Execution) ──────────────────────
        primary_tasks = [
            # 1. Market Breadth Analyzer
            (
                [
                    sys.executable,
                    os.path.join(
                        BASE_DIR,
                        "skills",
                        "market-breadth-analyzer",
                        "scripts",
                        "market_breadth_analyzer.py",
                    ),
                    "--market",
                    market,
                ],
                300,
                None,
            ),
            # 2. VCP Screener
            (
                [
                    sys.executable,
                    os.path.join(BASE_DIR, "skills", "vcp-screener", "scripts", "screen_vcp.py"),
                    "--market",
                    market,
                    "--max-candidates",
                    "100",
                    "--top",
                    "100",
                ],
                300,
                None,
            ),
            # 3. Uptrend Analyzer
            (
                [
                    sys.executable,
                    os.path.join(
                        BASE_DIR, "skills", "uptrend-analyzer", "scripts", "uptrend_analyzer.py"
                    ),
                    "--output-dir",
                    REPORTS_DIR,
                ],
                120,
                None,
            ),
            # 4. Downtrend Duration Analyzer
            (
                [
                    sys.executable,
                    os.path.join(
                        BASE_DIR,
                        "skills",
                        "downtrend-duration-analyzer",
                        "scripts",
                        "analyze_downtrends.py",
                    ),
                    "--max-stocks",
                    "30",
                    "--output-dir",
                    REPORTS_DIR,
                ],
                300,
                None,
            ),
        ]

        # 5. CANSLIM Screener
        primary_tasks.append(
            (
                [
                    sys.executable,
                    os.path.join(
                        BASE_DIR, "skills", "canslim-screener", "scripts", "screen_canslim.py"
                    ),
                    "--market",
                    market,
                    "--max-candidates",
                    "40",
                    "--top",
                    "40",
                    "--output-dir",
                    REPORTS_DIR,
                ],
                300,
                None,
            )
        )

        if market == "US":
            primary_tasks.extend(
                [
                    # 6. IBD Distribution Day Monitor (US only)
                    (
                        [
                            sys.executable,
                            os.path.join(
                                BASE_DIR,
                                "skills",
                                "ibd-distribution-day-monitor",
                                "scripts",
                                "ibd_monitor.py",
                            ),
                            "--output-dir",
                            REPORTS_DIR,
                        ],
                        60,
                        None,
                    ),
                    # 7. Earnings Trade Analyzer (US only)
                    (
                        [
                            sys.executable,
                            os.path.join(
                                BASE_DIR,
                                "skills",
                                "earnings-trade-analyzer",
                                "scripts",
                                "analyze_earnings_trades.py",
                            ),
                            "--output-dir",
                            REPORTS_DIR,
                        ],
                        600,
                        None,
                    ),
                    # 8-11. TV-powered US skills (parallel, no API key required)
                    (
                        [
                            sys.executable,
                            os.path.join(BASE_DIR, "skills", "us-sector-heatmap", "scripts", "generate_us_heatmap.py"),
                            "--output-dir",
                            REPORTS_DIR,
                        ],
                        120,
                        None,
                    ),
                    (
                        [
                            sys.executable,
                            os.path.join(BASE_DIR, "skills", "us-breadth-analyzer-tv", "scripts", "analyze_us_breadth_tv.py"),
                            "--output-dir",
                            REPORTS_DIR,
                        ],
                        120,
                        None,
                    ),
                    (
                        [
                            sys.executable,
                            os.path.join(BASE_DIR, "skills", "us-watchlist-builder", "scripts", "build_us_watchlists.py"),
                            "--output-dir",
                            REPORTS_DIR,
                        ],
                        120,
                        None,
                    ),
                    (
                        [
                            sys.executable,
                            os.path.join(BASE_DIR, "skills", "us-dividend-screener", "scripts", "screen_us_dividends.py"),
                            "--output-dir",
                            REPORTS_DIR,
                        ],
                        120,
                        None,
                    ),
                ]
            )

        if market == "TH":
            # 6. Thai Swing Screener (TH only)
            thai_swing_script = os.path.join(
                BASE_DIR, "skills", "vcp-screener", "scripts", "screen_thai_swing.py"
            )
            if os.path.exists(thai_swing_script):
                primary_tasks.append(
                    ([sys.executable, thai_swing_script, "--output-dir", REPORTS_DIR], 180, None)
                )
            # 7-10. TV-powered Thai skills
            tv_th_skills = [
                ("thai-sector-heatmap", "generate_heatmap.py"),
                ("thai-breadth-analyzer", "analyze_thai_breadth.py"),
                ("thai-watchlist-builder", "build_watchlists.py"),
                ("thai-dividend-screener", "screen_thai_dividends.py"),
            ]
            for skill_name, script_name in tv_th_skills:
                script_path = os.path.join(BASE_DIR, "skills", skill_name, "scripts", script_name)
                if os.path.exists(script_path):
                    primary_tasks.append(
                        ([sys.executable, script_path, "--output-dir", REPORTS_DIR], 120, None)
                    )

        # Count dependent tasks to get total
        total_tasks = len(primary_tasks) + 3  # Exposure, breakout planner, signal pipeline

        # Yield start event
        yield f"event: start\ndata: {json.dumps({'total_tasks': total_tasks})}\n\n"

        # Phase 1 Parallel Execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(primary_tasks)) as executor:
            futures = {
                executor.submit(_run, cmd, timeout, env): cmd for cmd, timeout, env in primary_tasks
            }
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                log.append(res)
                yield f"event: task_done\ndata: {json.dumps(res)}\n\n"

        # Phase 2
        latest_mb = latest_file(
            os.path.join(ROOT_DIR, "market_breadth_20[0-9][0-9]-*.json"), market
        )
        latest_vcp = latest_file(os.path.join(REPORTS_DIR, "vcp_screener_*.json"), market)

        dependent_tasks = []
        if latest_mb:
            dependent_tasks.append(
                (
                    build_exposure_cmd(latest_mb, market),
                    60,
                    None,
                )
            )
        else:
            res = {
                "cmd": "calculate_exposure.py",
                "ok": False,
                "out": "",
                "err": "No market breadth output found — run market breadth analyzer first",
            }
            log.append(res)
            yield f"event: task_done\ndata: {json.dumps(res)}\n\n"

        if latest_vcp:
            dependent_tasks.append(
                (
                    [
                        sys.executable,
                        os.path.join(
                            BASE_DIR,
                            "skills",
                            "breakout-trade-planner",
                            "scripts",
                            "plan_breakout_trades.py",
                        ),
                        "--input",
                        latest_vcp,
                        "--account-size",
                        account_size,
                        "--risk-pct",
                        risk_pct,
                        "--target-r-multiple",
                        target_r,
                        "--output-dir",
                        REPORTS_DIR,
                    ],
                    60,
                    None,
                )
            )
        else:
            res = {
                "cmd": "plan_breakout_trades.py",
                "ok": False,
                "out": "",
                "err": "No VCP screener output found",
            }
            log.append(res)
            yield f"event: task_done\ndata: {json.dumps(res)}\n\n"

        if dependent_tasks:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(dependent_tasks)
            ) as executor:
                futures = {
                    executor.submit(_run, cmd, timeout, env): cmd
                    for cmd, timeout, env in dependent_tasks
                }
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    log.append(res)
                    yield f"event: task_done\ndata: {json.dumps(res)}\n\n"

        # Save snapshot
        snapshot = _collect_snapshot(market)
        breadth = snapshot.get("breadth")
        vcp = snapshot.get("vcp")
        is_success = (
            breadth
            and isinstance(breadth, dict)
            and breadth.get("composite")
            and vcp
            and isinstance(vcp, dict)
        )

        if is_success:
            run_at = db_save_run(market, snapshot)
            status = "success"
        else:
            run_at = None
            status = "failed"

        signal_pipeline_result = run_signal_pipeline_followup(market)
        log.append(signal_pipeline_result)
        yield f"event: task_done\ndata: {json.dumps(signal_pipeline_result)}\n\n"

        cleanup_old_files(keep_count=2)
        clean_unsuccessful_db_runs()

        final_res = {
            "status": status,
            "market": market,
            "run_at": run_at,
            "log": log,
            "signal_pipeline": signal_pipeline_result,
        }
        yield f"event: done\ndata: {json.dumps(final_res)}\n\n"

    return Response(
        g(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/history/<symbol>")
def api_history(symbol):
    from datetime import date

    try:
        sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
        from cache_manager import CacheManager

        cache = CacheManager(DB_PATH)

        # Helper to determine if cached data is fresh, accounting for weekends and market hours
        def is_cache_fresh(symbol_str) -> bool:
            latest = cache.latest_bar_date(symbol_str)
            if not latest:
                return False
            today = date.today()
            diff = (today - latest).days
            if diff <= 0:  # Cache has today's data
                return True

            today_wd = today.weekday()  # Monday=0, Sunday=6
            if today_wd == 5:  # Saturday (Friday was 1 day ago)
                return diff <= 1
            if today_wd == 6:  # Sunday (Friday was 2 days ago)
                return diff <= 2

            # Weekdays (Monday-Friday)
            # If it's after market close, we expect today's data (diff should be 0)
            from datetime import datetime

            now_dt = datetime.now()
            if symbol_str.endswith(".BK"):
                # Thai market closes at 16:30. After 17:00 local time, today's data is available.
                if now_dt.hour >= 17:
                    return False
                return diff <= 1
            else:
                # US market closes at 03:00/04:00 AM Thai time.
                # During Thai daytime, yesterday's US bar is the latest.
                # After US market closes (approx 04:00 AM Thai time), today's bar is available.
                if now_dt.hour >= 5:
                    return diff <= 1
                return diff <= 2

        # Try local cache first if it is fresh
        if is_cache_fresh(symbol):
            try:
                bars = cache.get_bars(symbol, 260)
                if bars and len(bars) >= 50:
                    history = [
                        {
                            "time": b["date"],
                            "open": float(b["open"]),
                            "high": float(b["high"]),
                            "low": float(b["low"]),
                            "close": float(b["close"]),
                            "value": float(b["volume"]),
                        }
                        for b in reversed(bars)
                    ]
                    return jsonify(history)
            except Exception as ce:
                print(f"Cache lookup failed for {symbol}: {ce}", file=sys.stderr)

        # Fallback to Live download (stale cache or no cache)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty:
            # If live download fails but we have some cached data, return cached data as fallback
            try:
                bars = cache.get_bars(symbol, 260)
                if bars and len(bars) >= 50:
                    history = [
                        {
                            "time": b["date"],
                            "open": float(b["open"]),
                            "high": float(b["high"]),
                            "low": float(b["low"]),
                            "close": float(b["close"]),
                            "value": float(b["volume"]),
                        }
                        for b in reversed(bars)
                    ]
                    return jsonify(history)
            except Exception:
                pass
            return jsonify({"error": "No data found"}), 404

        df = df.reset_index()
        history = [
            {
                "time": row["Date"].strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "value": float(row["Volume"]),
            }
            for _, row in df.iterrows()
        ]

        # Save back to CacheManager to update the local database cache
        try:
            db_bars = [
                {
                    "date": h["time"],
                    "open": h["open"],
                    "high": h["high"],
                    "low": h["low"],
                    "close": h["close"],
                    "volume": int(h["value"]),
                }
                for h in history
            ]
            cache.upsert_bars(symbol, db_bars)
        except Exception as err:
            print(f"Failed to upsert updated bars for {symbol} to cache: {err}", file=sys.stderr)

        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/earnings/<symbol>")
def api_earnings(symbol):
    try:
        sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
        from cache_manager import CacheManager

        cache = CacheManager(DB_PATH)

        # Check local sqlite cache first (TTL 24 hours)
        is_cached, cached_res = cache.get_earnings_scan(symbol, ttl_hours=24.0)
        if is_cached:
            if cached_res:
                try:
                    from datetime import date

                    earn_date = date.fromisoformat(cached_res["date"])
                    days_to = (earn_date - date.today()).days
                    cached_res["days_to_earnings"] = days_to
                except Exception:
                    cached_res["days_to_earnings"] = None
                return jsonify(cached_res)
            return jsonify({"symbol": symbol, "date": None, "days_to_earnings": None})

        # Fetch dynamically from yfinance
        earnings_date = None
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            cal = ticker.calendar
            if cal:
                key = next((k for k in cal.keys() if k.lower() == "earnings date"), None)
                if key:
                    dates = cal[key]
                    if dates and len(dates) > 0:
                        d = dates[0]
                        if hasattr(d, "strftime"):
                            earnings_date = d.strftime("%Y-%m-%d")
                        else:
                            earnings_date = str(d)
        except Exception as err:
            print(f"Failed to fetch earnings for {symbol} via yfinance: {err}", file=sys.stderr)

        # Save to cache
        res_dict = None
        days_to_earnings = None
        if earnings_date:
            res_dict = {"symbol": symbol, "date": earnings_date, "time": "unknown"}
            try:
                from datetime import date

                earn_date = date.fromisoformat(earnings_date)
                days_to_earnings = (earn_date - date.today()).days
            except Exception:
                pass

        cache.save_earnings_scan(symbol, res_dict)
        return jsonify(
            {"symbol": symbol, "date": earnings_date, "days_to_earnings": days_to_earnings}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/db/stats")
def api_db_stats():
    """Return DB stats: run counts, date ranges per market."""
    try:
        clean_unsuccessful_db_runs()
        with _db() as conn:
            rows = conn.execute("""
                SELECT market,
                       COUNT(*)        AS total_runs,
                       MIN(run_at)     AS oldest_run,
                       MAX(run_at)     AS newest_run
                FROM analysis_run
                GROUP BY market
                ORDER BY market
            """).fetchall()
            try:
                price_stats = conn.execute("""
                    SELECT COUNT(DISTINCT symbol) AS symbols,
                           COUNT(*)               AS total_bars,
                           MIN(date)              AS oldest_bar,
                           MAX(date)              AS newest_bar
                    FROM price_bar
                """).fetchone()
                price_cache = dict(price_stats) if price_stats else {}
            except Exception:
                price_cache = {}
        return jsonify(
            {
                "analysis_runs": [dict(r) for r in rows],
                "price_cache": price_cache,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Paper Trade Simulator ────────────────────────────────────────────────────


def _count_files(path: Path, patterns: list[str]) -> int:
    if not path.exists():
        return 0
    total = 0
    for pattern in patterns:
        total += len(list(path.glob(pattern)))
    return total


def _read_thesis_summary() -> dict:
    state_dir = Path(BASE_DIR) / "state" / "theses"
    summary = {
        "total": 0,
        "by_status": {},
        "by_source": {},
        "by_type": {},
        "recent": [],
    }
    if not state_dir.exists():
        return summary

    rows = []
    for path in sorted(state_dir.glob("th_*.yaml")):
        try:
            thesis = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        status = thesis.get("status") or "UNKNOWN"
        source = signal_ledger.normalize_source((thesis.get("origin") or {}).get("skill"))
        thesis_type = thesis.get("thesis_type") or "unknown"
        score = (thesis.get("origin") or {}).get("screening_score")
        row = {
            "thesis_id": thesis.get("thesis_id"),
            "ticker": thesis.get("ticker"),
            "status": status,
            "source": source,
            "thesis_type": thesis_type,
            "score": score,
            "grade": (thesis.get("origin") or {}).get("screening_grade"),
            "created_at": thesis.get("created_at"),
            "next_review_date": (thesis.get("monitoring") or {}).get("next_review_date"),
        }
        rows.append(row)
        summary["total"] += 1
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
        summary["by_type"][thesis_type] = summary["by_type"].get(thesis_type, 0) + 1

    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    summary["recent"] = rows[:12]
    return summary


def _read_feedback_files() -> list[dict]:
    reports_dir = Path(REPORTS_DIR)
    candidates: list[Path] = []
    for pattern in ("**/*feedback*.json", "**/*improvement*.json", "**/*backlog*.yaml"):
        candidates.extend(reports_dir.glob(pattern))
    items = []
    for path in sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        items.append(
            {
                "name": path.name,
                "path": str(path.relative_to(Path(BASE_DIR))),
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(
                    timespec="seconds"
                ),
            }
        )
    return items


def _parse_report_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S UTC"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _report_item(label: str, path: str | None) -> dict:
    if not path or not os.path.exists(path):
        return {"label": label, "status": "missing", "path": None}
    data = load_json(path)
    meta = data.get("metadata", {}) if isinstance(data, dict) else {}
    generated = (
        meta.get("generated_at")
        or meta.get("generated")
        or data.get("generated_at")
        or data.get("generated")
        if isinstance(data, dict)
        else None
    )
    generated_dt = _parse_report_time(generated)
    modified_dt = datetime.fromtimestamp(os.path.getmtime(path))
    reference_dt = generated_dt or modified_dt
    age_hours = max((datetime.now(reference_dt.tzinfo) - reference_dt).total_seconds() / 3600, 0)
    if age_hours <= 24:
        status = "fresh"
    elif age_hours <= 72:
        status = "aging"
    else:
        status = "stale"
    return {
        "label": label,
        "status": status,
        "path": str(Path(path).relative_to(BASE_DIR)),
        "generated_at": generated,
        "modified_at": modified_dt.isoformat(timespec="seconds"),
        "age_hours": round(age_hours, 1),
    }


def _freshness_snapshot(market: str | None) -> dict:
    market = (market or "TH").upper()
    reports = [
        _report_item(
            "Daily pipeline",
            latest_file_any(
                os.path.join(REPORTS_DIR, "daily-signal-pipeline", "daily_signal_pipeline_*.json")
            ),
        ),
        _report_item(
            "VCP screener", latest_file(os.path.join(REPORTS_DIR, "vcp_screener_*.json"), market)
        ),
        _report_item(
            "CANSLIM screener",
            latest_file(os.path.join(REPORTS_DIR, "canslim_screener_*.json"), market),
        ),
    ]
    if market == "US":
        reports.append(
            _report_item(
                "Market-top risk", latest_file_any(os.path.join(REPORTS_DIR, "market_top_*.json"))
            )
        )
    if market == "TH":
        reports.append(
            _report_item(
                "Thai swing", latest_file_any(os.path.join(REPORTS_DIR, "thai_swing_*.json"))
            )
        )
    missing = sum(1 for row in reports if row.get("status") == "missing")
    stale = sum(1 for row in reports if row.get("status") == "stale")
    return {
        "market": market,
        "reports": reports,
        "missing": missing,
        "stale": stale,
        "overall_status": "attention" if missing or stale else "ok",
    }


def _vcp_near_miss_snapshot(market: str | None) -> dict:
    market = (market or "TH").upper()
    path = latest_file(os.path.join(REPORTS_DIR, "vcp_screener_*.json"), market)
    data = load_json(path) if path else None
    if not isinstance(data, dict):
        return {"market": market, "status": "missing", "near_misses": [], "funnel": {}}
    meta = data.get("metadata") or {}
    funnel = meta.get("funnel") or {}
    near_misses = data.get("near_misses") or []
    results = data.get("results") or []
    notes = []
    if not near_misses and funnel.get("trend_template_passed", 0) and not results:
        notes.append(
            "This VCP report was generated before near-miss diagnostics were available; rerun analysis to populate reasons."
        )
    return {
        "market": market,
        "status": "ok",
        "path": str(Path(path).relative_to(BASE_DIR)) if path else None,
        "generated_at": meta.get("generated_at"),
        "funnel": funnel,
        "results": len(results),
        "near_misses": near_misses[:10],
        "notes": notes,
    }


def _normalize_paper_summary_sources(paper_summary: dict) -> dict:
    by_source = paper_summary.get("by_source") or {}
    merged: dict[str, dict] = {}
    for source, stats in by_source.items():
        normalized = signal_ledger.normalize_source(source)
        if normalized not in merged:
            merged[normalized] = dict(stats)
            continue
        current = merged[normalized]
        for key in ("total_trades", "open_positions", "closed_trades", "wins", "losses"):
            current[key] = int(current.get(key) or 0) + int(stats.get(key) or 0)
        scored_total = 0.0
        scored_count = 0
        for row in (current, stats):
            score = row.get("avg_source_score")
            count = int(row.get("total_trades") or 0)
            if score is not None and count:
                scored_total += float(score) * count
                scored_count += count
        current["avg_source_score"] = (
            round(scored_total / scored_count, 2) if scored_count else None
        )
        closed = int(current.get("closed_trades") or 0)
        wins = int(current.get("wins") or 0)
        current["win_rate"] = round(wins / closed, 3) if closed else 0
    paper_summary["by_source"] = merged
    return paper_summary


def _source_readiness(
    thesis_summary: dict, paper_summary: dict, ledger_source_metrics: dict | None = None
) -> list[dict]:
    ledger_source_metrics = ledger_source_metrics or {}
    sources = set(thesis_summary.get("by_source", {}).keys())
    sources.update((paper_summary.get("by_source") or {}).keys())
    sources.update(ledger_source_metrics.keys())
    rows = []
    for source in sorted(sources):
        paper = (paper_summary.get("by_source") or {}).get(source, {})
        ledger = ledger_source_metrics.get(source, {})
        complete_signals = int(ledger.get("complete_signals") or 0)
        completed_outcomes = int(ledger.get("complete_outcomes") or 0)
        closed = max(int(paper.get("closed_trades") or 0), complete_signals)
        paper_total = int(paper.get("total_trades") or 0)
        thesis_total = int((thesis_summary.get("by_source") or {}).get(source, 0))
        signal_total = int(ledger.get("signals") or 0)
        displayed_signals = max(thesis_total, signal_total)
        horizon_5d = (ledger.get("horizons") or {}).get("5") or {}
        win_rate = paper.get("win_rate")
        expectancy_r = paper.get("expectancy_r")
        if completed_outcomes and (win_rate is None or win_rate == 0):
            win_rate = horizon_5d.get("win_rate")
        if completed_outcomes and (expectancy_r is None or expectancy_r == 0):
            expectancy_r = horizon_5d.get("avg_r")
        if closed >= 100:
            stage = "validated"
            guidance = "ใช้ได้เป็น source หลัก แต่ยังต้อง monitor edge decay"
        elif closed >= 30:
            stage = "calibrating"
            guidance = "เริ่มปรับ weight ได้แบบระวัง"
        elif closed > 0:
            stage = "collecting"
            guidance = "ใช้เพื่อเรียนรู้ก่อน ยังไม่ควรเพิ่ม size"
        elif paper_total > 0 or thesis_total > 0:
            stage = "needs_outcomes"
            guidance = "มี signal แล้ว แต่ยังไม่มี closed outcome"
        else:
            stage = "not_started"
            guidance = "ยังไม่มีข้อมูล"
        rows.append(
            {
                "source": source,
                "signals": displayed_signals,
                "ledger_signals": signal_total,
                "paper_trades": paper_total,
                "closed_trades": closed,
                "complete_signals": complete_signals,
                "completed_outcomes": completed_outcomes,
                "win_rate": win_rate,
                "expectancy_r": expectancy_r,
                "avg_score": paper.get("avg_source_score"),
                "horizons": ledger.get("horizons", {}),
                "stage": stage,
                "guidance": guidance,
            }
        )
    return rows


def _improvement_recommendations(
    thesis_summary: dict,
    paper_summary: dict,
    postmortem_count: int,
    completed_signals: int = 0,
    auto_paper_summary: dict | None = None,
) -> list[dict]:
    recs = []
    auto_paper_summary = auto_paper_summary or {}
    closed = int(paper_summary.get("closed_trades") or 0)
    open_positions = int(paper_summary.get("open_positions") or 0)
    auto_eligible = int(auto_paper_summary.get("eligible") or 0)
    auto_config_summary = auto_paper_summary.get("config") or {}
    auto_execute = bool(auto_config_summary.get("execute"))
    if closed == 0 and completed_signals == 0:
        recs.append(
            {
                "priority": "P0",
                "title": "เริ่มเก็บ closed outcomes อัตโนมัติ",
                "why": "ตอนนี้ยังไม่มี closed paper trade จึงยังวัด expectancy หรือ win rate จริงไม่ได้",
                "action": "ให้ daily automation เพิ่ม qualified signals เข้า paper trade และอัปเดต stop/target ทุกวัน",
            }
        )
    elif closed == 0 and completed_signals > 0:
        recs.append(
            {
                "priority": "P1",
                "title": "แยก forward outcome กับ paper trade outcome",
                "why": f"มี forward-tested signals {completed_signals} รายการแล้ว แต่ยังไม่มี closed paper trade",
                "action": "ใช้ forward outcome เพื่อ calibrate signal เบื้องต้น และเริ่ม auto-paper สำหรับสัญญาณรอบใหม่",
            }
        )
    if thesis_summary.get("by_status", {}).get("IDEA", 0) == thesis_summary.get(
        "total", 0
    ) and thesis_summary.get("total", 0):
        recs.append(
            {
                "priority": "P0",
                "title": "ทำทางเดิน IDEA → PAPER/ACTIVE",
                "why": "thesis ทั้งหมดค้างที่ IDEA ทำให้ learning loop ยังไม่ปิด",
                "action": "เพิ่ม automation ที่แปลง signal คุณภาพสูงเป็น paper position พร้อม entry/stop/target",
            }
        )
    if auto_eligible == 0:
        recs.append(
            {
                "priority": "P2",
                "title": "Auto-paper พร้อม แต่รอสัญญาณใหม่",
                "why": "ยังไม่มี signal สดที่ผ่าน gate: score ≥70 และอายุไม่เกิน 10 วัน",
                "action": "หลังรัน fresh analysis รอบใหม่ ให้สั่ง auto-paper dry-run อีกครั้งก่อน execute",
            }
        )
    elif open_positions > 0 and auto_execute:
        recs.append(
            {
                "priority": "P2",
                "title": "มี paper positions เปิดแล้ว",
                "why": f"มี open paper positions {open_positions} รายการ และยังมี {auto_eligible} signals ที่รอรอบถัดไป",
                "action": "ให้ scheduler ตามราคาและเปิดเพิ่มตาม max_new_positions โดยไม่เปิดหุ้นซ้ำ",
            }
        )
    else:
        recs.append(
            {
                "priority": "P1",
                "title": "มี signal พร้อมเข้า auto-paper",
                "why": f"พบ {auto_eligible} signals ที่ผ่าน gate สำหรับ paper portfolio",
                "action": "ตรวจ dry-run แล้วค่อยรัน auto-paper ด้วย --execute เพื่อเริ่มเก็บผล",
            }
        )
    if postmortem_count == 0:
        recs.append(
            {
                "priority": "P1",
                "title": "เปิด postmortem pipeline",
                "why": "ยังไม่มี postmortem record สำหรับวิเคราะห์ false positive และ regime mismatch",
                "action": "ให้ระบบสร้าง postmortem เมื่อ signal ครบ 5D/20D/60D หรือเมื่อ paper trade ปิด",
            }
        )
    if 0 < closed < 30:
        recs.append(
            {
                "priority": "P1",
                "title": "จำกัดการปรับ weight จนกว่าจะมี sample 30+",
                "why": f"มี closed trades {closed} รายการ ซึ่งยังน้อยเกินไปสำหรับสรุปความแม่น",
                "action": "ให้ใช้ผลลัพธ์เป็น warning เท่านั้น ห้ามปรับ rule แรงจาก sample เล็ก",
            }
        )
    if open_positions > 0:
        recs.append(
            {
                "priority": "P2",
                "title": "ตาม open paper positions ให้ครบ",
                "why": f"มี open paper positions {open_positions} รายการที่รอ outcome",
                "action": "กด update marks หรือให้ scheduler เรียก /api/paper/update_marks หลังตลาดปิด",
            }
        )
    return recs


@app.route("/api/signal-results")
def api_signal_results():
    """Summarize signal/outcome readiness for the dashboard calibration tab."""
    market = request.args.get("market")
    try:
        paper_summary = _normalize_paper_summary_sources(paper_stats(market))
        thesis_summary = _read_thesis_summary()
        with signal_ledger.connect(DB_PATH) as conn:
            ledger_counts = signal_ledger.get_signal_counts(conn, market=market)
            ledger_sources = signal_ledger.source_metrics(conn, market=market)
            ledger_outcomes = signal_ledger.outcome_summary(conn, market=market)
            pipeline_config = run_daily_signal_pipeline.load_config(
                Path(BASE_DIR) / "state" / "automation_config.yaml"
            )
            paper_config = pipeline_config.get("auto_paper") or {}
            fee_model = paper_config.get("fee_model") or {}
            transaction_cost_bps = effective_transaction_cost_bps(fee_model)
            auto_enabled = bool(paper_config.get("enabled", True))
            auto_execute = bool(paper_config.get("execute", False))
            auto_config = auto_paper.AutoPaperConfig(
                market=market,
                min_score=float(paper_config.get("min_score", 70.0)),
                max_age_days=int(paper_config.get("max_age_days", 10)),
                max_new_positions=int(paper_config.get("max_new_positions", 3)),
                max_open_positions=(
                    int(paper_config["max_open_positions"])
                    if paper_config.get("max_open_positions") is not None
                    else None
                ),
                high_score_override_min=(
                    float(paper_config["high_score_override_min"])
                    if paper_config.get("high_score_override_min") is not None
                    else None
                ),
                max_open_positions_with_override=(
                    int(paper_config["max_open_positions_with_override"])
                    if paper_config.get("max_open_positions_with_override") is not None
                    else None
                ),
                shares=int(paper_config.get("shares", 100)),
                derive_missing_risk=bool(paper_config.get("derive_missing_risk", True)),
                default_stop_pct=float(paper_config.get("default_stop_pct", 8.0)),
                target_r=float(paper_config.get("target_r", 2.0)),
                transaction_cost_bps=transaction_cost_bps,
                account_size=(
                    float(paper_config["account_size"])
                    if paper_config.get("account_size")
                    else None
                ),
                risk_per_trade_pct=(
                    float(paper_config["risk_per_trade_pct"])
                    if paper_config.get("risk_per_trade_pct")
                    else None
                ),
                max_position_pct=(
                    float(paper_config["max_position_pct"])
                    if paper_config.get("max_position_pct")
                    else None
                ),
                max_portfolio_heat_pct=(
                    float(paper_config["max_portfolio_heat_pct"])
                    if paper_config.get("max_portfolio_heat_pct")
                    else None
                ),
                board_lot_size=int(paper_config.get("board_lot_size", 100)),
                source_rules=paper_config.get("source_rules") or {},
                dry_run=not (auto_enabled and auto_execute),
            )
            auto_candidates = auto_paper.eligible_signals(conn, auto_config)
            auto_diagnostics = auto_paper.explain_candidates(conn, auto_config)
            replacement_review = auto_paper.replacement_review(conn, auto_config)
            auto_paper_summary = {
                "eligible": len(auto_candidates),
                "candidates": auto_candidates[:5],
                "diagnostics": auto_diagnostics,
                "replacement_review": replacement_review,
                "config": {
                    "min_score": auto_config.min_score,
                    "max_age_days": auto_config.max_age_days,
                    "max_new_positions": auto_config.max_new_positions,
                    "max_open_positions": auto_config.max_open_positions,
                    "high_score_override_min": auto_config.high_score_override_min,
                    "max_open_positions_with_override": auto_config.max_open_positions_with_override,
                    "transaction_cost_bps": auto_config.transaction_cost_bps,
                    "fee_model": fee_model,
                    "account_size": auto_config.account_size,
                    "risk_per_trade_pct": auto_config.risk_per_trade_pct,
                    "max_position_pct": auto_config.max_position_pct,
                    "max_portfolio_heat_pct": auto_config.max_portfolio_heat_pct,
                    "board_lot_size": auto_config.board_lot_size,
                    "source_rules": auto_config.source_rules,
                    "execute": auto_execute,
                    "dry_run": auto_config.dry_run,
                },
            }
        postmortem_count = _count_files(
            Path(REPORTS_DIR) / "postmortems", ["*.json", "*.yaml", "*.md"]
        )
        file_signal_count = _count_files(Path(BASE_DIR) / "state" / "signals", ["*.json", "*.yaml"])
        signal_count = max(file_signal_count, ledger_counts["total"])
        payload = {
            "as_of": datetime.now().isoformat(timespec="seconds"),
            "market": market,
            "paper": paper_summary,
            "theses": thesis_summary,
            "postmortems": {"count": postmortem_count},
            "signals": {
                "count": signal_count,
                "ledger_count": ledger_counts["total"],
                "file_count": file_signal_count,
                "completed_signals": ledger_counts["completed_signals"],
                "by_source": ledger_counts["by_source"],
            },
            "outcomes": ledger_outcomes,
            "auto_paper": auto_paper_summary,
            "source_readiness": _source_readiness(thesis_summary, paper_summary, ledger_sources),
            "freshness": _freshness_snapshot(market),
            "vcp_near_misses": _vcp_near_miss_snapshot(market),
            "recommendations": _improvement_recommendations(
                thesis_summary,
                paper_summary,
                postmortem_count,
                ledger_counts["completed_signals"],
                auto_paper_summary,
            ),
            "feedback_files": _read_feedback_files(),
        }
        return jsonify(_clean_nan(payload))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper/open", methods=["POST"])
def api_paper_open():
    """Open a new paper position. JSON body required."""
    try:
        d = request.get_json(force=True) or {}
        row = paper_open(
            symbol=d["symbol"],
            market=d["market"],
            shares=int(d["shares"]),
            entry=float(d["entry"]),
            stop=float(d["stop"]),
            target=float(d["target"]),
            side=d.get("side", "long"),
            source=d.get("source"),
            source_score=d.get("source_score"),
            notes=d.get("notes"),
            emotion=d.get("emotion"),
        )
        hf_sync.upload_db()
        return jsonify(_clean_nan(row))
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper/close", methods=["POST"])
def api_paper_close():
    """Close an open position. JSON: {id, exit_price, status?, emotion?, notes?}"""
    try:
        d = request.get_json(force=True) or {}
        row = paper_close(
            trade_id=int(d["id"]),
            exit_price=float(d["exit_price"]),
            status=d.get("status", "closed_manual"),
            emotion=d.get("emotion"),
            notes=d.get("notes"),
        )
        hf_sync.upload_db()
        return jsonify(_clean_nan(row))
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper/list")
def api_paper_list():
    """List positions. Query: ?status=open|closed|all&market=TH|US"""
    status = request.args.get("status", "all").strip().lower()
    if status not in {"open", "closed", "all"}:
        return jsonify({"error": "status must be open, closed, or all"}), 400
    market = request.args.get("market")
    rows = paper_list(status, market)
    return jsonify(_clean_nan(rows))


@app.route("/api/paper/stats")
def api_paper_stats():
    """Portfolio statistics. Query: ?market=TH|US"""
    market = request.args.get("market")
    return jsonify(_clean_nan(paper_stats(market)))


@app.route("/api/paper/fingerprint")
def api_paper_fingerprint():
    """Stock/technique behavior profiles with forward +1/+3/+5 observations."""
    market = request.args.get("market")
    return jsonify(_clean_nan(paper_fingerprints(market)))


@app.route("/api/paper/update_marks", methods=["POST"])
def api_paper_update_marks():
    """Refresh prices for all open positions; auto-trigger stop/target."""
    try:
        results = paper_update_marks()
        hf_sync.upload_db()
        return jsonify(_clean_nan({"updated": len(results), "results": results}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper/journal", methods=["POST"])
def api_paper_journal():
    """Add journal entry to a trade. JSON: {id, text, emotion?}"""
    try:
        d = request.get_json(force=True) or {}
        row = paper_journal(int(d["id"]), d["text"], d.get("emotion"))
        hf_sync.upload_db()
        return jsonify(_clean_nan(row))
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper/discipline_check")
def api_paper_discipline_check():
    """Return recent discipline warnings (low stop respect, FOMO streak)."""
    try:
        res = paper_discipline_check()
        return jsonify(_clean_nan(res))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/paper/emotions")
def api_paper_emotions():
    """Return valid emotion tags."""
    return jsonify(sorted(VALID_EMOTIONS))


@app.route("/api/patterns")
def api_patterns():
    import sqlite3

    db_path = os.path.join(BASE_DIR, "state", "market_cache.db")
    if not os.path.exists(db_path):
        return jsonify({})

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT symbol, date, open, close, high, low, volume FROM price_bar ORDER BY symbol, date ASC"
    )
    rows = c.fetchall()

    data = {}
    for r in rows:
        if r["open"] is None or r["close"] is None:
            continue
        sym = r["symbol"]
        if sym not in data:
            data[sym] = []
        data[sym].append(dict(r))

    oversold = []
    overbought = []

    for sym, bars in data.items():
        if len(bars) < 10:
            continue

        consecutive_red = 0
        consecutive_green = 0

        for b in reversed(bars):
            if b["close"] < b["open"]:
                if consecutive_green > 0:
                    break
                consecutive_red += 1
            elif b["close"] > b["open"]:
                if consecutive_red > 0:
                    break
                consecutive_green += 1
            else:
                break

        if consecutive_red >= 3 or consecutive_green >= 3:
            is_oversold = consecutive_red >= 3
            target_consecutive = consecutive_red if is_oversold else consecutive_green

            occurrences = 0
            wins = 0
            sum_returns = 0

            curr_streak = 0
            for i in range(len(bars) - 1):
                b = bars[i]
                if is_oversold:
                    if b["close"] < b["open"]:
                        curr_streak += 1
                    else:
                        curr_streak = 0
                else:
                    if b["close"] > b["open"]:
                        curr_streak += 1
                    else:
                        curr_streak = 0

                if curr_streak == target_consecutive:
                    next_b = bars[i + 1]
                    occurrences += 1

                    if b["close"] > 0:
                        next_return = (next_b["close"] - b["close"]) / b["close"] * 100
                    else:
                        next_return = 0
                    sum_returns += next_return

                    if is_oversold and next_b["close"] > b["close"]:
                        wins += 1
                    elif not is_oversold and next_b["close"] < b["close"]:
                        wins += 1

            if occurrences > 0:
                win_rate = (wins / occurrences) * 100
                avg_return = sum_returns / occurrences

                if occurrences >= 3 and win_rate > 50.0:
                    latest = bars[-1]
                    item = {
                        "symbol": sym,
                        "consecutive": target_consecutive,
                        "occurrences": occurrences,
                        "win_rate": round(win_rate, 2),
                        "avg_return": round(avg_return, 2),
                        "latest": {
                            "date": latest["date"],
                            "open": latest["open"],
                            "high": latest["high"],
                            "low": latest["low"],
                            "close": latest["close"],
                            "volume": latest["volume"],
                        },
                    }
                    if is_oversold:
                        oversold.append(item)
                    else:
                        overbought.append(item)

    return jsonify({"Oversold": oversold, "Overbought": overbought})


if __name__ == "__main__":
    cleanup_old_files(keep_count=2)
    clean_unsuccessful_db_runs()
    dashboard_host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    dashboard_port = int(os.environ.get("DASHBOARD_PORT", "5050"))
    dashboard_debug = os.environ.get("FLASK_DEBUG", "1").lower() not in {"0", "false", "no"}
    app.run(debug=dashboard_debug, host=dashboard_host, use_reloader=False, port=dashboard_port)
