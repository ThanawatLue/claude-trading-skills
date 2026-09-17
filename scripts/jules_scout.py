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

import paper_trade

import scripts.jules_evolver as je
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


def _ensure_dirs():
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    ORDERS_DIR.mkdir(parents=True, exist_ok=True)


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
) -> dict[str, Any]:
    """Calculate SET Board Lot shares, tight stop, and resistance-aware target."""
    if price <= 0:
        return {"shares": 100, "stop": 0.0, "target": 0.0, "est_cost": 0.0}

    # Board lot = 100 shares
    raw_shares = int(POSITION_BUDGET_THB // price)
    shares = max(100, (raw_shares // 100) * 100)

    # Stop Loss: use suggested_stop if valid and below price, else 5% default
    if suggested_stop and 0 < suggested_stop < price:
        stop = round(suggested_stop, 2)
    else:
        stop = round(price * 0.95, 2)

    risk_per_share = price - stop
    default_target = round(price + (risk_per_share * 2.0), 2)

    # Resistance-Aware Check: take profit before the smart-money dump
    resistance = find_nearest_resistance(symbol, price) if symbol else None
    if resistance and (price + risk_per_share * 1.1) <= resistance <= default_target:
        target = round(resistance, 2)
        target_note = f"฿{target:.2f} (Resistance Pivot)"
    elif suggested_target and suggested_target > price:
        target = round(suggested_target, 2)
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


def generate_today_mission(market: str = "TH") -> dict[str, Any]:
    """Compile market scout candidates with Trader DNA into today's mission."""
    _ensure_dirs()
    dna = je.load_dna()
    open_pos = paper_trade.list_positions(status_filter="open", market=market, portfolio="jules")

    available_slots = max(0, 4 - len(open_pos))

    # 1. Gather candidates across all engines: Thai Swing, CANSLIM, Volume Anomaly
    thai_swing = get_latest_thai_swing_candidates()
    canslim = get_latest_canslim_candidates()
    vol_leaders = get_volume_anomaly_candidates()

    seen_symbols = set()
    combined_candidates = []

    # Prioritize: Thai Swing setups -> CANSLIM leaders -> Volume surge
    for c in thai_swing + canslim + vol_leaders:
        sym = c["symbol"].upper()
        if sym in seen_symbols:
            continue
        # Skip unaffordable stocks where 1 board lot (100 shares) exceeds ฿10,000
        if c["price"] * 100 > 10000.0:
            continue

        seen_symbols.add(sym)

        # Calculate levels with resistance awareness
        levels = calculate_sizing_and_levels(
            price=c["price"],
            symbol=c["symbol"],
            suggested_stop=c.get("suggested_stop"),
            suggested_target=c.get("suggested_target"),
        )
        c.update(levels)
        combined_candidates.append(c)

    # Select top 3-4 candidates
    top_candidates = combined_candidates[:4]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Format Markdown Mission
    cand_rows_md = []
    yaml_templates_md = []

    for idx, cand in enumerate(top_candidates, 1):
        stop_pct = ((cand["stop"] - cand["price"]) / cand["price"]) * 100.0
        target_note = cand.get("target_note", f"฿{cand['target']:.2f} (+2.0R)")
        cand_rows_md.append(
            f"| **{idx}. {cand['symbol']}** | ฿{cand['price']:.2f} | **{cand['shares']:,}** หุ้น | ฿{cand['est_cost']:,.2f} | ฿{cand['stop']:.2f} ({stop_pct:.1f}%) | {target_note} | {cand['highlights']} |"
        )
        yaml_templates_md.append(f"""```yaml
# Order Template {idx}: {cand["symbol"]}
# หากอนุมัติ ให้บันทึกเป็นไฟล์: state/jules_orders/buy_{cand["symbol"].replace(".BK", "")}.yaml
action: buy
symbol: "{cand["symbol"]}"
shares: {cand["shares"]}
entry_price: {cand["price"]:.2f}
stop_price: {cand["stop"]:.2f}
target_price: {cand["target"]:.2f}
thesis: "วิเคราะห์โมเดลธุรกิจ: [ใส่เหตุผลสั้นๆ ที่นี่] | Catalyst: [ใส่ปัจจัยเร่ง] | แผน: MFE +0.5R ขยับ Stop บังทุนทันที"
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

    mission_content = f"""# 🎯 Jules AI Fund: Daily Mission & Research Briefing
**วันที่:** {today_str} | **สถานะพอร์ต:** ว่าง {available_slots}/4 ไม้ | **เงินทุนเริ่มต้น:** ฿30,000.00 THB

---

## 🧬 Trader DNA Memory (Gen {dna.get("generation", 1)})
Jules ต้องใช้กฎที่เรียนรู้มาในอดีตมาช่วยตัดสินใจเลือกลงทุน:
{rules_text}
- 🛡️ **MFE Ratchet Protection:** หากราคาหุ้นบวกแตะ +0.5R ระบบจะเลื่อน Stop Loss ขึ้นมาที่ทุน (Breakeven) อัตโนมัติ เพื่อป้องกันไม่ให้กำไรกลายเป็นขาดทุน!
- 🎯 **Resistance-Aware Exits:** หากมีแนวต้านยอดเดิมขวางอยู่ก่อน 2.0R ให้ตั้งเป้าขายทำกำไรที่แนวต้านร่วมกับเจ้ามือทันที

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
   - ค้นหาข่าวด่วนล่าสุดจาก Google Search หรือข่าวทันหุ้น: มีข่าวลบ / XD / Dilution หรือไม่?
2. **ตัดสินใจ (Approve or Veto):**
   - หากหุ้นตัวใดผ่านเกณฑ์ และเข้าตา Jules ที่สุด **เลือก 1 ตัว**
   - บันทึกไฟล์ Order ตาม Template ด้านล่างลงในโฟลเดอร์ `state/jules_orders/`
   - เมื่อ Push ขึ้น GitHub แล้ว ระบบบน VM จะเข้าซื้อให้อัตโนมัติ!

---

## 📝 คำสั่งซื้อสำเร็จรูป (Order Templates)
{templates_body}
"""

    MISSION_MD.write_text(mission_content, encoding="utf-8")

    payload = {
        "generated_at": isoformat_seconds(),
        "market": market,
        "dna_generation": dna.get("generation", 1),
        "available_slots": available_slots,
        "candidates": top_candidates,
    }
    with open(MISSION_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(
        "Generated today's mission at %s with %d candidates", MISSION_MD, len(top_candidates)
    )
    return payload


def main():
    parser = argparse.ArgumentParser(description="Jules Autonomous Scout Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run")
    sub.add_parser("show")

    args = parser.parse_args()

    if args.cmd == "run":
        res = generate_today_mission()
        print(f"Mission generated successfully with {len(res['candidates'])} candidates.")
        print(f"File: {MISSION_MD}")
    elif args.cmd == "show":
        if MISSION_MD.exists():
            print(MISSION_MD.read_text(encoding="utf-8"))
        else:
            print("No active mission found. Run 'python scripts/jules_scout.py run' first.")


if __name__ == "__main__":
    main()
