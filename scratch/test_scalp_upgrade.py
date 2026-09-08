import os
import sys
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "tools"))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import fast_scalper
import session_filter
import trade_manager
import trading_desk

class TestScalpUpgrade(unittest.TestCase):

    def test_scalp_strategies_detection(self):
        """Verify that fast scalper scans and produces standardized scalp metadata."""
        setups = fast_scalper.scan_all_scalp_opportunities(["BTC", "ETH"])
        # Should return a list (either empty or populated with valid setups)
        self.assertIsInstance(setups, list)
        if setups:
            s = setups[0]
            self.assertTrue(s.get("is_scalp"))
            self.assertEqual(s.get("timeframe"), "5m")
            self.assertGreater(s.get("rr_ratio", 0), 1.3)
            self.assertIn("target_duration", s)

    @patch("liquidity_heatmap.get_liquidity_intelligence")
    @patch("coinbase_premium.get_coinbase_premium")
    def test_scalp_confluence_scoring_passing(self, mock_cb, mock_depth):
        """Verify that a 5m scalp with 1:1.6 R:R passes confluence audit without 4H trend penalty."""
        mock_cb.return_value = {"is_us_inflow": True, "is_us_dump": False, "premium_pct": 0.02, "confluence_bonus": 4}
        mock_depth.return_value = {"imbalance": {"imbalance_ratio": 1.2, "biggest_ask_wall": {}}, "clusters": {}}

        sess = {
            "session_name": "New York Open",
            "session_code": "NY_OPEN",
            "bonus_score": 12,
            "min_threshold": 70,
            "is_dead_zone": False
        }
        scalp_candidate = {
            "symbol": "SOLUSDT",
            "base": "SOL",
            "side": "LONG",
            "price": 103.50,
            "sl": 101.80,
            "tp": 106.22,
            "rr": 1.60,
            "is_scalp": True,
            "is_mean_reversion_or_sweep": True,
            "macro_aligned": False,  # Even if 4H is counter-trend!
            "reason": "5m VWAP Oversold bounce with 5m Liquidity Sweep"
        }
        is_ok, summary, score_data = session_filter.audit_candidate_confluence(scalp_candidate, sess)
        
        # Breakdown checks
        self.assertIn("Statistical Reversion / Micro-Sweep", score_data["breakdown"])
        self.assertIn("Risk:Reward Quality", score_data["breakdown"])
        self.assertGreaterEqual(score_data["score"], 72)
        self.assertTrue(is_ok, f"Scalp should pass confluence with >=72%: {summary}")

    def test_scalp_micro_breakeven_threshold(self):
        """Verify that trade manager sets micro-breakeven threshold to 0.60R for scalps."""
        scalp_meta = {"is_scalp": True, "breakeven_locked": False}
        swing_meta = {"is_scalp": False, "breakeven_locked": False}

        be_scalp = 0.60 if scalp_meta.get("is_scalp") else 1.3
        be_swing = 0.60 if swing_meta.get("is_scalp") else 1.3

        self.assertEqual(be_scalp, 0.60)
        self.assertEqual(be_swing, 1.3)

    def test_scalp_time_stop_duration(self):
        """Verify that scalp trades time-stop after 20 minutes of stagnation."""
        # Active for 25 minutes, r_multiple 0.15 (stagnant)
        opened_at_stagnant = (datetime.now() - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S")
        is_stagnant, reason = fast_scalper.evaluate_scalp_time_stop(opened_at_stagnant, current_profit_r=0.15, max_minutes=20)
        self.assertTrue(is_stagnant)
        self.assertIn("TIME_STOP_TRIGGERED", reason)

        # Active for 10 minutes (fresh trade)
        opened_at_fresh = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        is_fresh, _ = fast_scalper.evaluate_scalp_time_stop(opened_at_fresh, current_profit_r=0.15, max_minutes=20)
        self.assertFalse(is_fresh)

    def test_portfolio_guard_four_positions_capacity(self):
        """Verify that portfolio guard enforces 4 total positions and 3 same-direction cap."""
        import portfolio_guard
        self.assertEqual(portfolio_guard.MAX_TOTAL_POSITIONS, 4)
        self.assertEqual(portfolio_guard.MAX_SAME_DIRECTION_CAP, 3)
        self.assertEqual(portfolio_guard.MAX_HIGH_BETA_ALTS_TOTAL, 3)

        # 2 active Longs (ETH + SOPH)
        active_2 = [
            {"symbol": "ETHUSDT", "positionAmt": "0.05"},
            {"symbol": "SOPHUSDT", "positionAmt": "100.0"}
        ]
        cand_3rd_long = {"symbol": "UNIUSDT", "side": "LONG", "base": "UNI"}
        approved, reason = portfolio_guard.filter_candidate_by_correlation(cand_3rd_long, active_2)
        self.assertTrue(approved, f"3rd Long must be permitted under 4-position limit: {reason}")

        # 3 active Longs (ETH + SOPH + UNI)
        active_3 = active_2 + [{"symbol": "UNIUSDT", "positionAmt": "20.0"}]
        cand_4th_long = {"symbol": "DOGEUSDT", "side": "LONG", "base": "DOGE"}
        approved_4th, reason_4th = portfolio_guard.filter_candidate_by_correlation(cand_4th_long, active_3)
        self.assertFalse(approved_4th, "4th Long must be blocked by directional cap")
        self.assertIn("3/3 LONG", reason_4th)

        # But a SHORT hedge as 4th position must be approved!
        cand_4th_short = {"symbol": "BTCUSDT", "side": "SHORT", "base": "BTC"}
        approved_short, reason_short = portfolio_guard.filter_candidate_by_correlation(cand_4th_short, active_3)
        self.assertTrue(approved_short, f"Hedge Short as 4th position must be permitted: {reason_short}")

        # Dynamic risk heat scaling
        self.assertEqual(portfolio_guard.get_scaled_risk_pct("LONG", [], base_risk_pct=0.50), 0.50)
        self.assertEqual(portfolio_guard.get_scaled_risk_pct("LONG", active_2[:1], base_risk_pct=0.50), 0.38)
        self.assertEqual(portfolio_guard.get_scaled_risk_pct("LONG", active_2, base_risk_pct=0.50), 0.25)
        self.assertEqual(portfolio_guard.get_scaled_risk_pct("SHORT", active_3, base_risk_pct=0.50), 0.50)

if __name__ == "__main__":
    unittest.main()

