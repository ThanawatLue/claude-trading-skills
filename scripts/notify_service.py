"""Real-time Multi-Channel Trading Alert & Notification Service.

Supports:
- Telegram Bot (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
- Discord Webhook (DISCORD_WEBHOOK_URL)
- LINE Notify / Webhook (LINE_NOTIFY_TOKEN or LINE_WEBHOOK_URL)

All dispatches are non-blocking, fail-safe, and gracefully silent when no credentials
are configured or during test runs.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger("notify_service")


def format_currency(amount: float, market: str = "TH") -> str:
    """Format currency symbol and comma separators according to market."""
    sym = "$" if market.upper() == "US" else "฿"
    return f"{sym}{amount:,.2f}"


def send_telegram(text: str) -> bool:
    """Send text alert to Telegram channel or chat."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        logger.warning("Failed to dispatch Telegram alert: %s", e)
        return False


def send_discord(text: str, title: str | None = None) -> bool:
    """Send alert embed to Discord webhook."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return False

    payload = {
        "embeds": [
            {
                "title": title or "Jules AI Fund Notification",
                "description": text,
                "color": 0x9C27B0,  # Purple brand theme
            }
        ]
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=5)
        return resp.status_code in (200, 204)
    except Exception as e:
        logger.warning("Failed to dispatch Discord alert: %s", e)
        return False


def send_line(text: str) -> bool:
    """Send alert to LINE Notify service or custom webhook."""
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    webhook_url = os.environ.get("LINE_WEBHOOK_URL")

    if token:
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {token}"}
        data = {"message": f"\n{text}"}
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning("Failed to dispatch LINE Notify alert: %s", e)
            return False

    if webhook_url:
        try:
            resp = requests.post(webhook_url, json={"message": text}, timeout=5)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.warning("Failed to dispatch LINE webhook alert: %s", e)
            return False

    return False


def dispatch_alert(message: str, title: str = "JULES AI ALERT") -> dict[str, bool]:
    """Fan-out notification message to all configured communication channels."""
    results = {
        "telegram": send_telegram(f"<b>{title}</b>\n\n{message}"),
        "discord": send_discord(message, title=title),
        "line": send_line(f"[{title}]\n{message}"),
    }
    return results


def notify_order_staged(order: dict[str, Any]) -> dict[str, bool]:
    """Alert when an autonomous order is staged for market open."""
    sym = order.get("symbol", "N/A")
    market = order.get("market", "TH")
    shares = order.get("shares", 0)
    entry = float(order.get("entry_price") or 0.0)
    stop = float(order.get("stop_price") or 0.0)
    target = float(order.get("target_price") or 0.0)
    t1 = float(order.get("t1_price") or 0.0)
    t2 = float(order.get("t2_price") or 0.0)
    thesis = order.get("thesis", "High conviction setup")

    title = f"🎯 ORDER STAGED: {sym} [{market}]"
    lines = [
        f"<b>Symbol:</b> {sym}",
        f"<b>Action:</b> BUY {shares:,} shares",
        f"<b>Entry Trigger:</b> {format_currency(entry, market)}",
        f"<b>Stop Loss:</b> {format_currency(stop, market)} (Risk: {format_currency(entry - stop, market)})",
        f"<b>Scale-Out (T1, 1.5R):</b> {format_currency(t1, market)}",
        f"<b>Target (T2, 2.5R):</b> {format_currency(t2 or target, market)}",
        f"<b>Thesis:</b> {thesis}",
    ]
    return dispatch_alert("\n".join(lines), title=title)


def notify_order_executed(order: dict[str, Any], fill_result: dict[str, Any]) -> dict[str, bool]:
    """Alert when an autonomous order is successfully filled."""
    sym = order.get("symbol", "N/A")
    market = order.get("market", "TH")
    shares = order.get("shares", 0)
    fill_price = float(fill_result.get("entry_price") or order.get("entry_price") or 0.0)

    title = f"✅ ORDER FILLED: {sym} [{market}]"
    lines = [
        f"<b>Symbol:</b> {sym}",
        f"<b>Filled:</b> {shares:,} shares @ {format_currency(fill_price, market)}",
        f"<b>Stop Loss:</b> {format_currency(float(order.get('stop_price', 0)), market)}",
        f"<b>Target:</b> {format_currency(float(order.get('target_price', 0)), market)}",
    ]
    return dispatch_alert("\n".join(lines), title=title)


def notify_order_quarantined(symbol: str, reason: str, market: str = "TH") -> dict[str, bool]:
    """Alert when an order is rejected and sent to dead-letter quarantine."""
    title = f"⚠️ ORDER QUARANTINED: {symbol} [{market}]"
    lines = [
        f"<b>Symbol:</b> {symbol}",
        f"<b>Reason:</b> {reason}",
        "<b>Action Taken:</b> Order moved to quarantine folder.",
    ]
    return dispatch_alert("\n".join(lines), title=title)


def notify_scale_out(
    symbol: str,
    shares_closed: int,
    total_shares: int,
    scale_price: float,
    pnl: float,
    new_stop: float,
    market: str = "TH",
) -> dict[str, bool]:
    """Alert when a position scales out 50% at T1 (1.5R) and ratchets stop to BE."""
    title = f"💰 SCALE-OUT (T1 HIT): {symbol} [{market}]"
    sign = "+" if pnl >= 0 else ""
    if shares_closed > 0:
        share_str = f"Closed {shares_closed:,}/{total_shares:,} shares"
    else:
        share_str = "Single share protected"

    lines = [
        f"<b>Symbol:</b> {symbol}",
        f"<b>Action:</b> {share_str} @ {format_currency(scale_price, market)}",
        f"<b>Banked PnL:</b> {sign}{format_currency(pnl, market)}",
        f"<b>Risk Status:</b> Breakeven Stop: {format_currency(new_stop, market)}",
        "<b>Strategy:</b> Remaining runner running risk-free to T2 (2.5R)!",
    ]
    return dispatch_alert("\n".join(lines), title=title)


def notify_position_closed(
    symbol: str,
    exit_price: float,
    status: str,
    realized_pnl: float,
    return_pct: float,
    days_held: int,
    market: str = "TH",
) -> dict[str, bool]:
    """Alert when a position is completely exited."""
    sign = "+" if realized_pnl >= 0 else ""
    status_upper = status.upper()
    status_clean = "TARGET HIT" if "TARGET" in status_upper else status_upper.replace("CLOSED_", "")
    icon = "🎉" if realized_pnl > 0 else "🛑"
    title = f"{icon} POSITION CLOSED ({status_clean}): {symbol} [{market}]"
    lines = [
        f"<b>Symbol:</b> {symbol}",
        f"<b>Exit Price:</b> {format_currency(exit_price, market)}",
        f"<b>Status:</b> {status_clean}",
        f"<b>Realized PnL:</b> {sign}{format_currency(realized_pnl, market)} ({sign}{return_pct:.2f}%)",
        f"<b>Days Held:</b> {days_held} days",
    ]
    return dispatch_alert("\n".join(lines), title=title)
