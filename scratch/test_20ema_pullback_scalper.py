"""
Unit Test Suite for 5m 20-EMA Dynamic Pullback Trap Scalper
Reference: Trader DNA "(9 Wins Out of 10)... This 90% WIN RATE Scalping Strategy Should Be Illegal" (YouTube ll_9xH10KPY)
"""

import os
import sys
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, ".agents", "tools")
sys.path.insert(0, TOOLS_DIR)

import fast_scalper
import session_filter

class Test20EmaPullbackScalper(unittest.TestCase):

    @patch("fast_scalper.get_15m_context")
    def test_bullish_20ema_pullback_trap(self, mock_ctx):
        """
        Tests that a bullish pullback below 20 EMA followed by a decisive bullish reclaim triggers a LONG 2R setup.
        """
        mock_ctx.return_value = {"bias": "BULLISH", "trend": "BULLISH"}

        # Construct steady uptrend candles (30 candles)
        candles = []
        base_p = 2000.0
        for i in range(25):
            p = base_p + (i * 4.0)  # rising 2000 to ~2096
            candles.append({
                "ts": 1700000000000 + i * 300000,
                "time": f"2026-09-09 10:{i*5:02d}",
                "open": p - 1.0,
                "high": p + 3.0,
                "low": p - 2.0,
                "close": p + 2.0,
                "volume": 100.0
            })

        # Calculate where 20 EMA currently sits
        closes = [c["close"] for c in candles]
        ema20 = fast_scalper.calc_ema_series(closes, 20)[-1]

        # Candle 26: Dip below 20 EMA (Discount pullback)
        candles.append({
            "ts": 1700007800000,
            "time": "2026-09-09 12:05",
            "open": ema20 + 2.0,
            "high": ema20 + 3.0,
            "low": ema20 - 8.0,  # clearly below 20 EMA
            "close": ema20 - 4.0, # closed below 20 EMA
            "volume": 150.0
        })

        # Candle 27 (Current): Decisive bullish reclaim closing back above 20 EMA
        candles.append({
            "ts": 1700008100000,
            "time": "2026-09-09 12:10",
            "open": ema20 - 3.0,
            "high": ema20 + 7.0,
            "low": ema20 - 4.0,
            "close": ema20 + 6.0,  # closed firmly above 20 EMA
            "volume": 250.0
        })

        signal = fast_scalper.scan_5m_20ema_pullback_trap_scalp("ETHUSDT", candles)

        self.assertIsNotNone(signal, "Should detect a valid Bullish 20-EMA Pullback Trap")
        self.assertEqual(signal["side"], "LONG")
        self.assertEqual(signal["strategy"], "5m 20-EMA Dynamic Pullback Trap")
        self.assertEqual(signal["rr_ratio"], 2.0)
        self.assertLess(signal["sl"], signal["entry"])
        self.assertGreater(signal["tp"], signal["entry"])

        expected_tp = round(signal["entry"] + (signal["r_dist"] * 2.0), 4)
        self.assertEqual(signal["tp"], expected_tp)

    @patch("fast_scalper.get_15m_context")
    def test_bearish_20ema_pullback_trap(self, mock_ctx):
        """
        Tests that a bearish rally above 20 EMA followed by a decisive bearish rejection triggers a SHORT 2R setup.
        """
        mock_ctx.return_value = {"bias": "BEARISH", "trend": "BEARISH"}

        # Construct steady downtrend candles (30 candles)
        candles = []
        base_p = 2200.0
        for i in range(25):
            p = base_p - (i * 4.0)  # falling 2200 to ~2104
            candles.append({
                "ts": 1700000000000 + i * 300000,
                "time": f"2026-09-09 10:{i*5:02d}",
                "open": p + 1.0,
                "high": p + 2.0,
                "low": p - 3.0,
                "close": p - 2.0,
                "volume": 100.0
            })

        # Calculate where 20 EMA currently sits
        closes = [c["close"] for c in candles]
        ema20 = fast_scalper.calc_ema_series(closes, 20)[-1]

        # Candle 26: Rally above 20 EMA (Premium bull trap)
        candles.append({
            "ts": 1700007800000,
            "time": "2026-09-09 12:05",
            "open": ema20 - 2.0,
            "high": ema20 + 8.0,  # clearly above 20 EMA
            "low": ema20 - 3.0,
            "close": ema20 + 4.0, # closed above 20 EMA
            "volume": 150.0
        })

        # Candle 27 (Current): Decisive bearish rejection closing back below 20 EMA
        candles.append({
            "ts": 1700008100000,
            "time": "2026-09-09 12:10",
            "open": ema20 + 3.0,
            "high": ema20 + 4.0,
            "low": ema20 - 7.0,
            "close": ema20 - 6.0,  # closed firmly below 20 EMA
            "volume": 250.0
        })

        signal = fast_scalper.scan_5m_20ema_pullback_trap_scalp("ETHUSDT", candles)

        self.assertIsNotNone(signal, "Should detect a valid Bearish 20-EMA Pullback Trap")
        self.assertEqual(signal["side"], "SHORT")
        self.assertEqual(signal["strategy"], "5m 20-EMA Dynamic Pullback Trap")
        self.assertEqual(signal["rr_ratio"], 2.0)
        self.assertGreater(signal["sl"], signal["entry"])
        self.assertLess(signal["tp"], signal["entry"])

        expected_tp = round(signal["entry"] - (signal["r_dist"] * 2.0), 4)
        self.assertEqual(signal["tp"], expected_tp)

    @patch("fast_scalper.get_15m_context")
    def test_no_dip_no_signal(self, mock_ctx):
        """
        Tests that when price remains completely above 20 EMA without a dip, no trap is triggered.
        """
        mock_ctx.return_value = {"bias": "BULLISH", "trend": "BULLISH"}
        candles = []
        base_p = 2000.0
        for i in range(30):
            p = base_p + (i * 5.0)
            candles.append({
                "ts": 1700000000000 + i * 300000,
                "time": f"2026-09-09 10:{i*5:02d}",
                "open": p,
                "high": p + 4.0,
                "low": p + 1.0,  # strictly above
                "close": p + 3.0,
                "volume": 100.0
            })
        signal = fast_scalper.scan_5m_20ema_pullback_trap_scalp("ETHUSDT", candles)
        self.assertIsNone(signal, "Price running without EMA dip should NOT trigger a setup")

    @patch("fast_scalper.get_15m_context")
    def test_macro_counter_trend_blocked(self, mock_ctx):
        """
        Tests that when 15m trend is BEARISH, a long EMA dip is prevented.
        """
        mock_ctx.return_value = {"bias": "BEARISH", "trend": "BEARISH"}
        candles = []
        base_p = 2000.0
        for i in range(25):
            p = base_p + (i * 4.0)
            candles.append({
                "ts": 1700000000000 + i * 300000,
                "time": f"2026-09-09 10:{i*5:02d}",
                "open": p - 1.0,
                "high": p + 3.0,
                "low": p - 2.0,
                "close": p + 2.0,
                "volume": 100.0
            })
        closes = [c["close"] for c in candles]
        ema20 = fast_scalper.calc_ema_series(closes, 20)[-1]
        candles.append({
            "ts": 1700007800000,
            "time": "2026-09-09 12:05",
            "open": ema20 + 2.0,
            "high": ema20 + 3.0,
            "low": ema20 - 8.0,
            "close": ema20 - 4.0,
            "volume": 150.0
        })
        candles.append({
            "ts": 1700008100000,
            "time": "2026-09-09 12:10",
            "open": ema20 - 3.0,
            "high": ema20 + 7.0,
            "low": ema20 - 4.0,
            "close": ema20 + 6.0,
            "volume": 250.0
        })

        signal = fast_scalper.scan_5m_20ema_pullback_trap_scalp("ETHUSDT", candles)
        self.assertIsNone(signal, "Counter-trend trade against 15m bias should be blocked")

    @patch("coinbase_premium.get_coinbase_premium")
    def test_session_filter_confluence_recognition(self, mock_cb):
        """
        Tests that session_filter recognizes 20-EMA Dynamic Pullback Trap and awards +22 pts.
        """
        mock_cb.return_value = {
            "premium_pct": 0.04,
            "is_us_inflow": True,
            "is_us_dump": False,
            "confluence_bonus": 4
        }

        setup = {
            "symbol": "ETHUSDT",
            "base": "ETH",
            "side": "LONG",
            "strategy": "5m 20-EMA Dynamic Pullback Trap",
            "entry": 2150.0,
            "sl": 2135.0,
            "tp": 2180.0,
            "rr": 2.0,
            "is_scalp": True,
            "is_mean_reversion_or_sweep": True,
            "macro_aligned": True,
            "reason": "20-EMA Discount Trap: Price dipped below 20 EMA and reclaimed"
        }

        mock_session = {
            "session_name": "New York Open",
            "session_code": "NY_OPEN",
            "is_active": True,
            "min_threshold": 70,
            "bonus_score": 12,
            "is_dead_zone": False
        }

        is_valid, summary, score_data = session_filter.audit_candidate_confluence(setup, session_info=mock_session)

        breakdown = score_data["breakdown"]
        self.assertIn("Key Level / Structure", breakdown)
        self.assertIn("+22 pts", breakdown["Key Level / Structure"])
        self.assertIn("Trader DNA", breakdown["Key Level / Structure"])
        self.assertGreaterEqual(score_data["score"], 75)
        self.assertTrue(is_valid)

if __name__ == "__main__":
    unittest.main()
