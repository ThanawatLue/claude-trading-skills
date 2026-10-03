#!/usr/bin/env python3
"""Jules Autonomous Scout & Daily Mission Generator.

Runs independently on GCP VM (or local schedule) without requiring an Antigravity session.
Scans the market for top fundamental and momentum anomalies, pairs them with Jules's current
Trader DNA, and generates an actionable daily mission packet in `state/jules_tasks/today_mission.md`.

Usage:
    python scripts/jules_scout.py run
    python scripts/jules_scout.py show
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import paper_trade

import scripts.adaptive_indicators as ai
import scripts.jules_evolver as je
from scripts.jules_trader import round_to_set_tick
from trading_core.clock import isoformat_seconds

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jules_scout")

DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"
REPORTS_DIR = PROJECT_ROOT / "reports"
TASKS_DIR = PROJECT_ROOT / "state" / "jules_tasks"
ORDERS_DIR = PROJECT_ROOT / "state" / "jules_orders"

MISSION_MD = TASKS_DIR / "today_mission.md"
MISSION_JSON = TASKS_DIR / "today_mission.json"

POSITION_BUDGET_THB = 7000.0  # ~23% of 30,000 THB to allow max 4 positions
POSITION_BUDGET_USD = 250.0  # 25% of $1,000 USD to allow max 4 positions


def get_mission_paths(market: str = "TH") -> tuple[Path, Path, Path, Path]:
    """Return (tasks_dir, orders_dir, mission_md, mission_json) for the given market."""
    if market.upper() == "US":
        tasks_dir = PROJECT_ROOT / "state" / "jules_us_tasks"
        orders_dir = PROJECT_ROOT / "state" / "jules_us_orders"
    else:
        tasks_dir = PROJECT_ROOT / "state" / "jules_tasks"
        orders_dir = PROJECT_ROOT / "state" / "jules_orders"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    orders_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir, orders_dir, tasks_dir / "today_mission.md", tasks_dir / "today_mission.json"


def _ensure_dirs(market: str = "TH"):
    get_mission_paths(market)


def get_us_screened_candidates(limit: int = 15) -> list[dict[str, Any]]:
    """Screen top US stocks using TradingView Americas screener with VCP/CANSLIM filters."""
    from scripts.lib.tv_client import get_us_stocks

    try:
        stocks = get_us_stocks(limit=500, min_avg_volume=500_000, min_market_cap=1_000_000_000)
    except Exception as e:
        logger.error("Failed to fetch US stocks from TradingView: %s", e)
        return []

    candidates = []
    for s in stocks:
        price = float(s.get("price") or 0.0)
        # Sizing filter for $1,000 account ($250 slot): price between $5 and $250
        if price < 5.0 or price > 250.0:
            continue

        rsi = float(s.get("rsi") or 0.0)
        if rsi < 45.0 or rsi > 78.0:
            continue

        sma50 = float(s.get("sma50") or 0.0)
        sma200 = float(s.get("sma200") or 0.0)
        if sma50 > 0 and price < sma50:
            continue

        vol = float(s.get("volume") or 0.0)
        avg_vol = float(s.get("avgVolume") or 1.0)
        vol_ratio = vol / avg_vol if avg_vol > 0 else 1.0

        perf_1m = float(s.get("perf_1m") or 0.0)
        perf_3m = float(s.get("perf_3m") or 0.0)

        score = 65.0
        if vol_ratio >= 1.5:
            score += 10.0
        elif vol_ratio >= 1.2:
            score += 5.0

        if perf_1m > 0:
            score += min(10.0, perf_1m)
        if perf_3m > 0:
            score += min(10.0, perf_3m * 0.5)

        if sma200 > 0 and sma50 > sma200:
            score += 5.0  # Golden Cross / Long-term uptrend

        suggested_stop = round(price * 0.955, 2)
        suggested_target = round(price + (price - suggested_stop) * 2.2, 2)

        sym = s["symbol"].upper().strip().replace(".BK", "")
        candidates.append(
            {
                "symbol": sym,
                "company_name": s.get("name", sym),
                "sector": s.get("sector", "Unknown"),
                "price": price,
                "score": round(score, 1),
                "source": "US Momentum Screener",
                "highlights": f"RSI: {rsi:.1f} | Vol: {vol_ratio:.1f}x | 1M: {perf_1m:+.1f}% | 3M: {perf_3m:+.1f}%",
                "suggested_stop": suggested_stop,
                "suggested_target": suggested_target,
            }
        )

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:limit]


def get_latest_canslim_candidates() -> list[dict[str, Any]]:
    """Extract top candidates from the latest CANSLIM report if available."""
    candidates = []
    canslim_files = sorted(glob.glob(str(REPORTS_DIR / "canslim_screener_*.json")))
    if not canslim_files:
        return candidates

    latest_file = Path(canslim_files[-1])
    try:
        with open(latest_file, encoding="utf-8") as f:
            data = json.load(f)
            results = data.get("results", [])
            for r in results[:10]:
                sym = r.get("symbol", "")
                if not sym:
                    continue
                candidates.append(
                    {
                        "symbol": sym,
                        "company_name": r.get("company_name", sym),
                        "sector": r.get("sector", "N/A"),
                        "price": float(r.get("price") or 0.0),
                        "score": float(r.get("composite_score") or 0.0),
                        "source": "CANSLIM Screener",
                        "highlights": f"CANSLIM Score: {r.get('composite_score', 0):.1f} | 52w Dist: {r.get('n_component', {}).get('distance_from_high_pct', 0):.1f}%",
                    }
                )
    except Exception as e:
        logger.warning("Failed to parse CANSLIM file %s: %s", latest_file.name, e)

    return candidates


def get_latest_thai_swing_candidates() -> list[dict[str, Any]]:
    """Extract top candidates from the latest Thai Swing Screener report if available."""
    candidates = []
    swing_files = sorted(glob.glob(str(REPORTS_DIR / "thai_swing_*.json")))
    if not swing_files:
        return candidates

    latest_file = Path(swing_files[-1])
    try:
        with open(latest_file, encoding="utf-8") as f:
            data = json.load(f)
            items = data.get("momentum", []) + data.get("dip_buy", [])
            for r in items[:10]:
                sym = r.get("symbol", "")
                if not sym:
                    continue
                plan = r.get("plan") or {}
                vol_ratio = (
                    float(r.get("volume") or 0) / float(r.get("avg_volume") or 1)
                    if float(r.get("avg_volume") or 0) > 0
                    else 1.0
                )
                candidates.append(
                    {
                        "symbol": sym,
                        "company_name": r.get("name", sym),
                        "sector": r.get("sector", "N/A"),
                        "price": float(r.get("price") or 0.0),
                        "score": float(r.get("score") or 0.0),
                        "source": f"Thai Swing ({r.get('strategy', 'MOMENTUM')})",
                        "highlights": f"RSI: {float(r.get('rsi') or 0):.1f} | Vol: {vol_ratio:.1f}x | Swing Score: {float(r.get('score') or 0):.1f}",
                        "suggested_stop": plan.get("stop"),
                        "suggested_target": plan.get("target"),
                    }
                )
    except Exception as e:
        logger.warning("Failed to parse Thai Swing file %s: %s", latest_file.name, e)

    return candidates


def get_latest_intraday_candidates(market: str = "TH") -> list[dict[str, Any]]:
    """Extract intraday breakout candidates if available."""
    tasks_dir, _, _, _ = get_mission_paths(market)
    intraday_file = tasks_dir / "intraday_candidates.json"
    if not intraday_file.exists():
        return []
    try:
        with open(intraday_file, encoding="utf-8") as f:
            data = json.load(f)
            candidates = []
            for c in data.get("candidates", []):
                sym = c.get("symbol", "")
                if not sym:
                    continue
                candidates.append(
                    {
                        "symbol": sym,
                        "company_name": sym,
                        "sector": c.get("sector", "Intraday Breakout"),
                        "price": float(c.get("price") or 0.0),
                        "score": float(c.get("score") or 70.0),
                        "source": "Intraday ORB Scanner",
                        "highlights": c.get("highlights", ""),
                        "suggested_stop": c.get("suggested_stop"),
                        "suggested_target": c.get("suggested_target"),
                    }
                )
            return candidates
    except Exception as e:
        logger.debug("Failed to read intraday candidates: %s", e)
        return []


def find_nearest_resistance(symbol: str, current_price: float, lookback: int = 30) -> float | None:
    """Query recent price bars to find prior swing high resistance above current price."""
    if not DB_PATH.exists() or current_price <= 0:
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                """SELECT high FROM price_bar
                   WHERE symbol = ?
                   ORDER BY date DESC
                   LIMIT ?""",
                (symbol, lookback),
            ).fetchall()
            if not rows:
                return None
            highs = [float(r[0]) for r in rows if float(r[0]) > current_price * 1.01]
            if highs:
                return min(highs)
    except Exception:
        pass
    return None


def get_volume_anomaly_candidates(limit: int = 5) -> list[dict[str, Any]]:
    """Scan price bars in market_cache.db for volume leaders."""
    candidates = []
    if not DB_PATH.exists():
        return candidates

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT symbol, max(date) as last_d, close, volume
                   FROM price_bar
                   WHERE symbol LIKE '%.BK'
                   GROUP BY symbol
                   HAVING close > 1.0
                   ORDER BY volume DESC
                   LIMIT ?""",
                (limit * 2,),
            ).fetchall()

            for r in rows:
                candidates.append(
                    {
                        "symbol": r["symbol"],
                        "company_name": r["symbol"].replace(".BK", ""),
                        "sector": "Volume Surge",
                        "price": float(r["close"]),
                        "score": 60.0,
                        "source": "Volume Leader",
                        "highlights": f"High Volume: {int(r['volume']):,} shares @ ฿{float(r['close']):.2f}",
                    }
                )
    except Exception as e:
        logger.warning("Failed to query price bars: %s", e)

    return candidates


def calculate_sizing_and_levels(
    price: float,
    symbol: str | None = None,
    suggested_stop: float | None = None,
    suggested_target: float | None = None,
    market: str = "TH",
) -> dict[str, Any]:
    """Calculate shares, tight stop, and resistance-aware target."""
    if price <= 0:
        return {"shares": 1, "stop": 0.0, "target": 0.0, "target_note": "N/A", "est_cost": 0.0}

    market_clean = market.upper()
    curr_sym = "$" if market_clean == "US" else "฿"

    if market_clean == "US":
        raw_shares = int(POSITION_BUDGET_USD // price)
        shares = max(1, raw_shares)
        if suggested_stop and 0 < suggested_stop < price:
            stop = round(suggested_stop, 2)
        else:
            stop = round(price * 0.95, 2)
        risk_per_share = price - stop
        default_target = round(price + (risk_per_share * 2.0), 2)
        if suggested_target and suggested_target > price:
            target = round(suggested_target, 2)
            target_note = f"{curr_sym}{target:.2f} (Swing Target)"
        else:
            target = default_target
            target_note = f"{curr_sym}{target:.2f} (2.0R)"
    else:
        # Board lot = 100 shares
        raw_shares = int(POSITION_BUDGET_THB // price)
        shares = max(100, (raw_shares // 100) * 100)

        # Stop Loss: use suggested_stop if valid and below price, else 5% default
        if suggested_stop and 0 < suggested_stop < price:
            stop = round_to_set_tick(suggested_stop, "down")
        else:
            stop = round_to_set_tick(price * 0.95, "down")

        risk_per_share = price - stop
        default_target = round_to_set_tick(price + (risk_per_share * 2.0), "down")

        # Resistance-Aware Check: take profit before the smart-money dump
        resistance = find_nearest_resistance(symbol, price) if symbol else None
        if resistance and (price + risk_per_share * 1.1) <= resistance <= default_target:
            target = round_to_set_tick(resistance, "down")
            target_note = f"฿{target:.2f} (Resistance Pivot)"
        elif suggested_target and suggested_target > price:
            target = round_to_set_tick(suggested_target, "down")
            target_note = f"฿{target:.2f} (Swing Target)"
        else:
            target = default_target
            target_note = f"฿{target:.2f} (2.0R)"

    est_cost = round(price * shares, 2)

    return {
        "shares": shares,
        "stop": stop,
        "target": target,
        "target_note": target_note,
        "est_cost": est_cost,
    }


def _get_stock_history_bars(symbol: str, lookback: int = 35, market: str = "TH") -> pd.DataFrame:
    """Fetch historical daily bars from market_cache.db or yfinance for U/D and RS calculation."""
    if market.upper() == "US":
        try:
            import yfinance as yf

            yf_sym = symbol.replace(".", "-") if "." in symbol else symbol
            ticker = yf.Ticker(yf_sym)
            df = ticker.history(period=f"{lookback + 10}d")
            if not df.empty and "Close" in df.columns:
                df = df.reset_index()
                date_col = "Date" if "Date" in df.columns else df.columns[0]
                df["Date"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")
                df.set_index("Date", inplace=True)
                return df.tail(lookback)
        except Exception as e:
            logger.debug("yfinance history bars failed for %s: %s", symbol, e)

    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            query = """SELECT date, open, high, low, close, volume
                       FROM price_bar
                       WHERE symbol = ?
                       ORDER BY date ASC"""
            df = pd.read_sql_query(query, conn, params=(symbol,))
            if not df.empty:
                df.rename(
                    columns={
                        "date": "Date",
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "volume": "Volume",
                    },
                    inplace=True,
                )
                df.set_index("Date", inplace=True)
                return df.tail(lookback)
    except Exception as e:
        logger.debug("Failed to fetch price bars for %s: %s", symbol, e)
    return pd.DataFrame()


def generate_today_mission(market: str = "TH") -> dict[str, Any]:
    """Compile market scout candidates with Trader DNA into today's mission."""
    market_clean = market.upper()
    tasks_dir, orders_dir, mission_md, mission_json = get_mission_paths(market_clean)
    dna = je.load_dna(market=market_clean)
    open_pos = paper_trade.list_positions(
        status_filter="open", market=market_clean, portfolio="jules"
    )

    available_slots = max(0, 4 - len(open_pos))

    # 1. Gather candidates across all engines
    intraday_cands = get_latest_intraday_candidates(market=market_clean)
    if market_clean == "US":
        raw_pool = get_us_screened_candidates(limit=25) + intraday_cands
    else:
        thai_swing = get_latest_thai_swing_candidates()
        canslim = get_latest_canslim_candidates()
        vol_leaders = get_volume_anomaly_candidates()
        raw_pool = thai_swing + canslim + vol_leaders + intraday_cands

    # 2. Detect active Thematic Clusters across candidate pool
    cluster_detection = ai.detect_thematic_clusters(
        raw_pool, min_cluster_gainers=2, min_gain_pct=1.5, market=market_clean
    )
    active_clusters = cluster_detection.get("active_clusters", {})

    seen_symbols = set()
    combined_candidates = []

    for c in raw_pool:
        sym = c["symbol"].upper().strip()
        if sym in seen_symbols:
            continue

        if market_clean == "TH":
            # Skip unaffordable stocks where 1 board lot (100 shares) exceeds ฿10,000
            if c["price"] * 100 > 10000.0:
                continue
        else:
            # Skip unaffordable stocks where 1 share exceeds $250.0 slot budget
            if c["price"] > POSITION_BUDGET_USD:
                continue

        cluster_name = ai.get_cluster_for_symbol(sym, market=market_clean)
        if cluster_name and cluster_name in active_clusters:
            c["in_active_cluster"] = True
            c["score"] = float(c.get("score") or 60.0) + 15.0
            c["highlights"] = f"🚀 {cluster_name} Cluster | " + c.get("highlights", "")
        else:
            c["in_active_cluster"] = False

        # 3. Check for Distribution Trap via Recency-Weighted U/D Ratio
        bars_df = _get_stock_history_bars(sym, market=market_clean)
        if not bars_df.empty:
            ud_res = ai.calculate_recency_weighted_ud_ratio(bars_df)
            if ud_res["ud_ratio"] < 0.85:
                logger.info(
                    "Scout: Rejecting %s - Distribution trap (U/D %.2f < 0.85)",
                    sym,
                    ud_res["ud_ratio"],
                )
                continue
            c["ud_ratio"] = ud_res["ud_ratio"]

        # 4. Market Intelligence Disqualification Gate (News, Earnings, ADR, Overhead Supply)
        try:
            from scripts.market_intelligence_filter import evaluate_stock_intelligence

            intel_res = evaluate_stock_intelligence(
                symbol=sym,
                price=c["price"],
                market=market_clean,
            )
            if not intel_res.passed:
                logger.info("Scout: Disqualifying %s - %s", sym, intel_res.reason)
                continue
            c["score"] = float(c.get("score") or 60.0) + intel_res.composite_modifier
            if intel_res.rs_rating:
                c["rs_rating"] = intel_res.rs_rating
        except Exception as e:
            logger.debug("Market intelligence filter check failed for %s: %s", sym, e)

        seen_symbols.add(sym)

        # Calculate levels with resistance awareness
        levels = calculate_sizing_and_levels(
            price=c["price"],
            symbol=c["symbol"],
            suggested_stop=c.get("suggested_stop"),
            suggested_target=c.get("suggested_target"),
            market=market_clean,
        )
        c.update(levels)
        c["cluster"] = cluster_name
        combined_candidates.append(c)

    # Sort candidates by composite score descending
    combined_candidates.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)

    # 4. Anti-Correlation Selection: max 1 stock per sector / thematic cluster
    top_candidates = []
    selected_clusters: set[str] = set()
    selected_sectors: set[str] = set()

    for cand in combined_candidates:
        cluster = cand.get("cluster")
        sector = cand.get("sector")

        if cluster and cluster in selected_clusters:
            logger.info(
                "Scout Anti-Correlation: Skipping %s (cluster %s already represented)",
                cand["symbol"],
                cluster,
            )
            continue
        if (
            sector
            and sector in selected_sectors
            and sector not in ("N/A", "Volume Surge", "Unknown")
        ):
            logger.info(
                "Scout Anti-Correlation: Skipping %s (sector %s already represented)",
                cand["symbol"],
                sector,
            )
            continue

        top_candidates.append(cand)
        if cluster:
            selected_clusters.add(cluster)
        if sector and sector not in ("N/A", "Volume Surge", "Unknown"):
            selected_sectors.add(sector)

        if len(top_candidates) >= 4:
            break

    today_str = datetime.now().strftime("%Y-%m-%d")
    curr_sym = "$" if market_clean == "US" else "฿"
    curr_cap_str = "$1,000.00 USD" if market_clean == "US" else "฿30,000.00 THB"
    orders_folder_name = "state/jules_us_orders" if market_clean == "US" else "state/jules_orders"

    # Format Markdown Mission
    cand_rows_md = []
    yaml_templates_md = []

    for idx, cand in enumerate(top_candidates, 1):
        stop_pct = ((cand["stop"] - cand["price"]) / cand["price"]) * 100.0
        target_note = cand.get("target_note", f"{curr_sym}{cand['target']:.2f} (+2.0R)")
        cand_rows_md.append(
            f"| **{idx}. {cand['symbol']}** | {curr_sym}{cand['price']:.2f} | **{cand['shares']:,}** หุ้น | {curr_sym}{cand['est_cost']:,.2f} | {curr_sym}{cand['stop']:.2f} ({stop_pct:.1f}%) | {target_note} | {cand['highlights']} |"
        )
        yaml_templates_md.append(f"""```yaml
# Order Template {idx}: {cand["symbol"]}
# หากอนุมัติ ให้บันทึกเป็นไฟล์: {orders_folder_name}/buy_{cand["symbol"].replace(".BK", "")}.yaml
action: buy
symbol: "{cand["symbol"]}"
market: "{market_clean}"
shares: {cand["shares"]}
entry_price: {cand["price"]:.2f}
stop_price: {cand["stop"]:.2f}
target_price: {cand["target"]:.2f}
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: Scale-out 50% ที่ T1 (1.5R), ขยับ Stop บังทุน, ปล่อยรันเนอร์ไป T2 (2.5R)"
```""")

    table_body = (
        "\n".join(cand_rows_md)
        if cand_rows_md
        else "| ไม่มี Candidate ในวันนี้ | - | - | - | - | - | - |"
    )
    templates_body = "\n\n".join(yaml_templates_md)

    rules_text = "\n".join(f"- 📜 {r}" for r in dna.get("rules", []))
    weaknesses_text = (
        "\n".join(f"- ⚠️ {w}" for w in dna.get("weaknesses_to_correct", []))
        or "- ไม่มีข้อผิดพลาดซ้ำเดิมในประวัติ"
    )

    mission_content = f"""# 🎯 Jules AI Fund ({market_clean}): Daily Mission & Research Briefing
**วันที่:** {today_str} | **สถานะพอร์ต:** ว่าง {available_slots}/4 ไม้ | **เงินทุนเริ่มต้น:** {curr_cap_str}

---

## 🧬 Trader DNA Memory (Gen {dna.get("generation", 1)})
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
{rules_text}
- 🛡️ **Two-Tier Scale-Out Engine:** แบ่งขายทำกำไร 50% ที่เป้า T1 (+1.5R) และเลื่อน Stop Loss ขึ้นมาที่ทุน (Breakeven +0.05R buffer) ทันที เพื่อล็อกกำไรและตัดความเสี่ยง!
- 🏃 **Runner Trail to T2:** ปล่อย 50% ที่เหลือวิ่งไปเป้า T2 (+2.5R) โดยเริ่ม Ratchet ปกป้องกำไรเมื่อถึง +2.0R (ล็อก +1.0R)
- ⏱️ **Velocity Stall Exit:** หากถือครบ 4 วันทำการแล้วราคาไม่ไปไหน (MFE < 0.3R) ระบบจะคัดทิ้งทันทีเพื่อรักษาความคุ้มค่าของเงินทุน
- 🎯 **Resistance-Aware Exits:** หากมีแนวต้านยอดเดิมขวางอยู่ก่อนเป้าหมาย ให้ตั้งเป้าขายทำกำไรที่แนวต้านร่วมกับเจ้ามือทันที

### ⚠️ ข้อผิดพลาดในอดีตที่ห้ามทำซ้ำ:
{weaknesses_text}

---

## 🔍 รายชื่อหุ้นเป้าหมายวันนี้ (Top Scouted Candidates)
ระบบ VM Scout คัดกรองหุ้นสวิงโมเมนตัมและงบการเงินมาให้พิจารณา {len(top_candidates)} ตัว:

| Ticker | ราคาล่าสุด | จำนวนซื้อแนะนำ | วงเงินประมาณ | จุด Stop Loss | เป้าทำกำไร (Resistance-Aware) | สรุปประเด็นเด่น |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
{table_body}

---

## 📋 ภารกิจสำหรับ Jules (Action Required)
1. **คัดกรองปัจจัยพื้นฐาน (Fundamental & Business Check):**
   - ตรวจสอบโมเดลธุรกิจ: กำไรโตจริง หรือแค่ภาพลวงตา?
   - ค้นหาข่าวด่วนล่าสุดจาก Google Search: มีข่าวลบ / XD / Dilution หรือไม่?
2. **ตัดสินใจ (Approve or Veto):**
   - หากหุ้นตัวใดผ่านเกณฑ์ และเข้าตา Jules ที่สุด **เลือก 1 ตัว**
   - บันทึกไฟล์ Order ตาม Template ด้านล่างลงในโฟลเดอร์ `{orders_folder_name}/`
   - เมื่อ Push ขึ้น GitHub แล้ว ระบบบน VM จะเข้าซื้อให้อัตโนมัติ!

---

## 📝 คำสั่งซื้อสำเร็จรูป (Order Templates)
{templates_body}
"""

    mission_md.write_text(mission_content, encoding="utf-8")

    payload = {
        "generated_at": isoformat_seconds(),
        "market": market_clean,
        "dna_generation": dna.get("generation", 1),
        "available_slots": available_slots,
        "candidates": top_candidates,
    }
    with open(mission_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(
        "Generated today's mission at %s with %d candidates", mission_md, len(top_candidates)
    )
    return payload


def main():
    parser = argparse.ArgumentParser(description="Jules Autonomous Scout Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run")
    run_p.add_argument(
        "--market", choices=["TH", "US"], default="TH", help="Target equity market (TH or US)"
    )

    show_p = sub.add_parser("show")
    show_p.add_argument(
        "--market", choices=["TH", "US"], default="TH", help="Target equity market (TH or US)"
    )

    args = parser.parse_args()

    if args.cmd == "run":
        res = generate_today_mission(market=args.market)
        _, _, mission_md, _ = get_mission_paths(args.market)
        print(
            f"Mission ({args.market}) generated successfully with {len(res['candidates'])} candidates."
        )
        print(f"File: {mission_md}")
    elif args.cmd == "show":
        _, _, mission_md, _ = get_mission_paths(args.market)
        if mission_md.exists():
            print(mission_md.read_text(encoding="utf-8"))
        else:
            print(
                f"No active mission found for {args.market}. Run 'python scripts/jules_scout.py run --market {args.market}' first."
            )


if __name__ == "__main__":
    main()
