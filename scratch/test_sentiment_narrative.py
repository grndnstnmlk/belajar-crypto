"""
Verification Suite for Tauric Sentiment & Social Narrative Scanner
Tests:
1. Crypto Fear & Greed Index Engine (Live score, 7-day trend, contrarian interpretation)
2. Narrative Sector Rotation Radar (6 sectors, leader detection, beta vs BTC)
3. Social Virality & Search Buzz (CoinGecko trending tokens, virality stages)
4. Catalyst Sentiment Classifier (Dual-Engine: Bullish/Bearish NLP lexicon)
5. Token Narrative Confluence & AI Risk Officer Integration
"""

import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, ".agents", "tools")
sys.path.insert(0, TOOLS_DIR)

import sentiment_narrative_scanner
import ai_risk_officer

class TestSentimentNarrativeScanner(unittest.TestCase):

    def test_01_fear_and_greed_engine(self):
        """Test Fear & Greed fetch, 7-day history, and contrarian signal."""
        fng = sentiment_narrative_scanner.get_fear_and_greed_index()
        self.assertIn("score", fng)
        self.assertIn("classification", fng)
        self.assertIn("contrarian_signal", fng)
        self.assertIn("history_7d", fng)
        self.assertGreaterEqual(fng["score"], 0)
        self.assertLessEqual(fng["score"], 100)
        self.assertGreater(len(fng["history_7d"]), 0)
        print(f"\n[Test 1 PASS] Fear & Greed: {fng['score']} [{fng['classification']}] | Signal: {fng['contrarian_signal']}")

    def test_02_narrative_sector_rotation(self):
        """Test narrative sector tracking across all 6 sectors."""
        rot = sentiment_narrative_scanner.get_narrative_sector_rotation()
        self.assertIn("sectors", rot)
        self.assertEqual(len(rot["sectors"]), 6)
        self.assertIn("leading_sector", rot)
        self.assertIn("laggard_sector", rot)
        
        leader = rot["leading_sector"]
        self.assertIsNotNone(leader)
        self.assertIn("title", leader)
        self.assertIn("avg_change_24h", leader)
        print(f"[Test 2 PASS] Narrative Rotation: 6 Sectors Scanned. #1 Leader: {leader['icon']} {leader['title']} ({leader['avg_change_24h']:+.2f}%)")

    def test_03_social_virality_trending(self):
        """Test CoinGecko search trending and virality stage."""
        vir = sentiment_narrative_scanner.get_social_virality_trending()
        self.assertIn("trending_tokens", vir)
        self.assertIn("virality_stage", vir)
        self.assertIsInstance(vir["trending_tokens"], list)
        print(f"[Test 3 PASS] Social Virality: Found {len(vir['trending_tokens'])} trending tokens. Stage: {vir['virality_stage']}")

    def test_04_catalyst_sentiment_lexicon(self):
        """Test dual-engine NLP lexicon classifier for bullish and bearish catalysts."""
        bull_text = "Spot ETF officially approved by regulators; $500M institutional inflow recorded."
        res_bull = sentiment_narrative_scanner.classify_catalyst_sentiment(bull_text)
        self.assertEqual(res_bull["sentiment"], "BULLISH")
        self.assertGreaterEqual(res_bull["impact_score"], 60)

        bear_text = "Emergency exploit detected in cross-chain bridge; SEC issues subpoena following hack."
        res_bear = sentiment_narrative_scanner.classify_catalyst_sentiment(bear_text)
        self.assertEqual(res_bear["sentiment"], "BEARISH")
        self.assertGreaterEqual(res_bear["impact_score"], 60)
        print(f"[Test 4 PASS] Catalyst Classifier: Bullish ('{res_bull['sentiment']}', Impact {res_bull['impact_score']}) | Bearish ('{res_bear['sentiment']}', Impact {res_bear['impact_score']})")

    def test_05_token_narrative_and_risk_integration(self):
        """Test token narrative mapping and AI Risk Officer integration."""
        sol_info = sentiment_narrative_scanner.get_token_narrative_info("SOL")
        self.assertEqual(sol_info["symbol"], "SOL")
        self.assertEqual(sol_info["sector_key"], "SOL_L1")
        self.assertIn("sector_rank", sol_info)

        # Test pre-trade audit integration with BTC
        setup = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "price": 66000.0,
            "entry": 66000.0,
            "sl": 65200.0,
            "tp": 68400.0,
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
        self.assertIn("sentiment_narrative", audit)
        print(f"[Test 5 PASS] Token Narrative & Risk Officer Integration -> SOL Sector: {sol_info['sector_title']} | Audit Narrative Attached: {bool(audit['sentiment_narrative'])}")

if __name__ == "__main__":
    unittest.main()
