#!/usr/bin/env python3
"""Adaptive Matrix and Specialized Dynamic Indicators for Jules AI Fund.

Solves the limitations of generic single-stock oscillators (RSI/SMA) by providing:
1. Recency-Weighted Up/Down Volume Ratio (U/D Ratio) with exponential weighting
2. Dynamic Volatility-Scaled Risk Cap (ATR-based envelope instead of static 6.0%)
3. Mansfield Relative Strength vs Benchmark (MSCI Thailand / SET)
4. Granular Thematic Sub-Cluster Mapping and Cluster Breadth Detection
5. Adaptive Candidate Quality Scoring & Systematic Trap Elimination
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("adaptive_indicators")

# ---------------------------------------------------------------------------
# Thematic Sub-Clusters for Thai SET Market
# ---------------------------------------------------------------------------
THEMATIC_CLUSTERS: dict[str, set[str]] = {
    "Marine Shipping": {"PSL.BK", "RCL.BK", "TTA.BK"},
    "Healthcare & Hospitals": {"BDMS.BK", "BH.BK", "BCH.BK", "CHG.BK", "VIH.BK", "PR9.BK"},
    "Power & Renewables": {"GULF.BK", "GPSC.BK", "BGRIM.BK", "SSP.BK", "BCPG.BK", "EA.BK"},
    "Consumer Finance & Leasing": {"MTC.BK", "SAWAD.BK", "TIDLOR.BK", "SCAP.BK", "THANI.BK", "SGC.BK"},
    "Data Center & ICT Infra": {"INSET.BK", "SKY.BK", "DELTA.BK", "CCET.BK", "TRUE.BK", "ADVANC.BK"},
    "Commerce & Retail": {"CPALL.BK", "CRC.BK", "CPAXT.BK", "BJC.BK", "COM7.BK"},
    "Industrial Estates & Logistics": {"WHA.BK", "AMATA.BK", "ROJNA.BK", "WHAIR.BK"},
    "Food & Pet Food Export": {"ITC.BK", "AAI.BK", "CPF.BK", "TU.BK", "GFPT.BK"},
    "Commercial Banks": {"KBANK.BK", "SCB.BK", "BBL.BK", "KTB.BK", "TTB.BK"},
    "Oil & Refinery": {"PTTEP.BK", "TOP.BK", "SPRC.BK", "BCP.BK", "IRPC.BK"},
    "Building Materials & Construction": {"SCC.BK", "SCCC.BK", "DCC.BK", "TASCO.BK"},
}


def get_cluster_for_symbol(symbol: str) -> str | None:
    """Find the thematic cluster for a given symbol."""
    sym_clean = symbol.upper()
    if not sym_clean.endswith(".BK"):
        sym_clean += ".BK"
    for cluster_name, tickers in THEMATIC_CLUSTERS.items():
        if sym_clean in tickers:
            return cluster_name
    return None


def detect_thematic_clusters(
    stocks: list[dict[str, Any]],
    min_cluster_gainers: int = 2,
    min_gain_pct: float = 1.5,
) -> dict[str, Any]:
    """Detect clusters that have concurrent price and volume expansion.

    A cluster is active if at least `min_cluster_gainers` stocks have:
    - Daily Price Change >= `min_gain_pct`
    """
    cluster_stats: dict[str, list[dict[str, Any]]] = {}
    for s in stocks:
        sym = s.get("symbol", "").upper()
        if not sym.endswith(".BK"):
            sym += ".BK"
        cluster = get_cluster_for_symbol(sym)
        if not cluster:
            continue
        cluster_stats.setdefault(cluster, []).append(s)

    active_clusters: dict[str, dict[str, Any]] = {}
    symbol_to_cluster: dict[str, str] = {}

    for cluster_name, members in cluster_stats.items():
        gainers = [
            m for m in members if float(m.get("change") or m.get("chg_today") or 0.0) >= min_gain_pct
        ]
        if len(gainers) >= min_cluster_gainers:
            avg_gain = sum(float(m.get("change") or m.get("chg_today") or 0.0) for m in gainers) / len(
                gainers
            )
            active_clusters[cluster_name] = {
                "active": True,
                "gainer_count": len(gainers),
                "total_members_seen": len(members),
                "avg_gain": round(avg_gain, 2),
                "gainers": [g.get("symbol") for g in gainers],
            }
            for g in gainers:
                sym_clean = g.get("symbol", "").upper()
                symbol_to_cluster[sym_clean] = cluster_name

    return {
        "active_clusters": active_clusters,
        "symbol_cluster_map": symbol_to_cluster,
    }


# ---------------------------------------------------------------------------
# Recency-Weighted Up/Down Volume Ratio
# ---------------------------------------------------------------------------
def calculate_recency_weighted_ud_ratio(
    stock_df: pd.DataFrame,
    lookback: int = 20,
    recent_days: int = 5,
    recent_weight: float = 0.6,
) -> dict[str, Any]:
    """Calculate Up/Down Volume Ratio with recency weighting.

    Balances early catalyst detection while filtering sustained institutional distribution.
    Weight allocation:
    - Recent 5 days: 60%
    - Prior 15 days: 40%
    """
    if stock_df.empty or len(stock_df) < lookback:
        return {
            "ud_ratio": 1.0,
            "status": "NEUTRAL",
            "is_accumulation": True,
            "raw_recent_ratio": 1.0,
            "raw_prior_ratio": 1.0,
        }

    df = stock_df.iloc[-lookback:].copy()
    df["chg"] = df["Close"].diff()

    # Split into prior (15 days) and recent (5 days)
    prior_df = df.iloc[:-recent_days]
    recent_df = df.iloc[-recent_days:]

    recent_up = float(recent_df.loc[recent_df["chg"] > 0, "Volume"].sum())
    recent_down = float(recent_df.loc[recent_df["chg"] < 0, "Volume"].sum())

    prior_up = float(prior_df.loc[prior_df["chg"] > 0, "Volume"].sum())
    prior_down = float(prior_df.loc[prior_df["chg"] < 0, "Volume"].sum())

    raw_recent = (recent_up / recent_down) if recent_down > 0 else (9.99 if recent_up > 0 else 1.0)
    raw_prior = (prior_up / prior_down) if prior_down > 0 else (9.99 if prior_up > 0 else 1.0)

    prior_weight = 1.0 - recent_weight
    weighted_up = (recent_up * recent_weight) + (prior_up * prior_weight)
    weighted_down = (recent_down * recent_weight) + (prior_down * prior_weight)

    if weighted_down <= 0:
        final_ratio = 9.99 if weighted_up > 0 else 1.0
    else:
        final_ratio = round(weighted_up / weighted_down, 2)

    if final_ratio >= 1.25:
        status = "ACCUMULATION"
    elif final_ratio < 0.8:
        status = "DISTRIBUTION"
    else:
        status = "NEUTRAL"

    return {
        "ud_ratio": final_ratio,
        "status": status,
        "is_accumulation": final_ratio >= 1.0,
        "raw_recent_ratio": round(raw_recent, 2),
        "raw_prior_ratio": round(raw_prior, 2),
    }


# ---------------------------------------------------------------------------
# Dynamic Volatility-Scaled Risk Cap
# ---------------------------------------------------------------------------
def calculate_dynamic_risk_cap(
    price: float,
    atr: float,
    default_cap: float = 6.0,
    min_cap: float = 3.5,
    max_cap: float = 8.5,
    atr_multiplier: float = 1.8,
) -> float:
    """Calculate an ATR-scaled risk cap instead of a rigid percentage.

    Allows volatile leaders (like shipping with ATR ~4-5%) to set realistic stops
    without rejecting them arbitrarily at 6.0%, while keeping low-beta stocks tight.
    """
    if price <= 0 or atr <= 0:
        return default_cap

    vol_cap = (atr / price) * 100.0 * atr_multiplier
    return round(float(np.clip(vol_cap, min_cap, max_cap)), 2)


# ---------------------------------------------------------------------------
# Mansfield Relative Strength vs Benchmark
# ---------------------------------------------------------------------------
def calculate_mansfield_rs(
    stock_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    ma_len: int = 50,
) -> dict[str, Any]:
    """Calculate Mansfield Relative Strength against benchmark.

    RS(t) = Stock(t) / Benchmark(t)
    Base_RS = SMA(RS, ma_len)
    Mansfield_RS = ((RS / Base_RS) - 1) * 100
    """
    if stock_df.empty or bench_df.empty:
        return {
            "rs_score": 0.0,
            "rs_trend": "UNKNOWN",
            "is_outperforming": False,
            "rs_near_high": False,
        }

    s_close = stock_df["Close"].copy()
    s_close.index = pd.to_datetime(s_close.index).strftime("%Y-%m-%d")
    b_close = bench_df["Close"].copy()
    b_close.index = pd.to_datetime(b_close.index).strftime("%Y-%m-%d")

    df = pd.DataFrame({"stock": s_close, "bench": b_close}).dropna()
    if df.empty or len(df) < 5:
        return {
            "rs_score": 0.0,
            "rs_trend": "UNKNOWN",
            "is_outperforming": False,
            "rs_near_high": False,
        }

    if len(df) < ma_len:
        ma_len = max(5, len(df) // 2)

    rs = df["stock"] / df["bench"]
    base_rs = rs.rolling(window=ma_len).mean()
    mansfield_rs = ((rs / base_rs) - 1) * 100

    latest_rs = float(mansfield_rs.iloc[-1])
    prev_rs = float(mansfield_rs.iloc[-2]) if len(mansfield_rs) > 1 else latest_rs
    trend = "RISING" if latest_rs > prev_rs else "FALLING"

    recent_high_rs = float(rs.iloc[-20:].max()) if len(rs) >= 20 else float(rs.max())
    is_near_high = float(rs.iloc[-1]) >= recent_high_rs * 0.98

    return {
        "rs_score": round(latest_rs, 2),
        "rs_trend": trend,
        "is_outperforming": latest_rs > 0.0,
        "rs_near_high": is_near_high,
    }


# ---------------------------------------------------------------------------
# Adaptive Candidate Quality Evaluation & Trap Elimination
# ---------------------------------------------------------------------------
def evaluate_adaptive_candidate(
    symbol: str,
    price: float,
    traded_value_thb: float,
    high_52w: float,
    stock_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    active_clusters: dict[str, Any] | None = None,
    atr: float | None = None,
    base_score: float = 60.0,
) -> dict[str, Any]:
    """Comprehensive evaluation applying the 4-layer adaptive matrix.

    Returns:
    - adaptive_score (0-100+)
    - eligible (True/False)
    - rejection_reasons (list of strings if rejected)
    - detailed metrics (ud, rs, cluster, dynamic_risk_cap)
    """
    rejections: list[str] = []
    bonus = 0.0

    # 1. Liquidity Trap Gate (ADTV >= 15M THB)
    if traded_value_thb < 15_000_000:
        rejections.append(f"Low Liquidity: ฿{traded_value_thb/1e6:.1f}M < ฿15.0M threshold")

    # 2. 52-Week High Proximity (Reject deep bottom bounces / dead cats)
    if high_52w > 0:
        dist_52w = ((high_52w - price) / high_52w) * 100.0
        if dist_52w > 15.0:
            rejections.append(f"Laggard / Rebound: {dist_52w:.1f}% below 52w high (max 15%)")
    else:
        dist_52w = 0.0

    # 3. Recency-Weighted Up/Down Volume Ratio
    ud = calculate_recency_weighted_ud_ratio(stock_df)
    if ud["ud_ratio"] < 0.85:
        rejections.append(f"Distribution Trap: U/D ratio {ud['ud_ratio']:.2f} < 0.85")
    elif ud["is_accumulation"]:
        bonus += 10.0

    # 4. Mansfield Relative Strength vs Benchmark
    rs = calculate_mansfield_rs(stock_df, benchmark_df)
    if rs["is_outperforming"]:
        bonus += 10.0
        if rs["rs_trend"] == "RISING":
            bonus += 5.0
    elif rs["rs_score"] < -10.0:
        rejections.append(f"Severe Relative Laggard: RS score {rs['rs_score']:.1f}%")

    # 5. Thematic Cluster Momentum
    cluster_name = get_cluster_for_symbol(symbol)
    in_active_cluster = False
    if active_clusters and cluster_name:
        act_map = active_clusters.get("active_clusters", {})
        if cluster_name in act_map:
            in_active_cluster = True
            bonus += 15.0  # Cluster momentum bonus!

    # 6. Dynamic Volatility Risk Cap
    if atr is not None and atr > 0:
        dynamic_cap = calculate_dynamic_risk_cap(price, atr)
    else:
        dynamic_cap = 6.0

    final_score = round(base_score + bonus, 1)
    eligible = len(rejections) == 0

    return {
        "symbol": symbol,
        "eligible": eligible,
        "adaptive_score": final_score,
        "rejection_reasons": rejections,
        "cluster": cluster_name,
        "in_active_cluster": in_active_cluster,
        "ud_ratio": ud["ud_ratio"],
        "ud_status": ud["status"],
        "mansfield_rs": rs["rs_score"],
        "rs_trend": rs["rs_trend"],
        "dynamic_risk_cap": dynamic_cap,
    }
