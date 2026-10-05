import os
import unittest
from unittest.mock import MagicMock, patch

from scripts.notify_service import (
    dispatch_alert,
    format_currency,
    notify_order_quarantined,
    notify_order_staged,
    notify_position_closed,
    notify_scale_out,
)


class TestNotifyService(unittest.TestCase):
    def setUp(self):
        self.mock_env = {
            "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "TELEGRAM_CHAT_ID": "-1001234567890",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc",
            "LINE_NOTIFY_TOKEN": "mock_line_token",
        }

    def test_format_currency(self):
        self.assertEqual(format_currency(1234.5, "TH"), "฿1,234.50")
        self.assertEqual(format_currency(1234.5, "US"), "$1,234.50")
        self.assertEqual(format_currency(0.0, "US"), "$0.00")

    @patch("requests.post")
    def test_dispatch_alert_sends_to_all_configured_channels(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        with patch.dict(os.environ, self.mock_env):
            res = dispatch_alert("Test Alert Message", title="TEST ALERT")

        self.assertTrue(res["telegram"])
        self.assertTrue(res["discord"])
        self.assertTrue(res["line"])
        self.assertEqual(mock_post.call_count, 3)

    @patch("requests.post")
    def test_dispatch_alert_graceful_when_no_channels_configured(self, mock_post):
        # Empty env
        with patch.dict(os.environ, {}, clear=True):
            res = dispatch_alert("Test Silent Message")

        self.assertFalse(res["telegram"])
        self.assertFalse(res["discord"])
        self.assertFalse(res["line"])
        mock_post.assert_not_called()

    @patch("scripts.notify_service.dispatch_alert")
    def test_notify_order_staged(self, mock_dispatch):
        mock_dispatch.return_value = {"telegram": True}
        order = {
            "symbol": "ADVANC.BK",
            "market": "TH",
            "shares": 100,
            "entry_price": 250.0,
            "stop_price": 240.0,
            "target_price": 275.0,
            "t1_price": 265.0,
            "t2_price": 275.0,
            "max_chase_pct": 0.01,
            "thesis": "High conviction breakout setup",
        }
        res = notify_order_staged(order)
        self.assertIsNotNone(res)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        self.assertIn("ORDER STAGED", kwargs.get("title", ""))
        self.assertIn("ADVANC.BK", args[0])
        self.assertIn("250.00", args[0])

    @patch("scripts.notify_service.dispatch_alert")
    def test_notify_scale_out(self, mock_dispatch):
        mock_dispatch.return_value = {"discord": True}
        res = notify_scale_out(
            symbol="PBR.A",
            shares_closed=5,
            total_shares=11,
            scale_price=20.50,
            pnl=12.50,
            new_stop=19.10,
            market="US",
        )
        self.assertIsNotNone(res)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        self.assertIn("SCALE-OUT (T1 HIT)", kwargs.get("title", ""))
        self.assertIn("PBR.A", args[0])
        self.assertIn("+$12.50", args[0])
        self.assertIn("Breakeven Stop: $19.10", args[0])

    @patch("scripts.notify_service.dispatch_alert")
    def test_notify_position_closed(self, mock_dispatch):
        mock_dispatch.return_value = {"line": True}
        res = notify_position_closed(
            symbol="CPALL.BK",
            exit_price=66.0,
            status="closed_target",
            realized_pnl=1200.0,
            return_pct=4.8,
            days_held=3,
            market="TH",
        )
        self.assertIsNotNone(res)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        self.assertIn("POSITION CLOSED", kwargs.get("title", ""))
        self.assertIn("CPALL.BK", args[0])
        self.assertIn("+฿1,200.00", args[0])
        self.assertIn("TARGET HIT", args[0])

    @patch("scripts.notify_service.dispatch_alert")
    def test_notify_order_quarantined(self, mock_dispatch):
        mock_dispatch.return_value = {"telegram": True}
        res = notify_order_quarantined(
            symbol="CHASE.BK",
            reason="Chase limit exceeded: price is +2.5% above trigger",
            market="TH",
        )
        self.assertIsNotNone(res)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        self.assertIn("ORDER QUARANTINED", kwargs.get("title", ""))
        self.assertIn("CHASE.BK", args[0])


if __name__ == "__main__":
    unittest.main()
