#!/usr/bin/env python3
"""Update mark-to-market prices for all open paper positions.

For each open position:
1. Fetch latest price from yfinance
2. Update last_price, last_updated, unrealized_pnl, unrealized_r
3. Track MAE (worst price) and MFE (best price) since entry
4. If price crossed stop → auto-close with status=closed_stop
5. If price crossed target → auto-close with status=closed_target
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paper_trade import (  # noqa: E402
    STATUS_CLOSED_INVALIDATED,
    STATUS_CLOSED_STOP,
    STATUS_CLOSED_TARGET,
    STATUS_CLOSED_TIME,
    STATUS_OPEN,
    _db,
    _now_iso,
    close_position,
    record_mark,
)

# Backward-compatible patch target for older tests and callers. The active DB
# connection still comes from paper_trade._db(), which reads paper_trade.DB_PATH.
DB_PATH = None
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUTOMATION_CONFIG = PROJECT_ROOT / "state" / "automation_config.yaml"
INVALIDATING_STATES = frozenset({"Damaged", "Invalid", "Overextended"})
SETUP_AWARE_SOURCES = frozenset(
    {"vcp-screener", "vcp", "thai-swing-dip", "thai-swing-momentum", "thai-swing"}
)
DEFAULT_SOURCE_RULES = {
    "thai-swing-dip": {
        "take_profit_r": 1.0,
        # Longer hold; only time-stop when clearly underwater (not near flat).
        "max_hold_days": 4,
        "time_stop_min_r": -0.3,
        "trail_after_r": 1.0,
        "trail_stop_r": 0.0,
    },
    "thai-swing-momentum": {
        "take_profit_r": 1.0,
        "max_hold_days": 3,
        "time_stop_min_r": 0.0,
        "trail_after_r": 1.0,
        "trail_stop_r": 0.0,
    },
    "vcp-screener": {
        "take_profit_r": 1.5,
        "max_hold_days": 7,
        "time_stop_min_r": 0.5,
        "trail_after_r": 1.0,
        "trail_stop_r": 0.0,
    },
    "vcp": {
        "take_profit_r": 1.5,
        "max_hold_days": 7,
        "time_stop_min_r": 0.5,
        "trail_after_r": 1.0,
        "trail_stop_r": 0.0,
    },
}


def _load_exit_rules() -> dict[str, dict[str, float]]:
    rules = {k: dict(v) for k, v in DEFAULT_SOURCE_RULES.items()}
    if not AUTOMATION_CONFIG.exists():
        return rules
    try:
        import yaml

        config = yaml.safe_load(AUTOMATION_CONFIG.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"  warning: could not load exit rules: {e}", file=sys.stderr)
        return rules

    auto_paper = config.get("auto_paper") or {}
    for source, values in (auto_paper.get("source_rules") or {}).items():
        if isinstance(values, dict):
            rules.setdefault(source, {}).update(values)
    for source, values in (config.get("paper_exit_rules") or {}).items():
        if isinstance(values, dict):
            rules.setdefault(source, {}).update(values)
    return rules


def _rule_for_source(source: str | None, rules: dict[str, dict[str, float]]) -> dict[str, float]:
    key = (source or "").strip().lower()
    return rules.get(key, {})


def _execution_state_for_open(conn: sqlite3.Connection, trade_id: int) -> str | None:
    """Read latest linked signal payload execution_state when available."""
    try:
        row = conn.execute(
            """SELECT s.payload_json
               FROM signal_paper_link l
               JOIN signal_ledger s ON s.signal_id = l.signal_id
               WHERE l.paper_trade_id = ?""",
            (trade_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row or not row[0]:
        return None
    try:
        payload = json.loads(row[0])
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    state = payload.get("execution_state") or payload.get("consolidation_state")
    if state:
        return str(state)
    raw = payload.get("raw_provenance")
    if isinstance(raw, dict):
        nested = raw.get("execution_state") or raw.get("consolidation_state")
        if nested:
            return str(nested)
    return None


def _maybe_invalidate_setup(row: sqlite3.Row, price: float) -> dict | None:
    source = (row["source"] or "").strip().lower()
    if source not in SETUP_AWARE_SOURCES:
        return None
    with _db() as conn:
        state = _execution_state_for_open(conn, int(row["id"]))
    if not state or state not in INVALIDATING_STATES:
        return None
    close_position(
        row["id"],
        price,
        status=STATUS_CLOSED_INVALIDATED,
        notes=f"Auto-closed: setup invalidated ({state})",
    )
    return {
        "id": row["id"],
        "symbol": row["symbol"],
        "action": "auto_closed_invalidated",
        "exit_price": price,
        "state": state,
    }


def _fetch_price(symbol: str) -> float | None:
    """Get latest close price via yfinance. Returns None on failure."""
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        h = t.history(period="2d")
        if h.empty:
            return None
        return float(h["Close"].iloc[-1])
    except Exception as e:
        print(f"  fetch error for {symbol}: {e}", file=sys.stderr)
        return None


def update_one(
    row: sqlite3.Row,
    price: float,
    source_rules: dict[str, dict[str, float]] | None = None,
) -> dict:
    """Update marks for one open position; auto-close if stop/target crossed."""
    source_rules = source_rules or DEFAULT_SOURCE_RULES
    invalidated = _maybe_invalidate_setup(row, price)
    if invalidated is not None:
        return invalidated

    observed_at = _now_iso()
    record_mark(row["id"], price, observed_at)
    side = row["side"]
    entry = row["entry_price"]
    shares = row["shares"]
    risk_per_share = (entry - row["stop_price"]) if side == "long" else (row["stop_price"] - entry)

    if side == "long":
        pnl = (price - entry) * shares
    else:
        pnl = (entry - price) * shares

    r_mult = pnl / (risk_per_share * shares) if risk_per_share > 0 else 0
    new_mae = min(row["mae"] or price, price) if side == "long" else max(row["mae"] or price, price)
    new_mfe = max(row["mfe"] or price, price) if side == "long" else min(row["mfe"] or price, price)
    days = (
        datetime.fromisoformat(_now_iso()).replace(tzinfo=None)
        - datetime.fromisoformat(row["entry_at"]).replace(tzinfo=None)
    ).days
    rule = _rule_for_source(row["source"], source_rules)
    take_profit_r = rule.get("take_profit_r")
    max_hold_days = rule.get("max_hold_days")
    time_stop_min_r = float(rule.get("time_stop_min_r", 0.0))
    trail_after_r = rule.get("trail_after_r")
    trail_stop_r = rule.get("trail_stop_r")

    # After +N R, ratchet stop to entry + trail_stop_r * risk (default: breakeven).
    stop_price = float(row["stop_price"])
    if trail_after_r is not None and risk_per_share > 0 and r_mult >= float(trail_after_r):
        trail_level = float(trail_stop_r if trail_stop_r is not None else 0.0)
        if side == "long":
            new_stop = entry + (risk_per_share * trail_level)
            if new_stop > stop_price:
                stop_price = new_stop
                with _db() as conn:
                    conn.execute(
                        "UPDATE paper_trade SET stop_price=? WHERE id=?",
                        (round(stop_price, 4), row["id"]),
                    )
        else:
            new_stop = entry - (risk_per_share * trail_level)
            if new_stop < stop_price:
                stop_price = new_stop
                with _db() as conn:
                    conn.execute(
                        "UPDATE paper_trade SET stop_price=? WHERE id=?",
                        (round(stop_price, 4), row["id"]),
                    )

    short_target_price = None
    hit_short_target = False
    if take_profit_r is not None and risk_per_share > 0:
        if side == "long":
            short_target_price = entry + (risk_per_share * float(take_profit_r))
            hit_short_target = price >= short_target_price
        else:
            short_target_price = entry - (risk_per_share * float(take_profit_r))
            hit_short_target = price <= short_target_price
    hit_time_stop = (
        max_hold_days is not None and days >= int(max_hold_days) and r_mult < time_stop_min_r
    )

    # Auto-close cases (priority: stop > target because stop fires first if both crossed)
    if side == "long":
        hit_stop = price <= stop_price
        hit_target = price >= row["target_price"]
    else:
        hit_stop = price >= stop_price
        hit_target = price <= row["target_price"]

    if hit_stop:
        # Close at stop price (assume execution at stop)
        close_position(
            row["id"],
            stop_price,
            status=STATUS_CLOSED_STOP,
            notes=f"Auto-closed: price {price:.2f} crossed stop {stop_price:.2f}",
        )
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "action": "auto_closed_stop",
            "exit_price": stop_price,
        }
    if hit_target:
        close_position(
            row["id"],
            row["target_price"],
            status=STATUS_CLOSED_TARGET,
            notes=f"Auto-closed: price {price:.2f} hit target {row['target_price']:.2f}",
        )
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "action": "auto_closed_target",
            "exit_price": row["target_price"],
        }
    if hit_short_target and short_target_price is not None:
        close_position(
            row["id"],
            short_target_price,
            status=STATUS_CLOSED_TARGET,
            notes=(
                f"Auto-closed: short profit target {take_profit_r:g}R reached at price {price:.2f}"
            ),
        )
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "action": "auto_closed_short_target",
            "exit_price": round(short_target_price, 4),
            "r": float(take_profit_r),
        }
    if hit_time_stop:
        close_position(
            row["id"],
            price,
            status=STATUS_CLOSED_TIME,
            notes=(
                f"Auto-closed: time stop after {days}d; "
                f"current R {r_mult:.2f} < required {time_stop_min_r:.2f}R"
            ),
        )
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "action": "auto_closed_time",
            "exit_price": price,
            "r": round(r_mult, 2),
            "days": days,
        }

    # Otherwise just update marks
    with _db() as conn:
        conn.execute(
            """UPDATE paper_trade
               SET last_price=?, last_updated=?, unrealized_pnl=?, unrealized_r=?,
                   mae=?, mfe=?, days_held=?
               WHERE id=?""",
            (price, _now_iso(), pnl, r_mult, new_mae, new_mfe, days, row["id"]),
        )
    return {
        "id": row["id"],
        "symbol": row["symbol"],
        "action": "marked",
        "price": price,
        "pnl": round(pnl, 2),
        "r": round(r_mult, 2),
    }


def update_all() -> list[dict]:
    with _db() as conn:
        opens = conn.execute("SELECT * FROM paper_trade WHERE status=?", (STATUS_OPEN,)).fetchall()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(timespec="seconds")
        recent_closed = conn.execute(
            "SELECT * FROM paper_trade WHERE status != ? AND exit_at >= ?",
            (STATUS_OPEN, cutoff),
        ).fetchall()
    tracked = list(opens) + list(recent_closed)
    if not tracked:
        return []

    # Group by symbol to dedupe fetches
    unique_symbols = sorted({r["symbol"] for r in tracked})
    prices: dict[str, float | None] = {}
    for sym in unique_symbols:
        prices[sym] = _fetch_price(sym)

    # TradingView fallback for Thai stocks (.BK)
    thai_failures = [
        sym for sym in unique_symbols if sym.upper().endswith(".BK") and prices[sym] is None
    ]
    if thai_failures:
        print(f"Attempting TradingView fallback for Thai stocks: {thai_failures}", file=sys.stderr)
        try:
            tv_path = Path(__file__).resolve().parents[3] / "skills" / "vcp-screener" / "scripts"
            # Temporarily add vcp-screener to sys.path for tv_client import
            sys.path.insert(0, str(tv_path))
            import tv_client

            if tv_client.is_available():
                stocks = tv_client.get_thai_stocks()
                tv_prices = {
                    s["symbol"].upper(): s["price"]
                    for s in stocks
                    if "symbol" in s and "price" in s
                }
                for sym in thai_failures:
                    prices[sym] = tv_prices.get(sym.upper())
                    if prices[sym] is not None:
                        print(
                            f"  Successfully fetched TV fallback price for {sym}: {prices[sym]}",
                            file=sys.stderr,
                        )
            else:
                print(
                    "  TradingView screener is not available (is_available() returned False)",
                    file=sys.stderr,
                )
        except ImportError:
            logging.warning(
                "tv_client not found. TradingView fallback for Thai stocks is disabled. "
                "Ensure 'vcp-screener' skill is correctly installed if you need this functionality."
            )
        except Exception as e:
            print(f"  TradingView fallback failed: {e}", file=sys.stderr)
        finally:
            # Remove vcp-screener from sys.path
            if str(tv_path) in sys.path:
                sys.path.remove(str(tv_path))

    source_rules = _load_exit_rules()
    results = []
    close_action_status = {
        "auto_closed_stop": STATUS_CLOSED_STOP,
        "auto_closed_target": STATUS_CLOSED_TARGET,
        "auto_closed_short_target": STATUS_CLOSED_TARGET,
        "auto_closed_time": STATUS_CLOSED_TIME,
        "auto_closed_invalidated": STATUS_CLOSED_INVALIDATED,
    }
    for row in opens:
        price = prices.get(row["symbol"])
        if price is None:
            results.append({"id": row["id"], "symbol": row["symbol"], "action": "fetch_failed"})
            continue
        result = update_one(row, price, source_rules)
        status = close_action_status.get(result.get("action") or "")
        if status and result.get("exit_price") is not None:
            try:
                sys.path.insert(0, str(PROJECT_ROOT))
                from scripts import paper_memory_bridge

                with _db() as conn:
                    memory = paper_memory_bridge.sync_close(
                        conn,
                        paper_trade_id=int(row["id"]),
                        exit_price=float(result["exit_price"]),
                        exit_date=_now_iso()[:10],
                        paper_status=status,
                    )
                result["memory"] = memory
            except Exception as exc:  # pragma: no cover - never block marks
                result["memory"] = {
                    "ok": False,
                    "skipped": True,
                    "reason": f"bridge_error:{exc}",
                }
        results.append(result)

    # Keep collecting post-exit observations for the +1/+3/+5 session
    # fingerprint analysis. This never changes a closed trade.
    for row in recent_closed:
        price = prices.get(row["symbol"])
        if price is None:
            continue
        record_mark(row["id"], price)
        results.append(
            {"id": row["id"], "symbol": row["symbol"], "action": "forward_marked", "price": price}
        )
    return results


def main():
    print(f"Updating marks at {_now_iso()}...")
    out = update_all()
    print(json.dumps(out, indent=2))
    # Summary
    counts = {}
    for r in out:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    print(f"\nSummary: {counts}")


if __name__ == "__main__":
    main()
