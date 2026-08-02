#!/usr/bin/env python3
"""
Thai Swing Trade Screener — 3-5 day setups.

Two strategies:
  DIP_BUY   - RSI 35-52 daily + price < SMA20 + above SMA50 + weekly RSI > 42 + vol ≥ 0.8x avg
  MOMENTUM  - RSI 55-72 daily + volume > 1.4x avg + weekly RSI > 52 + risk ≤ 6% + score ≥ 50

Quality filters (post-scoring):
  Dip Buy  : price must be BELOW SMA20 (confirmed pullback), reward ≥ 3%, vol ≥ 0.8x avg
  Momentum : score ≥ 50 (no borderline setups), max risk ≤ 6%, reward ≥ 3%

Data: TradingView Screener (bulk, one call) + yfinance (ATR for top candidates).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from scripts.lib.tv_client import (
    get_thai_stocks,
    is_available as tv_available,
    get_set_memberships,
    tag_with_memberships,
    clean_for_json,
)

MIN_PRICE = 2.0

# Dip Buy thresholds
DIP_RSI_MIN = 35
DIP_RSI_MAX = 52
DIP_WEEKLY_RSI_MIN = 42
DIP_MIN_VOL_RATIO = 0.8       # must have real interest — dead-volume dips excluded
DIP_MIN_REWARD_PCT = 3.0      # reward must be ≥ 3% to cover slippage + commission

# Momentum thresholds
MOM_RSI_MIN = 55
MOM_RSI_MAX = 72
MOM_VOL_RATIO_MIN = 1.4
MOM_WEEKLY_RSI_MIN = 52
MOM_MAX_FROM_52W_HIGH = 0.12
MOM_MAX_RISK_PCT = 6.0        # stop too wide → skip for 3-5 day hold
MOM_MIN_REWARD_PCT = 3.0      # same minimum reward as dip buy


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_dip_buy(s: dict) -> float:
    rsi = s.get("rsi") or 0
    rsi_w = s.get("rsi_weekly") or 0
    price = s.get("price") or 0
    sma50 = s.get("sma50") or 0
    sma200 = s.get("sma200") or 0
    avg_vol = max(s.get("avgVolume") or 1, 1)
    vol = s.get("volume") or 0
    vol_ratio = vol / avg_vol

    if not (DIP_RSI_MIN <= rsi <= DIP_RSI_MAX):
        return 0.0
    if price <= 0 or sma50 <= 0 or price < sma50:
        return 0.0
    if sma200 > 0 and price < sma200:
        return 0.0
    if rsi_w < DIP_WEEKLY_RSI_MIN:
        return 0.0
    if vol_ratio < DIP_MIN_VOL_RATIO:  # hard filter: must have real volume activity
        return 0.0
    sma20 = s.get("sma20") or 0
    # Require price to be at least 0.5% below SMA20 (guards against float equality
    # and ensures a real pullback occurred — not just touching the moving average)
    if sma20 > 0 and price >= sma20 * 0.995:
        return 0.0

    # RSI sweet spot ~44 (oversold but not broken)
    rsi_score = max(0.0, min(100.0, 100 - abs(rsi - 44) * 4))
    weekly_score = min(100.0, (rsi_w - DIP_WEEKLY_RSI_MIN) * 3)
    # Volume: scale from 0.8x baseline; 2x = 100, penalise near-minimum
    vol_score = min(100.0, (vol_ratio - DIP_MIN_VOL_RATIO) / (2.0 - DIP_MIN_VOL_RATIO) * 100)

    # Ideally 0-5% above SMA50 (just bounced off support)
    sma50_dist = (price - sma50) / sma50
    if sma50_dist < 0:
        prox_score = 0.0
    elif sma50_dist <= 0.05:
        prox_score = 100.0
    elif sma50_dist <= 0.15:
        prox_score = max(0.0, 100 - (sma50_dist - 0.05) * 500)
    else:
        prox_score = 40.0

    return round(rsi_score * 0.35 + weekly_score * 0.25 + vol_score * 0.15 + prox_score * 0.25, 1)


def score_momentum(s: dict) -> float:
    rsi = s.get("rsi") or 0
    rsi_w = s.get("rsi_weekly") or 0
    price = s.get("price") or 0
    sma20 = s.get("sma20") or 0
    high52 = s.get("yearHigh") or 0
    avg_vol = max(s.get("avgVolume") or 1, 1)
    vol = s.get("volume") or 0
    vol_ratio = vol / avg_vol

    if not (MOM_RSI_MIN <= rsi <= MOM_RSI_MAX):
        return 0.0
    if price <= 0 or sma20 <= 0 or price < sma20:
        return 0.0
    if rsi_w < MOM_WEEKLY_RSI_MIN:
        return 0.0
    if vol_ratio < MOM_VOL_RATIO_MIN:
        return 0.0
    if high52 > 0 and price < high52 * (1 - MOM_MAX_FROM_52W_HIGH):
        return 0.0

    # RSI sweet spot ~63
    rsi_score = max(0.0, min(100.0, 100 - abs(rsi - 63) * 5))
    vol_score = min(100.0, (vol_ratio - 1.0) * 50)
    weekly_score = min(100.0, (rsi_w - MOM_WEEKLY_RSI_MIN) * 2.5)
    high_score = max(0.0, 100 - ((high52 - price) / high52 * 800)) if high52 > 0 else 50.0

    return round(rsi_score * 0.30 + vol_score * 0.30 + weekly_score * 0.20 + high_score * 0.20, 1)


# ---------------------------------------------------------------------------
# ATR + trade plan
# ---------------------------------------------------------------------------

def fetch_atr(symbol: str, lookback: int = 20) -> dict:
    try:
        import yfinance as yf

        hist = yf.Ticker(symbol).history(period=f"{lookback + 5}d")
        if hist.empty or len(hist) < 5:
            return {}

        closes = hist["Close"].tolist()
        highs = hist["High"].tolist()
        lows = hist["Low"].tolist()

        n = min(14, len(closes) - 1)
        trs = [
            max(highs[-(i + 1)] - lows[-(i + 1)],
                abs(highs[-(i + 1)] - closes[-(i + 2)]),
                abs(lows[-(i + 1)] - closes[-(i + 2)]))
            for i in range(n)
        ]
        atr = sum(trs) / len(trs) if trs else 0
        recent_low = min(lows[-5:]) if len(lows) >= 5 else lows[-1]
        return {"atr": atr, "recent_low": recent_low}
    except Exception:
        return {}


def build_plan(price: float, strategy: str, atr: float, recent_low: float) -> dict:
    entry = price
    if atr > 0:
        # DIP_BUY: 1.5x ATR (tighter — we're buying near support)
        # MOMENTUM: 1.5x ATR (same; wide stops kill R/R on short holds)
        atr_mult = 1.5
        stop = max(recent_low * 0.99, entry - atr_mult * atr)
    else:
        stop = entry * (0.95 if strategy == "DIP_BUY" else 0.95)
    # Ensure stop doesn't compress to < 1% (avoid nonsense plans)
    if (entry - stop) / entry < 0.01:
        stop = entry * 0.97
    risk = entry - stop
    target = entry + 2.0 * risk   # 2:1 R/R minimum
    return {
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "risk_pct": round(risk / entry * 100, 1),
        "reward_pct": round(risk * 2 / entry * 100, 1),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _row_dip(i: int, s: dict) -> str:
    p = s["_plan"]
    avg_vol = max(s.get("avgVolume") or 1, 1)
    vol_r = (s.get("volume") or 0) / avg_vol
    sma50 = s.get("sma50") or 0
    price = s.get("price") or 0
    sma50_dist = f"+{(price / sma50 - 1) * 100:.1f}%" if sma50 > 0 else "—"
    return (
        f"| {i} | **{s['symbol']}** | {s['_score']:.0f} | "
        f"{s.get('rsi', 0):.1f} | {s.get('rsi_weekly', 0):.1f} | "
        f"{vol_r:.1f}x | {sma50_dist} | "
        f"฿{p['entry']:.2f} | ฿{p['stop']:.2f} | ฿{p['target']:.2f} | {p['risk_pct']:.1f}% |"
    )


def _row_mom(i: int, s: dict) -> str:
    p = s["_plan"]
    avg_vol = max(s.get("avgVolume") or 1, 1)
    vol_r = (s.get("volume") or 0) / avg_vol
    high52 = s.get("yearHigh") or 0
    price = s.get("price") or 0
    h52 = f"-{(1 - price / high52) * 100:.1f}%" if high52 > 0 else "—"
    return (
        f"| {i} | **{s['symbol']}** | {s['_score']:.0f} | "
        f"{s.get('rsi', 0):.1f} | {s.get('rsi_weekly', 0):.1f} | "
        f"{vol_r:.1f}x | {h52} | "
        f"฿{p['entry']:.2f} | ฿{p['stop']:.2f} | ฿{p['target']:.2f} | {p['risk_pct']:.1f}% |"
    )


def _detail(s: dict) -> list[str]:
    p = s["_plan"]
    avg_vol = max(s.get("avgVolume") or 1, 1)
    vol_r = (s.get("volume") or 0) / avg_vol
    price = s.get("price") or 0
    gain_pct = (p["target"] / p["entry"] - 1) * 100
    lines = [
        f"#### {s['symbol']} — {s.get('name', '')}",
        f"**Sector:** {s.get('sector', '—')} | **Score:** {s['_score']:.0f}/100",
        f"- RSI: **{s.get('rsi', 0):.1f}** daily / **{s.get('rsi_weekly', 0):.1f}** weekly",
        f"- Volume: **{vol_r:.1f}x** avg  ({int(s.get('volume', 0) / 1000):,}K vs avg {int(avg_vol / 1000):,}K)",
        f"- Price: ฿{price:.2f}  |  SMA20: ฿{s.get('sma20', 0):.2f}  |  SMA50: ฿{s.get('sma50', 0):.2f}",
        f"- **Entry:** ฿{p['entry']:.2f}  |  **Stop:** ฿{p['stop']:.2f} (-{p['risk_pct']:.1f}%)  |  **Target:** ฿{p['target']:.2f} (+{gain_pct:.1f}%)  |  R/R: 2:1",
        "",
    ]
    return lines


def get_recent_expectancy(source_name: str, lookback: int = 15) -> tuple[float | None, int]:
    """Get the average realized R-multiple of the last 15 closed trades for this source."""
    import sqlite3
    import sys
    from pathlib import Path
    
    base_dir = Path(__file__).resolve().parents[3]
    db_path = base_dir / "state" / "market_cache.db"
    if not db_path.exists():
        return None, 0
    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trade'")
        if not cur.fetchone():
            conn.close()
            return None, 0
        rows = cur.execute(
            """SELECT realized_r FROM paper_trade 
               WHERE (source = ? OR source = ?) AND status != 'open' 
               ORDER BY exit_at DESC LIMIT ?""",
            (source_name, source_name.replace("-screener", ""), lookback)
        ).fetchall()
        conn.close()
        if not rows:
            return None, 0
        realized = [r["realized_r"] for r in rows if r["realized_r"] is not None]
        if not realized:
            return None, 0
        return sum(realized) / len(realized), len(realized)
    except Exception as e:
        print(f"  [Expectancy Check] Warning: Could not read paper trade stats: {e}", file=sys.stderr)
        return None, 0


def build_report(dip: list, mom: list, ts: str, universe: int) -> str:
    # Query expectancies
    exp_dip, count_dip = get_recent_expectancy("thai-swing-dip", lookback=15)
    exp_mom, count_mom = get_recent_expectancy("thai-swing-momentum", lookback=15)

    L = [
        "# Thai Swing Trade Screener — 3–5 Day Setups",
        f"**Generated:** {ts}  |  **Universe:** {universe} SET stocks",
        "",
    ]

    # Add calibration warnings if appropriate
    if (exp_dip is not None and exp_dip < 0) or (exp_mom is not None and exp_mom < 0):
        L.append("## Strategy Expectancy Calibration Alerts")
        if exp_dip is not None:
            L.append(f"- **Dip Buy (thai-swing-dip)** Expectancy: **{exp_dip:+.2f}R** ({count_dip} closed trades)")
            if exp_dip < 0:
                L.append("  > [!WARNING]")
                L.append("  > **Negative Expectancy:** Consider raising Dip Buy entry parameters or skipping marginal setups.")
        if exp_mom is not None:
            L.append(f"- **Momentum (thai-swing-momentum)** Expectancy: **{exp_mom:+.2f}R** ({count_mom} closed trades)")
            if exp_mom < 0:
                L.append("  > [!WARNING]")
                L.append("  > **Negative Expectancy:** Consider raising momentum score threshold to **85+** and reducing position size.")
        L.append("")
        L.append("---")
        L.append("")
    
    L += [
        "",
        "## Strategies",
        "",
        "| Strategy | Signal | Typical Hold | R/R Target |",
        "|----------|--------|-------------|------------|",
        "| **Dip Buy** | RSI 35–52 + above SMA50 + weekly RSI > 42 | 2–4 days | 2:1 |",
        "| **Momentum** | RSI 55–72 + volume > 1.4× avg + weekly RSI > 52 | 3–5 days | 2:1 |",
        "",
        "---",
        "",
        "## A: Dip Buy (Pullback in Uptrend)",
        "",
        "> หุ้นใน uptrend ที่ RSI ถอยลง oversold zone ชั่วคราว — รอ bounce กลับ",
        "",
    ]

    if not dip:
        L.append("*ไม่พบ Dip Buy setup วันนี้*\n")
    else:
        L += [
            "| # | Symbol | Score | RSI | RSI(W) | Vol | SMA50 Dist | Entry | Stop | Target | Risk |",
            "|---|--------|-------|-----|--------|-----|-----------|-------|------|--------|------|",
        ]
        for i, s in enumerate(dip, 1):
            L.append(_row_dip(i, s))
        L += ["", "### Details", ""]
        for s in dip[:5]:
            L += _detail(s)

    L += [
        "---",
        "",
        "## B: Momentum Continuation",
        "",
        "> หุ้นที่ volume surge วันนี้ + RSI momentum zone — เข้าตาม momentum รอ continuation",
        "",
    ]

    if not mom:
        L.append("*ไม่พบ Momentum setup วันนี้*\n")
    else:
        L += [
            "| # | Symbol | Score | RSI | RSI(W) | Vol | 52W High | Entry | Stop | Target | Risk |",
            "|---|--------|-------|-----|--------|-----|---------|-------|------|--------|------|",
        ]
        for i, s in enumerate(mom, 1):
            L.append(_row_mom(i, s))
        L += ["", "### Details", ""]
        for s in mom[:5]:
            L += _detail(s)

    L += [
        "---",
        "",
        "## Risk Guidelines",
        "",
        "- **Size:** Risk ≤ 1% ของ portfolio ต่อ trade",
        "- **Stop:** Hard stop — exit ทันทีถ้าปิดต่ำกว่า stop",
        "- **Partial exit:** Take 50% ที่ 1R, ปล่อยส่วนที่เหลือถึง 2R",
        "- **Time stop:** ถ้าไม่มีการเคลื่อนไหวใน 3 sessions ให้พิจารณา exit",
        "- **Market filter:** ตรวจ SET index trend ก่อน — อย่าซื้อสวนตลาด",
        "",
        "---",
        "",
        "> ⚠️ Algorithmic screening เท่านั้น ไม่ใช่คำแนะนำการลงทุน",
    ]

    return "\n".join(L)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re as _re

_DR_PATTERN = _re.compile(r"^[A-Z]+\d{2}\.BK$")   # e.g. SNOW23.BK, MSFT23.BK, PLTR23.BK


def _is_dr_or_warrant(symbol: str) -> bool:
    """Return True for DR certificates (tickerNN.BK) and common warrant suffixes."""
    if _DR_PATTERN.match(symbol):
        return True
    base = symbol.replace(".BK", "")
    return base.endswith("-W") or base.endswith("W") and len(base) > 4 and base[-5].isdigit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Thai Swing Trade Screener (3-5 day)")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument("--min-market-cap", type=float, default=2_000_000_000)
    parser.add_argument("--min-avg-volume", type=float, default=200_000)
    parser.add_argument("--no-atr", action="store_true", help="Skip ATR fetch (faster, less precise stops)")
    args = parser.parse_args()

    print("=" * 70)
    print("Thai Swing Trade Screener — 3-5 Day Setups")
    print("=" * 70)

    if not tv_available():
        print("ERROR: tradingview-screener not installed. Run: pip install tradingview-screener")
        sys.exit(1)

    print("\nPhase 1: Fetching Thai market data via TradingView...")
    stocks = get_thai_stocks(
        limit=1000,
        min_market_cap=args.min_market_cap,
        min_avg_volume=args.min_avg_volume,
    )
    stocks = [
        s for s in stocks
        if (s.get("price") or 0) >= MIN_PRICE
        and not s["symbol"].endswith(".R.BK")   # rights/warrants
        and not _is_dr_or_warrant(s["symbol"])  # DR certificates (SNOW23.BK etc.)
    ]
    print(f"  {len(stocks)} stocks after basic filters (excl. DRs/rights/warrants)")

    print("\nPhase 2: Scoring...")
    dip_list, mom_list = [], []
    for s in stocks:
        d = score_dip_buy(s)
        if d >= 40:
            sc = dict(s)
            sc["_strategy"] = "DIP_BUY"
            sc["_score"] = d
            dip_list.append(sc)

        m = score_momentum(s)
        if m >= 50:
            sc = dict(s)
            sc["_strategy"] = "MOMENTUM"
            sc["_score"] = m
            mom_list.append(sc)

    dip_list.sort(key=lambda x: x["_score"], reverse=True)
    mom_list.sort(key=lambda x: x["_score"], reverse=True)
    top_dip = dip_list[: args.top]
    top_mom = mom_list[: args.top]
    print(f"  Dip Buy: {len(dip_list)} candidates -> top {len(top_dip)}")
    print(f"  Momentum: {len(mom_list)} candidates -> top {len(top_mom)}")

    # ATR fetch
    all_top = {s["symbol"]: s for s in top_dip + top_mom}
    if not args.no_atr and all_top:
        print(f"\nPhase 3: Fetching ATR for {len(all_top)} stocks...")
        for sym, s in all_top.items():
            d = fetch_atr(sym)
            s["_atr"] = d
            print(f"  {sym}: ATR={d.get('atr', 0):.2f}" if d else f"  {sym}: no data")
    else:
        for s in all_top.values():
            s["_atr"] = {}

    # Trade plans
    for s in top_dip + top_mom:
        atr_d = s.get("_atr") or {}
        price = s.get("price") or 0
        s["_plan"] = build_plan(
            price, s["_strategy"],
            atr_d.get("atr", 0),
            atr_d.get("recent_low", price * 0.95),
        )

    # Post-scoring quality filters (applied after plans are built)
    before_dip = len(top_dip)
    before_mom = len(top_mom)
    top_dip = [
        s for s in top_dip
        if s["_plan"]["reward_pct"] >= DIP_MIN_REWARD_PCT
    ]
    top_mom = [
        s for s in top_mom
        if s["_plan"]["risk_pct"] <= MOM_MAX_RISK_PCT
        and s["_plan"]["reward_pct"] >= MOM_MIN_REWARD_PCT
    ]
    print(f"\nPhase 4: Quality filters")
    print(f"  Dip Buy:  {before_dip} -> {len(top_dip)} (removed {before_dip - len(top_dip)} low-reward)")
    print(f"  Momentum: {before_mom} -> {len(top_mom)} (removed {before_mom - len(top_mom)} wide-stop or low-reward)")

    # Save
    exp_dip, count_dip = get_recent_expectancy("thai-swing-dip", lookback=15)
    exp_mom, count_mom = get_recent_expectancy("thai-swing-momentum", lookback=15)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"thai_swing_{ts}.md"
    json_path = out / f"thai_swing_{ts}.json"

    # Tag top results with SET50/100/HD membership for downstream UIs
    try:
        memberships = get_set_memberships()
        tag_with_memberships(top_dip, memberships)
        tag_with_memberships(top_mom, memberships)
    except Exception as e:
        print(f"  (SET membership tagging skipped: {e})", file=sys.stderr)

    md_path.write_text(build_report(top_dip, top_mom, ts, len(stocks)), encoding="utf-8")
    result = {
        "generated": ts,
        "universe": len(stocks),
        "dip_buy": [_ser(s) for s in top_dip],
        "momentum": [_ser(s) for s in top_mom],
        "metadata": {
            "market": "TH", 
            "source": "tradingview+yfinance",
            "strategy_expectancy": {
                "thai-swing-dip": {"expectancy_r": exp_dip, "count": count_dip},
                "thai-swing-momentum": {"expectancy_r": exp_mom, "count": count_mom}
            }
        },
    }
    json_path.write_text(json.dumps(clean_for_json(result), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nReports: {md_path}")

    # Console calibration display
    if exp_dip is not None or exp_mom is not None:
        print("\nStrategy Expectancy Calibration:")
        if exp_dip is not None:
            print(f"  Dip Buy (thai-swing-dip): {exp_dip:+.2f}R ({count_dip} closed)")
            if exp_dip < 0:
                print("    ⚠️ WARNING: Negative expectancy. Focus only on high-conviction pullbacks.")
        if exp_mom is not None:
            print(f"  Momentum (thai-swing-momentum): {exp_mom:+.2f}R ({count_mom} closed)")
            if exp_mom < 0:
                print("    ⚠️ WARNING: Negative expectancy. Suggest raising score threshold to 85+.")

    # Console summary
    print(f"\n{'='*70}")
    print("DIP BUY:")
    for i, s in enumerate(top_dip[:5], 1):
        p = s["_plan"]
        print(f"  {i}. {s['symbol']:<12} Score:{s['_score']:>5.1f}  RSI:{s.get('rsi',0):>5.1f}  "
              f"Entry:{p['entry']:.2f}  Stop:{p['stop']:.2f}  Target:{p['target']:.2f}  Risk:{p['risk_pct']:.1f}%")
    print("MOMENTUM:")
    for i, s in enumerate(top_mom[:5], 1):
        p = s["_plan"]
        avg_vol = max(s.get("avgVolume") or 1, 1)
        vol_r = (s.get("volume") or 0) / avg_vol
        print(f"  {i}. {s['symbol']:<12} Score:{s['_score']:>5.1f}  RSI:{s.get('rsi',0):>5.1f}  "
              f"Vol:{vol_r:.1f}x  Entry:{p['entry']:.2f}  Stop:{p['stop']:.2f}  Target:{p['target']:.2f}  Risk:{p['risk_pct']:.1f}%")


def _ser(s: dict) -> dict:
    return {
        "symbol": s["symbol"],
        "name": s.get("name", ""),
        "sector": s.get("sector", ""),
        "strategy": s["_strategy"],
        "score": s["_score"],
        "price": s.get("price"),
        "rsi": s.get("rsi"),
        "rsi_weekly": s.get("rsi_weekly"),
        "sma20": s.get("sma20"),
        "sma50": s.get("sma50"),
        "volume": s.get("volume"),
        "avg_volume": s.get("avgVolume"),
        "plan": s.get("_plan", {}),
        # SET membership tags (added in Phase 3.2)
        "set_membership": s.get("set_membership", []),
        "is_set50": s.get("is_set50", False),
        "is_set100": s.get("is_set100", False),
        "is_sethd": s.get("is_sethd", False),
        # Additional TV metadata for richer UI display
        "market_cap": s.get("marketCap"),
        "dividend_yield": s.get("dividend_yield"),
        "perf_1m": s.get("perf_1m"),
        "perf_3m": s.get("perf_3m"),
    }


if __name__ == "__main__":
    main()
