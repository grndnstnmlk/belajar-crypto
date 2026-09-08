"""
Verification Suite for Tauric Tri-Perspective Risk Balancing Layer
Tests:
1. Optimal Setup Execution: High R:R, clean margin -> Approved Optimal/Balanced
2. High Portfolio Heat: 3 existing Longs -> Conservative spikes, Approved Defensive
3. Extreme Saturated Risk: Low margin, directional overflow -> Blocked Risk Limit (Veto)
4. AI Risk Officer Pre-Trade Integration: Verifies seamless gatekeeping
5. Disk Persistence & Retrieval
"""

import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, ".agents", "tools")
sys.path.insert(0, TOOLS_DIR)

import tri_perspective_risk
import ai_risk_officer

class TestTriPerspectiveRisk(unittest.TestCase):

    def test_01_optimal_setup_clearance(self):
        """Test prime conditions: High R:R, strong Bull conviction, fresh portfolio."""
        setup = {
            "symbol": "SOLUSDT",
            "side": "BUY",
            "entry_price": 145.0,
            "sl": 142.0,
            "tp": 155.0,
            "rr": 3.33,
            "strategy": "Institutional FVG Reversal"
        }
        portfolio_state = {
            "active_positions": [],
            "heat": {"long_count": 0, "short_count": 0},
            "free_margin_ratio": 0.90
        }
        market_ctx = {
            "adversarial_debate": {"bull_score": 75, "bear_score": 25},
            "market_regime": {"adx": 30.0, "trend_bias": "BULLISH"}
        }

        res = tri_perspective_risk.run_tri_perspective_risk(setup, portfolio_state, market_ctx)
        
        self.assertIn("fund_manager", res)
        fm = res["fund_manager"]
        self.assertIn(fm["verdict"], ["APPROVED_OPTIMAL", "APPROVED_BALANCED"])
        self.assertGreaterEqual(fm["allocated_risk_scale"], 0.90)
        self.assertGreaterEqual(res["aggressive"]["score"], 70)
        self.assertGreaterEqual(res["conservative"]["score"], 60)
        print(f"\n[Test 1 PASS] Optimal Setup -> {fm['verdict']} (Scale: {fm['allocated_risk_scale']:.2f}x)")

    def test_02_high_portfolio_heat_defensive(self):
        """Test crowded portfolio: 2 Long positions already open -> triggers defensive trimming."""
        setup = {
            "symbol": "ETHUSDT",
            "side": "BUY",
            "entry_price": 2700.0,
            "sl": 2660.0,
            "tp": 2780.0,
            "rr": 2.0,
            "strategy": "20-EMA Pullback"
        }
        portfolio_state = {
            "active_positions": [
                {"symbol": "BTCUSDT", "positionAmt": 0.05},
                {"symbol": "SOLUSDT", "positionAmt": 2.0}
            ],
            "heat": {"long_count": 2, "short_count": 0},
            "free_margin_ratio": 0.65
        }
        market_ctx = {
            "adversarial_debate": {"bull_score": 60, "bear_score": 40},
            "market_regime": {"adx": 22.0, "trend_bias": "NEUTRAL"}
        }

        res = tri_perspective_risk.run_tri_perspective_risk(setup, portfolio_state, market_ctx)
        fm = res["fund_manager"]
        
        self.assertIn(fm["verdict"], ["APPROVED_BALANCED", "APPROVED_DEFENSIVE"])
        self.assertLessEqual(fm["allocated_risk_scale"], 0.85)
        self.assertGreaterEqual(fm["regime_weights"]["conservative"], 0.35)
        print(f"[Test 2 PASS] High Heat (2 Longs) -> {fm['verdict']} (Scale: {fm['allocated_risk_scale']:.2f}x)")

    def test_03_extreme_risk_blocked_limit(self):
        """Test saturated risk: 4 Long positions, critical margin -> Fund Manager VETO."""
        setup = {
            "symbol": "DOGEUSDT",
            "side": "BUY",
            "entry_price": 0.12,
            "sl": 0.118,
            "tp": 0.124,
            "rr": 2.0,
            "strategy": "Scalp Breakout"
        }
        portfolio_state = {
            "active_positions": [
                {"symbol": "BTCUSDT", "positionAmt": 0.05},
                {"symbol": "ETHUSDT", "positionAmt": 0.5},
                {"symbol": "SOLUSDT", "positionAmt": 5.0},
                {"symbol": "AVAXUSDT", "positionAmt": 10.0}
            ],
            "heat": {"long_count": 4, "short_count": 0},
            "free_margin_ratio": 0.25 # Critical margin
        }
        market_ctx = {
            "adversarial_debate": {"bull_score": 50, "bear_score": 50},
            "market_regime": {"adx": 15.0, "trend_bias": "NEUTRAL"}
        }

        res = tri_perspective_risk.run_tri_perspective_risk(setup, portfolio_state, market_ctx)
        fm = res["fund_manager"]

        self.assertEqual(fm["verdict"], "BLOCKED_RISK_LIMIT")
        self.assertEqual(fm["allocated_risk_scale"], 0.0)
        print(f"[Test 3 PASS] Saturated Risk -> {fm['verdict']} (Scale: {fm['allocated_risk_scale']:.2f}x)")

    def test_04_ai_risk_officer_integration(self):
        """Test end-to-end integration: ai_risk_officer.heuristic_quant_audit enforces tri-risk."""
        setup = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "price": 65000.0,
            "entry": 65000.0,
            "sl": 64200.0,
            "tp": 67400.0,
            "rr": 3.0,
            "strategy": "Institutional FVG Retest"
        }
        ctx = {
            "active_positions": [],
            "free_margin_ratio": 0.90,
            "heat": {"long_count": 0, "short_count": 0},
            "market_regime": {"trend_bias": "BULLISH", "adx": 28.0, "bias": "BULLISH"}
        }

        audit = ai_risk_officer.heuristic_quant_audit(setup, ctx)
        
        self.assertIn("tri_perspective_risk", audit)
        self.assertIn("adversarial_debate", audit)
        self.assertIsNotNone(audit["tri_perspective_risk"])
        fm = audit["tri_perspective_risk"]["fund_manager"]
        self.assertIn(fm["verdict"], ["APPROVED_OPTIMAL", "APPROVED_BALANCED"])
        print(f"[Test 4 PASS] AI Risk Officer Audit -> Decision: {audit['decision']} | Tri-Risk: {fm['verdict']}")

    def test_05_disk_persistence_and_loading(self):
        """Test persistence of evaluations to disk."""
        history = tri_perspective_risk.load_tri_risk_history(limit=5)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        latest = history[-1]
        self.assertIn("fund_manager", latest)
        self.assertIn("aggressive", latest)
        self.assertIn("conservative", latest)
        self.assertIn("neutral", latest)
        print(f"[Test 5 PASS] Disk Persistence -> Loaded {len(history)} tri-risk records. Latest: {latest['symbol']} ({latest['fund_manager']['verdict']})")

if __name__ == "__main__":
    unittest.main()
