"""
Unit Test Suite for 15m Key Level "Rectangle" Break & Retest Scalper
Reference: Mulham Trading "My Simple 1 Minute Scalping Strategy (Sniper Entry)" (YouTube Y1r7fTJ0FZ8)
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

class TestMulhamRectangleScalper(unittest.TestCase):

    def setUp(self):
        # Base template candles for testing (20 candles)
        self.base_candles = []
        base_p = 2490.0
        for i in range(20):
            self.base_candles.append({
                "ts": 1700000000000 + i * 300000,
                "time": f"2026-09-09 10:{i*5:02d}",
                "open": base_p,
                "high": base_p + 4.0,
                "low": base_p - 4.0,
                "close": base_p + 1.0,
                "volume": 100.0
            })

    def test_long_rectangle_breakout_retest(self):
        """
        Tests 15m Resistance breakout followed by a clean retest into the Rectangle and bullish bounce.
        """
        candles = [dict(c) for c in self.base_candles]
        R = 2500.0

        # Breakout candle: closes strongly above R (2500)
        candles.append({
            "ts": 1700005000000,
            "time": "2026-09-09 11:15",
            "open": 2495.0,
            "high": 2518.0,
            "low": 2494.0,
            "close": 2515.0,
            "volume": 350.0
        })

        # Retest candle: dips into the rectangle [2495 - 2515]
        candles.append({
            "ts": 1700005300000,
            "time": "2026-09-09 11:20",
            "open": 2515.0,
            "high": 2516.0,
            "low": 2502.0,  # inside rectangle
            "close": 2508.0,
            "volume": 120.0
        })

        # Rejection candle (current): bounces with strong lower wick / green close
        candles.append({
            "ts": 1700005600000,
            "time": "2026-09-09 11:25",
            "open": 2508.0,
            "high": 2522.0,
            "low": 2501.0,
            "close": 2520.0,
            "volume": 200.0
        })

        levels_15m = {"highs": [R], "lows": [2450.0]}
        signal = fast_scalper.scan_15m_rectangle_break_retest_scalp("ETHUSDT", candles, levels_15m=levels_15m)

        self.assertIsNotNone(signal, "Should detect a valid LONG 15m Rectangle Break & Retest setup")
        self.assertEqual(signal["side"], "LONG")
        self.assertEqual(signal["strategy"], "5m 15m-Key-Level Rectangle Break & Retest")
        self.assertEqual(signal["rr_ratio"], 2.0)
        self.assertLess(signal["sl"], signal["entry"])
        self.assertGreater(signal["tp"], signal["entry"])

        expected_tp = round(signal["entry"] + (signal["r_dist"] * 2.0), 4)
        self.assertEqual(signal["tp"], expected_tp)

    def test_short_rectangle_breakdown_retest(self):
        """
        Tests 15m Support breakdown followed by a clean retest into the Rectangle and bearish bounce.
        """
        candles = []
        base_p = 2510.0
        for i in range(20):
            candles.append({
                "ts": 1700000000000 + i * 300000,
                "time": f"2026-09-09 10:{i*5:02d}",
                "open": base_p,
                "high": base_p + 4.0,
                "low": base_p - 4.0,
                "close": base_p - 1.0,
                "volume": 100.0
            })

        S = 2500.0

        # Breakdown candle: closes strongly below S (2500)
        candles.append({
            "ts": 1700005000000,
            "time": "2026-09-09 11:15",
            "open": 2505.0,
            "high": 2506.0,
            "low": 2482.0,
            "close": 2485.0,
            "volume": 350.0
        })

        # Retest candle: pulls back up into rectangle [2485 - 2505]
        candles.append({
            "ts": 1700005300000,
            "time": "2026-09-09 11:20",
            "open": 2485.0,
            "high": 2498.0,  # inside rectangle
            "low": 2484.0,
            "close": 2492.0,
            "volume": 120.0
        })

        # Rejection candle (current): rejects down with upper wick / red close
        candles.append({
            "ts": 1700005600000,
            "time": "2026-09-09 11:25",
            "open": 2492.0,
            "high": 2499.0,
            "low": 2478.0,
            "close": 2480.0,
            "volume": 200.0
        })

        levels_15m = {"highs": [2550.0], "lows": [S]}
        signal = fast_scalper.scan_15m_rectangle_break_retest_scalp("ETHUSDT", candles, levels_15m=levels_15m)

        self.assertIsNotNone(signal, "Should detect a valid SHORT 15m Rectangle Breakdown & Retest setup")
        self.assertEqual(signal["side"], "SHORT")
        self.assertEqual(signal["strategy"], "5m 15m-Key-Level Rectangle Break & Retest")
        self.assertEqual(signal["rr_ratio"], 2.0)
        self.assertGreater(signal["sl"], signal["entry"])
        self.assertLess(signal["tp"], signal["entry"])

        expected_tp = round(signal["entry"] - (signal["r_dist"] * 2.0), 4)
        self.assertEqual(signal["tp"], expected_tp)

    def test_invalidation_when_retest_violates_boundary(self):
        """
        Tests that when a retest plunges deeply beyond the rectangle boundary,
        the setup is properly invalidated and rejected.
        """
        candles = [dict(c) for c in self.base_candles]
        R = 2500.0

        # Breakout candle
        candles.append({
            "ts": 1700005000000,
            "time": "2026-09-09 11:15",
            "open": 2495.0,
            "high": 2515.0,
            "low": 2494.0,
            "close": 2512.0,
            "volume": 300.0
        })

        # Failed retest: crashes straight through rectangle base (2495) down to 2470
        candles.append({
            "ts": 1700005300000,
            "time": "2026-09-09 11:20",
            "open": 2512.0,
            "high": 2513.0,
            "low": 2465.0,
            "close": 2470.0,  # Deep failure
            "volume": 400.0
        })

        candles.append({
            "ts": 1700005600000,
            "time": "2026-09-09 11:25",
            "open": 2470.0,
            "high": 2475.0,
            "low": 2468.0,
            "close": 2472.0,
            "volume": 150.0
        })

        levels_15m = {"highs": [R], "lows": [2450.0]}
        signal = fast_scalper.scan_15m_rectangle_break_retest_scalp("ETHUSDT", candles, levels_15m=levels_15m)
        self.assertIsNone(signal, "Failed retest should NOT trigger a setup")

    @patch("coinbase_premium.get_coinbase_premium")
    def test_session_filter_confluence_recognition(self, mock_cb):
        """
        Tests that session_filter recognizes 15m Rectangle Break & Retest and awards +23 pts.
        """
        mock_cb.return_value = {
            "premium_pct": 0.05,
            "is_us_inflow": True,
            "is_us_dump": False,
            "confluence_bonus": 4
        }

        setup = {
            "symbol": "ETHUSDT",
            "base": "ETH",
            "side": "LONG",
            "strategy": "5m 15m-Key-Level Rectangle Break & Retest",
            "entry": 2520.0,
            "sl": 2500.0,
            "tp": 2560.0,
            "rr": 2.0,
            "is_scalp": True,
            "is_mean_reversion_or_sweep": True,
            "macro_aligned": True,
            "reason": "15m Resistance broken & flipped to Support"
        }

        # Mock session info to avoid midnight DEAD_ZONE threshold
        mock_session = {
            "session_name": "London Open",
            "session_code": "LONDON_OPEN",
            "is_active": True,
            "min_threshold": 70,
            "bonus_score": 10,
            "is_dead_zone": False
        }

        is_valid, summary, score_data = session_filter.audit_candidate_confluence(setup, session_info=mock_session)

        breakdown = score_data["breakdown"]
        self.assertIn("Key Level / Structure", breakdown)
        self.assertIn("+23 pts", breakdown["Key Level / Structure"])
        self.assertIn("Mulham Sniper", breakdown["Key Level / Structure"])
        self.assertGreaterEqual(score_data["score"], 75)
        self.assertTrue(is_valid)

if __name__ == "__main__":
    unittest.main()
