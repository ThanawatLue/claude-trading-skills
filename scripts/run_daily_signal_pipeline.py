"""Daily signal maintenance pipeline.

This orchestrates the evidence loop after market analysis has produced new
theses/signals:

1. optionally trigger the dashboard analysis endpoint
2. ingest thesis files into the signal ledger
3. update forward outcomes from cached price bars
4. run auto-paper in dry-run or execute mode according to config
5. write a compact daily report

The default config is deliberately conservative: analysis is not triggered and
auto-paper runs as a dry-run preview only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import auto_paper, signal_ledger
from scripts.fee_model import effective_transaction_cost_bps

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "state" / "automation_config.yaml"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports" / "daily-signal-pipeline"

DEFAULT_CONFIG: dict[str, Any] = {
    "market": "TH",
    "db_path": str(signal_ledger.DEFAULT_DB_PATH),
    "theses_dir": str(signal_ledger.DEFAULT_THESES_DIR),
    "signal_files": {
        "enabled": True,
        "patterns": [
            "state/signals/*.json",
            "state/signals/*.yaml",
            "reports/vcp_screener_*.json",
            "reports/canslim_screener_*.json",
            "reports/thai_swing_*.json",
        ],
        "max_files_per_pattern": 3,
    },
    "output_dir": str(DEFAULT_REPORT_DIR),
    "horizons": [5, 20, 60],
    "analysis": {
        "enabled": False,
        "url": "http://127.0.0.1:5050/api/run",
        "timeout_seconds": 900,
    },
    "auto_paper": {
        "enabled": True,
        "execute": False,
        "min_score": 70.0,
        "max_age_days": 10,
        "max_new_positions": 2,
        "max_open_positions": 5,
        "high_score_override_min": 85.0,
        "max_open_positions_with_override": 8,
        "shares": 100,
        "derive_missing_risk": True,
        "default_stop_pct": 8.0,
        "target_r": 2.0,
        "fee_model": {
            "broker": "innovestx",
            "commission_pct": 0.15,
            "trading_fee_pct": 0.005,
            "clearing_fee_pct": 0.001,
            "vat_pct": 7.0,
            "slippage_bps": 5.0,
        },
        "account_size": 100_000.0,
        "risk_per_trade_pct": 0.5,
        "max_position_pct": 10.0,
        "max_portfolio_heat_pct": 2.0,
        "board_lot_size": 100,
        "source_rules": {
            "thai-swing-dip": {"target_r": 1.0, "stop_pct_cap": 2.5},
            "thai-swing-momentum": {"target_r": 0.9, "stop_pct_cap": 4.0},
            "vcp-screener": {"target_r": 1.5, "stop_pct_cap": 5.0},
        },
    },
}


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if path:
        config_path = Path(path)
        if config_path.exists():
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"config must be a mapping: {config_path}")
            config = _deep_merge(config, loaded)
    return config


def _as_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _fetch_analysis(config: dict[str, Any]) -> dict[str, Any]:
    analysis = config.get("analysis") or {}
    if not analysis.get("enabled"):
        return {"enabled": False, "ok": True, "status": "skipped"}

    url = str(analysis.get("url") or DEFAULT_CONFIG["analysis"]["url"])
    timeout = int(analysis.get("timeout_seconds") or 900)
    params = urllib.parse.urlencode({"market": config["market"]})
    separator = "&" if "?" in url else "?"
    request_url = f"{url}{separator}{params}"
    with urllib.request.urlopen(request_url, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    payload = json.loads(body) if body else {}
    return {
        "enabled": True,
        "ok": str(payload.get("status", "")).lower() != "failed",
        "status": payload.get("status", "unknown"),
        "run_at": payload.get("run_at"),
    }


def _resolve_signal_files(config: dict[str, Any]) -> list[Path]:
    cfg = config.get("signal_files") or {}
    if not cfg.get("enabled", True):
        return []
    max_files = int(cfg.get("max_files_per_pattern") or 3)
    paths: list[Path] = []
    for pattern in cfg.get("patterns") or []:
        matches = sorted(
            _as_path(pattern).parent.glob(_as_path(pattern).name),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        paths.extend(matches[:max_files])
    return sorted(set(paths))


def _build_auto_config(
    config: dict[str, Any], as_of: date | None = None
) -> auto_paper.AutoPaperConfig:
    paper = config.get("auto_paper") or {}
    dry_run = not (bool(paper.get("enabled", True)) and bool(paper.get("execute", False)))
    fee_model = paper.get("fee_model") or {}
    transaction_cost_bps = (
        effective_transaction_cost_bps(fee_model)
        if fee_model
        else float(paper.get("transaction_cost_bps", 0.0))
    )
    return auto_paper.AutoPaperConfig(
        market=config.get("market"),
        min_score=float(paper.get("min_score", 70.0)),
        max_age_days=int(paper.get("max_age_days", 10)),
        max_new_positions=int(paper.get("max_new_positions", 3)),
        max_open_positions=(
            int(paper["max_open_positions"])
            if paper.get("max_open_positions") is not None
            else None
        ),
        high_score_override_min=(
            float(paper["high_score_override_min"])
            if paper.get("high_score_override_min") is not None
            else None
        ),
        max_open_positions_with_override=(
            int(paper["max_open_positions_with_override"])
            if paper.get("max_open_positions_with_override") is not None
            else None
        ),
        shares=int(paper.get("shares", 100)),
        derive_missing_risk=bool(paper.get("derive_missing_risk", True)),
        default_stop_pct=float(paper.get("default_stop_pct", 8.0)),
        target_r=float(paper.get("target_r", 2.0)),
        transaction_cost_bps=transaction_cost_bps,
        fee_model=fee_model,
        account_size=float(paper["account_size"]) if paper.get("account_size") else None,
        risk_per_trade_pct=(
            float(paper["risk_per_trade_pct"]) if paper.get("risk_per_trade_pct") else None
        ),
        max_position_pct=float(paper["max_position_pct"])
        if paper.get("max_position_pct")
        else None,
        max_portfolio_heat_pct=(
            float(paper["max_portfolio_heat_pct"]) if paper.get("max_portfolio_heat_pct") else None
        ),
        board_lot_size=int(paper.get("board_lot_size", 100)),
        source_rules=paper.get("source_rules") or {},
        as_of=as_of,
        dry_run=dry_run,
    )


def _report_paths(output_dir: Path, run_date: date) -> tuple[Path, Path]:
    stem = f"daily_signal_pipeline_{run_date.isoformat()}"
    return output_dir / f"{stem}.json", output_dir / f"{stem}.md"


def write_reports(result: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    out_dir = _as_path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = date.fromisoformat(result["run_date"])
    json_path, md_path = _report_paths(out_dir, run_date)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Daily Signal Pipeline",
        "",
        f"- Run date: {result['run_date']}",
        f"- Market: {result['market']}",
        f"- Analysis: {result['analysis']['status']}",
        f"- Ingested theses: {result['ingest']['theses']['inserted']} inserted, {result['ingest']['theses']['updated']} updated, {result['ingest']['theses']['skipped']} skipped",
        f"- Ingested signal files: {result['ingest']['signals']['files']} files, {result['ingest']['signals']['inserted']} inserted, {result['ingest']['signals']['updated']} updated",
        f"- Outcomes updated: {result['outcomes']['outcomes_updated']} rows, {result['outcomes']['complete_outcomes']} complete",
        f"- Auto-paper: {result['auto_paper']['eligible']} eligible, {result['auto_paper']['opened']} opened, dry_run={result['auto_paper']['dry_run']}",
        f"- Ledger signals: {result['signals']['total']}",
        f"- Completed signals: {result['signals']['completed_signals']}",
        "",
        "## Notes",
        "",
        "- Auto-paper opens simulated positions only.",
        "- Real-money execution is intentionally outside this pipeline.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def run_pipeline(
    config: dict[str, Any],
    *,
    analysis_runner: Callable[[dict[str, Any]], dict[str, Any]] = _fetch_analysis,
    open_fn: Callable[..., dict[str, Any]] | None = None,
    as_of: date | None = None,
    write_output: bool = True,
) -> dict[str, Any]:
    market = str(config.get("market") or "TH").upper()
    config = _deep_merge(config, {"market": market})
    run_date = as_of or date.today()

    try:
        analysis_result = analysis_runner(config)
    except Exception as exc:
        analysis_result = {"enabled": True, "ok": False, "status": "failed", "error": str(exc)}

    horizons = tuple(int(x) for x in config.get("horizons", DEFAULT_CONFIG["horizons"]))
    db_path = _as_path(config.get("db_path", signal_ledger.DEFAULT_DB_PATH))
    theses_dir = _as_path(config.get("theses_dir", signal_ledger.DEFAULT_THESES_DIR))

    with signal_ledger.connect(db_path) as conn:
        thesis_ingest = signal_ledger.ingest_theses(conn, theses_dir)
        signal_ingest = signal_ledger.ingest_signal_files(conn, _resolve_signal_files(config))
        ingest_result = {"theses": thesis_ingest, "signals": signal_ingest}
        outcome_result = signal_ledger.update_outcomes(conn, horizons=horizons, market=market)
        auto_config = _build_auto_config(config, as_of=run_date)
        if open_fn is None:
            auto_result = auto_paper.run_auto_paper(conn, auto_config)
        else:
            auto_result = auto_paper.run_auto_paper(conn, auto_config, open_fn=open_fn)
        signal_counts = signal_ledger.get_signal_counts(conn, market=market)
        outcome_summary = signal_ledger.outcome_summary(conn, market=market)

    result = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_date": run_date.isoformat(),
        "market": market,
        "analysis": analysis_result,
        "ingest": ingest_result,
        "outcomes": outcome_result,
        "auto_paper": auto_result,
        "signals": signal_counts,
        "outcome_summary": outcome_summary,
    }
    if write_output:
        result["reports"] = write_reports(result, config.get("output_dir", DEFAULT_REPORT_DIR))
    return result


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run daily signal maintenance pipeline")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--market", choices=["US", "TH"])
    parser.add_argument("--db-path")
    parser.add_argument("--theses-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--as-of")
    parser.add_argument("--run-analysis", action="store_true")
    parser.add_argument("--no-run-analysis", action="store_true")
    parser.add_argument("--execute-auto-paper", action="store_true")
    parser.add_argument("--no-auto-paper", action="store_true")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.market:
        config["market"] = args.market
    if args.db_path:
        config["db_path"] = args.db_path
    if args.theses_dir:
        config["theses_dir"] = args.theses_dir
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.run_analysis:
        config.setdefault("analysis", {})["enabled"] = True
    if args.no_run_analysis:
        config.setdefault("analysis", {})["enabled"] = False
    if args.execute_auto_paper:
        config.setdefault("auto_paper", {})["enabled"] = True
        config.setdefault("auto_paper", {})["execute"] = True
    if args.no_auto_paper:
        config.setdefault("auto_paper", {})["enabled"] = False
        config.setdefault("auto_paper", {})["execute"] = False

    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    result = run_pipeline(config, as_of=as_of)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["analysis"].get("ok", False) else 2


if __name__ == "__main__":
    raise SystemExit(run_cli())
