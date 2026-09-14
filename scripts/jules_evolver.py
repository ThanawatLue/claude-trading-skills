#!/usr/bin/env python3
"""Jules Autonomous Self-Improvement & Trade Evolution Engine.

Analyzes Jules AI Fund closed trades, diagnoses root causes (win/loss/fakeout),
distills actionable lessons into persistent memory (Trader DNA), and provides
personalized pre-trade briefings so Jules becomes progressively smarter with every trade.

Usage:
    python scripts/jules_evolver.py run
    python scripts/jules_evolver.py briefing
    python scripts/jules_evolver.py dna
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

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

from trading_core.clock import isoformat_seconds

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jules_evolver")

DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"
MEMORY_DIR = PROJECT_ROOT / "state" / "jules_memory"
REPORTS_DIR = PROJECT_ROOT / "reports" / "jules_postmortems"
DNA_FILE = MEMORY_DIR / "trader_dna.json"
LEARNINGS_FILE = MEMORY_DIR / "learnings.yaml"


def _ensure_dirs(memory_dir: Path | None = None, reports_dir: Path | None = None):
    m_dir = memory_dir or MEMORY_DIR
    r_dir = reports_dir or REPORTS_DIR
    m_dir.mkdir(parents=True, exist_ok=True)
    r_dir.mkdir(parents=True, exist_ok=True)


def load_dna(memory_dir: Path | None = None) -> dict[str, Any]:
    """Load or initialize Jules Trader DNA."""
    m_dir = memory_dir or MEMORY_DIR
    _ensure_dirs(memory_dir=m_dir)
    dna_path = m_dir / "trader_dna.json"
    if dna_path.exists():
        try:
            with open(dna_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load DNA from %s: %s", dna_path, e)

    return {
        "generation": 1,
        "total_analyzed_trades": 0,
        "last_evolved_at": isoformat_seconds(),
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "rules": [
            "Always verify positive Q2/Q3 net profit growth before entering.",
            "Avoid stocks trading within 5 days of XD dividend record date.",
            "Cut positions early if volume contracts by more than 60% on day 1 post-entry.",
            "Hold winning momentum trades until 2.2R target without premature manual closure.",
        ],
        "sector_experience": {},
        "strengths": ["Discretionary catalyst detection", "Strict 30,000 THB cash management"],
        "weaknesses_to_correct": [],
    }


def save_dna(dna: dict[str, Any], memory_dir: Path | None = None):
    m_dir = memory_dir or MEMORY_DIR
    _ensure_dirs(memory_dir=m_dir)
    dna_path = m_dir / "trader_dna.json"
    with open(dna_path, "w", encoding="utf-8") as f:
        json.dump(dna, f, ensure_ascii=False, indent=2)


def evolve_memory(
    market: str = "TH",
    memory_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Inspect all closed trades and generate learnings, postmortems, and updated DNA."""
    m_dir = memory_dir or MEMORY_DIR
    r_dir = reports_dir or REPORTS_DIR
    _ensure_dirs(m_dir, r_dir)

    dna = load_dna(memory_dir=m_dir)
    closed_trades = paper_trade.list_positions(
        status_filter="closed", market=market, portfolio="jules"
    )
    stats = paper_trade.compute_stats(market=market, portfolio="jules")

    wins = [r for r in closed_trades if (r.get("realized_r") or 0) > 0]
    losses = [r for r in closed_trades if (r.get("realized_r") or 0) < 0]
    total_trades = len(closed_trades)

    new_learnings = []
    weaknesses = list(dna.get("weaknesses_to_correct", []))
    strengths = list(
        dna.get(
            "strengths", ["Discretionary catalyst detection", "Strict 30,000 THB cash management"]
        )
    )
    active_rules = list(dna.get("rules", []))

    # 1. Analyze holding periods (Holding Discipline)
    avg_days_win = (sum(r.get("days_held", 0) for r in wins) / len(wins)) if wins else 0
    avg_days_loss = (sum(r.get("days_held", 0) for r in losses) / len(losses)) if losses else 0

    if avg_days_loss > avg_days_win and avg_days_loss >= 4:
        w_msg = "Holding losing positions too long. Cut stalled trades within 3 days."
        if w_msg not in weaknesses:
            weaknesses.append(w_msg)
        r_rule = "If price stalls without momentum within 3 days, exit to preserve capital."
        if r_rule not in active_rules:
            active_rules.append(r_rule)
        new_learnings.append(
            {
                "topic": "Holding Discipline",
                "rule": r_rule,
                "evidence": f"Avg losing hold ({avg_days_loss:.1f}d) > avg winning hold ({avg_days_win:.1f}d)",
            }
        )

    # 2. Analyze patience (Cutting winners prematurely)
    patience = stats.get("discipline", {}).get("patience_score")
    if patience is not None and patience < 0.6:
        w_msg = "Cutting winning trades too early before reaching full target."
        if w_msg not in weaknesses:
            weaknesses.append(w_msg)
        r_rule = "Trust the 2.2R target. Do not exit manual winners before 1.5R without structural invalidation."
        if r_rule not in active_rules:
            active_rules.append(r_rule)
        new_learnings.append(
            {
                "topic": "Patience Error",
                "rule": r_rule,
                "evidence": f"Patience score is low ({patience:.0%})",
            }
        )
    elif patience is not None and patience >= 0.8:
        s_msg = "High patience on winners (letting profits run to full target)"
        if s_msg not in strengths:
            strengths.append(s_msg)

    # 3. Analyze stop loss respect
    stop_respect = stats.get("discipline", {}).get("stop_respect_rate")
    if stop_respect is not None and stop_respect < 0.8:
        w_msg = "Stop overrides detected. Never widen or remove predefined stops."
        if w_msg not in weaknesses:
            weaknesses.append(w_msg)

    # 4. Analyze round-tripping (Trades reaching >= +1.5R that ended negative)
    round_trip_trades = []
    for t in closed_trades:
        side = t.get("side", "long")
        entry = float(t.get("entry_price") or 0)
        stop = float(t.get("stop_price") or 0)
        risk = abs(entry - stop)
        mfe = float(t.get("mfe") or entry)
        mfe_r = (
            ((mfe - entry) / risk)
            if (risk > 0 and side == "long")
            else (((entry - mfe) / risk) if risk > 0 else 0)
        )
        realized_r = float(t.get("realized_r") or 0)
        if mfe_r >= 1.5 and realized_r <= 0.2:
            round_trip_trades.append(t["symbol"])

    if round_trip_trades:
        r_rule = "Trail stop to breakeven (+0.05R) once price reaches +1.5R to protect gains."
        if r_rule not in active_rules:
            active_rules.append(r_rule)
        new_learnings.append(
            {
                "topic": "Profit Protection",
                "rule": r_rule,
                "evidence": f"{len(round_trip_trades)} trade(s) peaked >= +1.5R but finished near flat or loss ({', '.join(round_trip_trades)})",
            }
        )

    # 5. Generate Individual Trade Postmortems
    for t in closed_trades:
        tid = t["id"]
        sym = t["symbol"]
        pfile = r_dir / f"postmortem_trade_{tid}_{sym}.md"
        if not pfile.exists():
            realized_r = float(t.get("realized_r") or 0)
            realized_pnl = float(t.get("realized_pnl") or 0)
            outcome_str = (
                f"WIN (+{realized_r:.2f}R, ฿{realized_pnl:,.2f})"
                if realized_r > 0
                else f"LOSS ({realized_r:.2f}R, ฿{realized_pnl:,.2f})"
            )
            entry_notes = t.get("notes_entry") or "N/A"
            exit_notes = t.get("journal_text") or t.get("notes") or "N/A"
            md_content = f"""# Trade Postmortem #{tid}: {sym}
- **Date Closed:** {t.get("exit_at") or "N/A"}
- **Outcome:** {outcome_str}
- **Entry Price:** ฿{t["entry_price"]:.2f} | **Exit Price:** ฿{t.get("exit_price", 0):.2f}
- **Shares:** {t.get("shares", 0):,} | **Days Held:** {t.get("days_held", 0)}
- **Exit Status:** {t.get("status")}
- **Initial Thesis at Entry:** {entry_notes}
- **Exit Details & Log:** {exit_notes}

## Root Cause Analysis
1. **Thesis Accuracy:** Did the catalyst occur as expected?
2. **Execution Timing:** Was entry chased or entered near key support?
3. **Discipline Check:** Was the predefined stop respected?
4. **Key Lesson:** What specific filter or condition should Jules apply next time?
"""
            pfile.write_text(md_content, encoding="utf-8")

    # 6. Update DNA & Generation
    prev_analyzed = dna.get("total_analyzed_trades", 0)
    current_gen = dna.get("generation", 1)
    if total_trades > prev_analyzed:
        current_gen += 1

    dna["generation"] = current_gen
    dna["total_analyzed_trades"] = total_trades
    dna["last_evolved_at"] = isoformat_seconds()
    dna["win_rate"] = stats.get("win_rate", 0.0)
    dna["profit_factor"] = stats.get("expectancy_r", 0.0)
    dna["rules"] = active_rules
    dna["strengths"] = list(dict.fromkeys(strengths))
    dna["weaknesses_to_correct"] = list(dict.fromkeys(weaknesses))

    save_dna(dna, memory_dir=m_dir)

    # 7. Save Learnings YAML
    learnings_payload = {
        "updated_at": isoformat_seconds(),
        "generation": dna["generation"],
        "active_rules": dna["rules"],
        "strengths": dna["strengths"],
        "weaknesses_to_correct": dna["weaknesses_to_correct"],
        "recent_learnings": new_learnings,
        "stats_summary": {
            "total_trades": total_trades,
            "win_rate": dna["win_rate"],
            "wins": len(wins),
            "losses": len(losses),
        },
    }
    learnings_path = m_dir / "learnings.yaml"
    with open(learnings_path, "w", encoding="utf-8") as f:
        yaml.dump(learnings_payload, f, allow_unicode=True, sort_keys=False)

    return {
        "status": "evolved",
        "generation": dna["generation"],
        "total_trades": total_trades,
        "learnings_count": len(new_learnings),
        "dna": dna,
    }


def get_pre_trade_briefing(market: str = "TH", memory_dir: Path | None = None) -> str:
    """Generate an actionable context brief for Jules to read before analyzing stocks."""
    dna = load_dna(memory_dir=memory_dir)
    stats = paper_trade.compute_stats(market=market, portfolio="jules")
    open_positions = paper_trade.list_positions(
        status_filter="open", market=market, portfolio="jules"
    )

    rules_text = "\n".join(f"- {r}" for r in dna.get("rules", []))
    weaknesses_text = (
        "\n".join(f"- ⚠️ {w}" for w in dna.get("weaknesses_to_correct", []))
        if dna.get("weaknesses_to_correct")
        else "- No recurring weaknesses identified yet. Maintain current discipline."
    )
    strengths_text = "\n".join(f"- ✅ {s}" for s in dna.get("strengths", []))

    brief = f"""=======================================================
🧠 JULES AI FUND: PRE-TRADE BRAIN BRIEFING (GEN {dna.get("generation", 1)})
=======================================================
[PORTFOLIO STATE]
- Initial Capital: ฿30,000.00
- Active Holdings: {len(open_positions)}/4 slots used
- Win Rate: {(stats.get("win_rate", 0) * 100):.1f}% | Closed Trades: {stats.get("closed_trades", 0)}
- Realized PnL: ฿{(stats.get("total_realized_pnl", 0)):,.2f}

[CORE TRADING DNA & EVOLVED RULES]
{rules_text}

[FOCUS AREAS FOR TODAY'S SELECTION]
{strengths_text}

[MISTAKES TO AVOID BASED ON PAST DATA]
{weaknesses_text}
======================================================="""
    return brief


def main():
    parser = argparse.ArgumentParser(description="Jules Autonomous Self-Improvement Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run")
    sub.add_parser("briefing")
    sub.add_parser("dna")

    args = parser.parse_args()

    if args.cmd == "run":
        out = evolve_memory()
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "briefing":
        print(get_pre_trade_briefing())
    elif args.cmd == "dna":
        print(json.dumps(load_dna(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
