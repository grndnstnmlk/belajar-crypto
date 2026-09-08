"""
Unit Test Suite for Tauric Adversarial Debate Layer (Bull vs Bear Agent)
Inspired by Tauric Research's TradingAgents Multi-Agent Framework (arXiv:2412.20138).
"""

import sys
import os
import unittest
from unittest.mock import patch

# Ensure .agents/tools is in Python path
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "tools"))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import adversarial_debate
import ai_risk_officer

class TestAdversarialDebate(unittest.TestCase):

    def test_bull_wins_strong_setup(self):
        """
        Tests that an institutional setup with high R:R, bullish BTC macro,
        thick bid support, and verified Akademi Crypto strategy leads to a Bull victory.
        """
        setup = {
            "symbol": "SOLUSDT",
            "side": "LONG",
            "entry": 104.00,
            "sl": 102.50,
            "tp": 107.00,
            "rr_ratio": 2.0,
            "strategy": "5m Akademi Crypto High Win-Rate Scalp",
            "is_scalp": True
        }
        ctx = {
            "market_regime": {"trend_bias": "BULLISH", "adx": 30.0},
            "compass": {"regime_code": "ALT_SEASON_RISK_ON"},
            "depth": {"imbalance_ratio": 1.40}
        }
        res = adversarial_debate.run_adversarial_debate(setup, ctx)
        self.assertEqual(res["verdict"], "APPROVE")
        self.assertEqual(res["winner"], "BULL")
        self.assertGreater(res["bull_score"], res["bear_score"])
        self.assertEqual(res["suggested_risk_scale"], 1.0)
        self.assertIn("Bull", res["bull_thesis"])

    def test_bear_wins_veto_btc_drag(self):
        """
        Tests that an altcoin LONG setup fighting BTC macro gravity with low R:R
        and heavy overhead ask resistance causes Bear Researcher to win and trigger VETO.
        """
        setup = {
            "symbol": "DOGEUSDT",
            "side": "LONG",
            "entry": 0.0900,
            "sl": 0.0885,
            "tp": 0.0915,
            "rr_ratio": 1.0,
            "strategy": "Random Local Wick",
            "is_scalp": False
        }
        ctx = {
            "market_regime": {"trend_bias": "BEARISH", "adx": 16.0},
            "compass": {"regime_code": "CAPITAL_FLIGHT"},
            "depth": {"imbalance_ratio": 0.50}
        }
        res = adversarial_debate.run_adversarial_debate(setup, ctx)
        self.assertEqual(res["verdict"], "VETO")
        self.assertEqual(res["winner"], "BEAR")
        self.assertGreaterEqual(res["bear_score"], 65)
        self.assertEqual(res["suggested_risk_scale"], 0.0)
        self.assertIn("VETO", res["arbiter_synthesis"])

    def test_compromise_risk_adjustment(self):
        """
        Tests that mixed signals (neutral BTC but thin R:R or slight wall)
        leads to a COMPROMISE verdict with 50% risk scaling.
        """
        setup = {
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry": 2490.00,
            "sl": 2470.00,
            "tp": 2525.00,
            "rr_ratio": 1.75,
            "strategy": "5m VWAP Mean-Reversion",
            "is_scalp": True
        }
        ctx = {
            "market_regime": {"trend_bias": "NEUTRAL", "adx": 22.0},
            "depth": {"imbalance_ratio": 0.90}
        }
        res = adversarial_debate.run_adversarial_debate(setup, ctx)
        self.assertIn(res["verdict"], ["ADJUST_RISK", "APPROVE"])
        if res["verdict"] == "ADJUST_RISK":
            self.assertEqual(res["suggested_risk_scale"], 0.5)

    def test_history_persistence(self):
        """
        Tests that completed debates can be written to disk and loaded back.
        """
        mock_rec = {
            "symbol": "TESTUSDT",
            "side": "LONG",
            "bull_score": 65,
            "bear_score": 35,
            "winner": "BULL",
            "verdict": "APPROVE",
            "suggested_risk_scale": 1.0,
            "timestamp": "2026-09-09 01:00:00"
        }
        adversarial_debate.save_debate_record(mock_rec)
        history = adversarial_debate.load_debate_history(limit=5)
        self.assertGreater(len(history), 0)
        last = history[-1]
        self.assertEqual(last["symbol"], "TESTUSDT")

    def test_ai_risk_officer_integration(self):
        """
        Tests that ai_risk_officer.audit_trade_setup integrates the adversarial debate
        and honors VETO verdicts.
        """
        bad_setup = {
            "symbol": "LINKUSDT",
            "side": "LONG",
            "entry": 12.50,
            "sl": 12.35,
            "tp": 12.60,
            "rr_ratio": 0.67,
            "strategy": "Impulse Chase",
            "is_scalp": False
        }
        ctx = {
            "market_regime": {"trend_bias": "BEARISH", "adx": 15.0},
            "depth": {"imbalance_ratio": 0.45}
        }
        audit = ai_risk_officer.audit_trade_setup(bad_setup, ctx)
        self.assertIn("adversarial_debate", audit)
        self.assertEqual(audit["decision"], "VETO")
        self.assertEqual(audit["suggested_risk_scale"], 0.0)

if __name__ == "__main__":
    unittest.main()
