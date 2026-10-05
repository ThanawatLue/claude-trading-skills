#!/usr/bin/env python3
"""NVDR Program Trading & Net Flow Divergence Filter.

Protects Thai swing momentum trades against institutional distribution and bull traps:
- Detects when retail chases price surges while NVDR / proprietary program desks net dump into the liquidity.
- Identifies strong institutional accumulation providing follow-through tailwinds.
- Integrates with Jules Autonomous Decision Engine (`scripts/jules_trader.py`).

Usage:
    python scripts/nvdr_flow_filter.py check KBANK
    python scripts/nvdr_flow_filter.py summary
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nvdr_flow_filter")


@dataclass
class NVDRAnalysis:
    symbol: str
    status: str  # "DIVERGENCE_BULL_TRAP", "ACCUMULATION", "NEUTRAL", "NO_DATA"
    is_bull_trap: bool
    score_modifier: float
    net_val_1d: float
    net_val_5d: float
    nvdr_pct_1d: float
    details: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def init_nvdr_table(db_path: Path | None = None) -> None:
    """Initialize SQLite nvdr_flow table with indexes for fast queries."""
    target_db = db_path or DB_PATH
    target_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target_db) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS nvdr_flow (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                buy_vol INTEGER,
                sell_vol INTEGER,
                net_vol INTEGER,
                buy_val REAL,
                sell_val REAL,
                net_val REAL,
                nvdr_ratio REAL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (symbol, date)
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_nvdr_sym_date ON nvdr_flow (symbol, date DESC)"
        )
        conn.commit()


def upsert_nvdr_flow(records: list[dict[str, Any]], db_path: Path | None = None) -> int:
    """Upsert daily NVDR records into SQLite."""
    if not records:
        return 0
    target_db = db_path or DB_PATH
    init_nvdr_table(target_db)
    now_str = datetime.now(timezone.utc).isoformat()
    inserted = 0

    with sqlite3.connect(target_db) as conn:
        for r in records:
            sym = str(r.get("symbol", "")).upper().replace(".BK", "")
            if not sym:
                continue
            date_str = str(r.get("date", ""))
            buy_vol = int(r.get("buy_vol") or 0)
            sell_vol = int(r.get("sell_vol") or 0)
            net_vol = int(r.get("net_vol") or (buy_vol - sell_vol))
            buy_val = float(r.get("buy_val") or 0.0)
            sell_val = float(r.get("sell_val") or 0.0)
            net_val = float(r.get("net_val") or (buy_val - sell_val))
            nvdr_ratio = float(r.get("nvdr_ratio") or 0.0)

            conn.execute(
                """INSERT OR REPLACE INTO nvdr_flow
                   (symbol, date, buy_vol, sell_vol, net_vol, buy_val, sell_val, net_val, nvdr_ratio, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sym,
                    date_str,
                    buy_vol,
                    sell_vol,
                    net_vol,
                    buy_val,
                    sell_val,
                    net_val,
                    nvdr_ratio,
                    now_str,
                ),
            )
            inserted += 1
        conn.commit()
    return inserted


def get_nvdr_flow(symbol: str, days: int = 5, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Retrieve the most recent daily NVDR records for a symbol."""
    target_db = db_path or DB_PATH
    if not target_db.exists():
        return []
    sym = symbol.upper().replace(".BK", "")
    try:
        with sqlite3.connect(target_db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT symbol, date, buy_vol, sell_vol, net_vol, buy_val, sell_val, net_val, nvdr_ratio
                   FROM nvdr_flow
                   WHERE symbol = ?
                   ORDER BY date DESC
                   LIMIT ?""",
                (sym, days),
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.debug("Failed to query nvdr_flow for %s: %s", sym, e)
        return []


def analyze_nvdr_divergence(
    symbol: str,
    current_price: float,
    price_change_pct: float = 0.0,
    db_path: Path | None = None,
    days: int = 5,
) -> NVDRAnalysis:
    """Analyze NVDR institutional flow divergence against price action.

    Thresholds:
    - Bull Trap: Price is rallying/breaking out (price_change_pct > 0.5%), but:
        1D NVDR Net Sell < -10M THB OR
        5D NVDR Net Sell < -25M THB OR
        NVDR selling > 15% of turnover with net_vol < 0.
        -> Reject candidate / Apply -25.0 score penalty.
    - Institutional Accumulation:
        1D NVDR Net Buy > +10M THB OR
        5D NVDR Net Buy > +30M THB, with net_vol > 0.
        -> Apply +15.0 score bonus.
    - Neutral:
        Flow is balanced or insignificant.
    - No Data:
        Graceful fallback with 0 modifier when data has not been ingested yet.
    """
    flow = get_nvdr_flow(symbol, days=days, db_path=db_path)
    if not flow:
        return NVDRAnalysis(
            symbol=symbol,
            status="NO_DATA",
            is_bull_trap=False,
            score_modifier=0.0,
            net_val_1d=0.0,
            net_val_5d=0.0,
            nvdr_pct_1d=0.0,
            details="No NVDR data recorded; proceeding with neutral posture.",
        )

    rec_1d = flow[0]
    net_val_1d = float(rec_1d.get("net_val") or 0.0)
    net_vol_1d = int(rec_1d.get("net_vol") or 0)
    nvdr_ratio_1d = float(rec_1d.get("nvdr_ratio") or 0.0)

    net_val_5d = sum(float(r.get("net_val") or 0.0) for r in flow)

    # 1. Bull Trap Divergence Check
    # Stock is moving up or breaking out, but institutional NVDR is dumping into the rally
    is_price_up = price_change_pct > 0.5
    heavy_dump_1d = net_val_1d <= -10_000_000.0
    heavy_dump_5d = net_val_5d <= -25_000_000.0
    relative_dump = net_vol_1d < 0 and nvdr_ratio_1d >= 15.0 and net_val_1d <= -5_000_000.0

    if is_price_up and (heavy_dump_1d or heavy_dump_5d or relative_dump):
        details = (
            f"Bull trap warning: Stock up {price_change_pct:+.1f}% but NVDR net dumped "
            f"฿{abs(net_val_1d) / 1e6:.1f}M (5D net: ฿{net_val_5d / 1e6:+.1f}M, NVDR ratio: {nvdr_ratio_1d:.1f}%)"
        )
        return NVDRAnalysis(
            symbol=symbol,
            status="DIVERGENCE_BULL_TRAP",
            is_bull_trap=True,
            score_modifier=-25.0,
            net_val_1d=net_val_1d,
            net_val_5d=net_val_5d,
            nvdr_pct_1d=nvdr_ratio_1d,
            details=details,
        )

    # 2. Institutional Accumulation Check
    heavy_buy_1d = net_val_1d >= 10_000_000.0 and net_vol_1d > 0
    heavy_buy_5d = net_val_5d >= 30_000_000.0 and net_vol_1d >= 0

    if heavy_buy_1d or heavy_buy_5d:
        details = (
            f"Institutional accumulation confirmed: NVDR net bought "
            f"฿{net_val_1d / 1e6:+.1f}M (5D net: ฿{net_val_5d / 1e6:+.1f}M, NVDR ratio: {nvdr_ratio_1d:.1f}%)"
        )
        return NVDRAnalysis(
            symbol=symbol,
            status="ACCUMULATION",
            is_bull_trap=False,
            score_modifier=15.0,
            net_val_1d=net_val_1d,
            net_val_5d=net_val_5d,
            nvdr_pct_1d=nvdr_ratio_1d,
            details=details,
        )

    # 3. Neutral Flow
    return NVDRAnalysis(
        symbol=symbol,
        status="NEUTRAL",
        is_bull_trap=False,
        score_modifier=0.0,
        net_val_1d=net_val_1d,
        net_val_5d=net_val_5d,
        nvdr_pct_1d=nvdr_ratio_1d,
        details=f"NVDR flow neutral (1D: ฿{net_val_1d / 1e6:+.1f}M, 5D: ฿{net_val_5d / 1e6:+.1f}M)",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="NVDR Program Trading & Net Flow Filter")
    subparsers = parser.add_subparsers(dest="command")

    check_p = subparsers.add_parser("check", help="Check NVDR status for a symbol")
    check_p.add_argument("symbol", help="Stock symbol, e.g. KBANK")
    check_p.add_argument("--price", type=float, default=100.0, help="Current stock price")
    check_p.add_argument("--change", type=float, default=1.5, help="Current day pct price change")

    subparsers.add_parser("init", help="Initialize SQLite nvdr_flow table")

    args = parser.parse_args()

    if args.command == "init":
        init_nvdr_table()
        print(f"Initialized NVDR table in {DB_PATH}")
        return 0

    if args.command == "check":
        analysis = analyze_nvdr_divergence(
            symbol=args.symbol,
            current_price=args.price,
            price_change_pct=args.change,
        )
        print(f"Symbol: {analysis.symbol}")
        print(f"Status: {analysis.status}")
        print(f"Bull Trap: {analysis.is_bull_trap}")
        print(f"Score Modifier: {analysis.score_modifier:+.1f}")
        print(f"1D Net Val: ฿{analysis.net_val_1d:,.2f}")
        print(f"5D Net Val: ฿{analysis.net_val_5d:,.2f}")
        print(f"Details: {analysis.details}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
