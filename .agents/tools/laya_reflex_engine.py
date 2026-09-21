"""
laya_reflex_engine.py - Sub-35ms Non-Autoregressive System 1 Decision Engine
Synthesized for Belajar Kripto Workstation using Laya (ModernBERT-based encoder).

Capabilities:
1. Ultra-Low Latency Decision Gating (< 35ms):
   - Fast pre-execution vetting before sending orders to Binance Futures Testnet.
   - Categorizes trade setups (APPROVE, REQUIRE_CONFIRMATION, REJECT_RISK).
2. Institutional News & Headline Sentiment Classification:
   - Instant zero-shot classification of crypto headlines (BULLISH, BEARISH, NEUTRAL).
   - Gauges market impact (negligible to black swan) and regulatory risk.
3. Zero-Downtime Non-Blocking Architecture:
   - Model download and preload runs strictly in a background daemon thread.
   - Never blocks HTTP requests or trading loops.
   - Instant (< 1ms) quant reflex fallback while model is loading or if offline.
"""

import os
import sys
import time
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger("LayaReflexEngine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_ROUTER_INSTANCE = None
_ROUTER_READY = False
_INIT_STARTED = False
_INIT_ERROR = None
_INIT_LOCK = threading.Lock()


def _async_load_laya():
    """Background worker to download and preload Laya Router without blocking main threads."""
    global _ROUTER_INSTANCE, _ROUTER_READY, _INIT_ERROR
    try:
        import laya
        logger.info("Starting background preload of Laya Router...")
        r = laya.Router(preload=False)
        # Attempt to preload the english checkpoint in background
        r.preload(["english"])
        _ROUTER_INSTANCE = r
        _ROUTER_READY = True
        logger.info("Laya Router successfully preloaded and ready for sub-35ms inference.")
    except Exception as exc:
        _INIT_ERROR = str(exc)
        logger.warning("Background Laya preload failed: %s. Remaining on quant fallback.", exc)


def start_laya_background_init():
    """Triggers background initialization of Laya if not already started."""
    global _INIT_STARTED
    with _INIT_LOCK:
        if not _INIT_STARTED:
            _INIT_STARTED = True
            t = threading.Thread(target=_async_load_laya, daemon=True, name="LayaBgInit")
            t.start()


def get_laya_status() -> Dict[str, Any]:
    """
    Returns the current operational status of the Laya Reflex Engine.
    """
    global _ROUTER_INSTANCE, _ROUTER_READY, _INIT_ERROR
    try:
        import laya
        is_installed = True
        version = getattr(laya, "__version__", "unknown")
    except ImportError:
        is_installed = False
        version = None

    loaded_models = []
    if _ROUTER_INSTANCE is not None:
        try:
            loaded_models = list(_ROUTER_INSTANCE.loaded) if hasattr(_ROUTER_INSTANCE, "loaded") else []
        except Exception:
            pass

    return {
        "installed": is_installed,
        "version": version,
        "ready": _ROUTER_READY,
        "loaded_models": loaded_models,
        "default_models": ["convaiinnovations/laya"],
        "latency_target": "<35ms",
        "error": _INIT_ERROR
    }


def vet_trade_setup(
    symbol: str,
    side: str,
    timeframe: str,
    rr_ratio: float,
    confluence_notes: str,
    market_regime: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a sub-35ms System 1 vetting on a trade candidate before execution.
    Questions:
    - action: APPROVE, WAIT_CONFIRMATION, REJECT_RISK
    - confidence: low, medium, high, institutional_grade
    - emotional_fomo: boolean
    """
    t0 = time.perf_counter()

    # Trigger background load if not started yet
    if not _INIT_STARTED:
        start_laya_background_init()

    # If Laya router is fully loaded and ready, use it
    if _ROUTER_READY and _ROUTER_INSTANCE is not None:
        try:
            state_prompt = (
                f"Trade Candidate: {symbol} {side.upper()} on {timeframe}. "
                f"Risk-to-Reward: {rr_ratio:.2f}R. "
                f"Market Regime: {market_regime or 'Adaptive'}. "
                f"Confluence & Technical Context: {confluence_notes}"
            )

            questions = {
                "action": {
                    "type": "choice",
                    "instructions": "What is the correct execution decision for this trade candidate?",
                    "criteria": {
                        "APPROVE": "High-confluence setup with favorable R:R aligned with HTF bias.",
                        "WAIT_CONFIRMATION": "Promising setup but requires level-2 orderbook or retest confirmation.",
                        "REJECT_RISK": "Poor R:R, counter-trend, chasing extended price, or excessive risk."
                    }
                },
                "confidence": {
                    "type": "score",
                    "instructions": "How strong is the institutional confluence of this setup?",
                    "criteria": [
                        "low: weak confluence or conflicting indicators",
                        "medium: standard breakout or pullback setup",
                        "high: multi-timeframe alignment with SMC structure",
                        "institutional_grade: top-tier orderbook absorption and macro trend alignment"
                    ]
                },
                "emotional_fomo": {
                    "type": "noul",
                    "instructions": "Does the trade candidate describe chasing extended candles or emotional FOMO?"
                }
            }

            prediction = _ROUTER_INSTANCE.predict(state_prompt, questions)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "engine": "laya_modernbert",
                "symbol": symbol,
                "side": side.upper(),
                "decision": prediction.get("action", {}).get("choice", "APPROVE"),
                "confidence": prediction.get("confidence", {}).get("score", 2),
                "is_fomo": prediction.get("emotional_fomo", {}).get("noul", False),
                "raw_result": prediction,
                "latency_ms": round(latency_ms, 2),
                "status": "success"
            }
        except Exception as exc:
            logger.warning("Laya inference error: %s. Using quant fallback.", exc)

    # Deterministic Quant Fallback (< 1ms)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    side_u = side.upper()
    is_fomo = "fomo" in confluence_notes.lower() or "chasing" in confluence_notes.lower()
    
    if is_fomo or rr_ratio < 1.5:
        decision = "REJECT_RISK"
        conf = 0
    elif rr_ratio >= 3.0:
        decision = "APPROVE"
        conf = 3
    else:
        decision = "WAIT_CONFIRMATION" if rr_ratio < 2.0 else "APPROVE"
    # Integrate TypeSafe Jev AI Microstructure Decision as quantitative edge
    jev_summary = None
    try:
        import jev_trader_adapter
        jev_data = jev_trader_adapter.evaluate_jev_decision(symbol)
        if jev_data and "decision" in jev_data:
            jev_action = jev_data["decision"].get("action", "").lower()
            jev_conviction = jev_data.get("conviction", "")
            jev_summary = jev_data.get("summary")
            # If Jev strongly opposes trade direction, demote to WAIT_CONFIRMATION
            if (side_u in ["BUY", "LONG"] and jev_action == "sell" and jev_conviction == "HIGH_BEARISH"):
                if decision == "APPROVE":
                    decision = "WAIT_CONFIRMATION"
            elif (side_u in ["SELL", "SHORT"] and jev_action == "buy" and jev_conviction == "HIGH_BULLISH"):
                if decision == "APPROVE":
                    decision = "WAIT_CONFIRMATION"
            elif (side_u in ["BUY", "LONG"] and jev_action == "buy" and "BULLISH" in jev_conviction):
                conf = min(3, conf + 1)
    except Exception:
        pass

    return {
        "engine": "quant_reflex_fallback",
        "symbol": symbol,
        "side": side_u,
        "decision": decision,
        "confidence": conf,
        "is_fomo": is_fomo,
        "jev_summary": jev_summary,
        "raw_result": None,
        "latency_ms": round(latency_ms, 2),
        "status": "fallback"
    }


def evaluate_jev_reflex(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Sub-35ms System 1 Jev Microstructure Evaluator.
    Synthesized from jarrodwatts/jev-trader.
    """
    import jev_trader_adapter
    return jev_trader_adapter.evaluate_jev_decision(symbol)


def classify_market_headline(headline: str, source: Optional[str] = None) -> Dict[str, Any]:
    """
    Sub-35ms classification of crypto market news headlines.
    Questions:
    - sentiment: BULLISH, BEARISH, NEUTRAL
    - impact_level: negligible, minor_volatility, major_trend_shift, black_swan
    - regulatory_threat: boolean
    """
    t0 = time.perf_counter()

    # Trigger background load if not started yet
    if not _INIT_STARTED:
        start_laya_background_init()

    if _ROUTER_READY and _ROUTER_INSTANCE is not None:
        try:
            state_prompt = f"Crypto Market Headline: {headline} (Source: {source or 'Wire'})"

            questions = {
                "sentiment": {
                    "type": "choice",
                    "instructions": "What is the price sentiment impact of this crypto news headline?",
                    "criteria": {
                        "BULLISH": "Positive for crypto prices, adoption, ETF inflows, or institutional interest.",
                        "BEARISH": "Negative for crypto prices, hacks, outflows, liquidations, or regulatory crackdown.",
                        "NEUTRAL": "Informational, mixed, or routine operational update with no clear price bias."
                    }
                },
                "impact_level": {
                    "type": "score",
                    "instructions": "How significant is the market impact of this news?",
                    "criteria": [
                        "negligible: routine noise or trivial update",
                        "minor_volatility: brief intraday reaction",
                        "major_trend_shift: multi-day/week institutional trend driver",
                        "black_swan: systemic liquidation crisis or emergency macro event"
                    ]
                },
                "regulatory_threat": {
                    "type": "noul",
                    "instructions": "Does this headline report regulatory enforcement, SEC lawsuits, or government bans?"
                }
            }

            prediction = _ROUTER_INSTANCE.predict(state_prompt, questions)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "engine": "laya_modernbert",
                "headline": headline,
                "sentiment": prediction.get("sentiment", {}).get("choice", "NEUTRAL"),
                "impact_level": prediction.get("impact_level", {}).get("score", 0),
                "is_regulatory_threat": prediction.get("regulatory_threat", {}).get("noul", False),
                "raw_result": prediction,
                "latency_ms": round(latency_ms, 2),
                "status": "success"
            }
        except Exception as exc:
            logger.warning("Laya headline inference error: %s. Using quant fallback.", exc)

    # Heuristic Quant Fallback (< 1ms)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    hl_lower = headline.lower()
    bullish_keywords = ["etf", "inflow", "approval", "surge", "breakout", "rally", "accumulat", "ath", "all-time high"]
    bearish_keywords = ["hack", "exploit", "outflow", "sec", "lawsuit", "ban", "crackdown", "plunge", "liquidation", "fraud"]

    is_reg = any(w in hl_lower for w in ["sec", "lawsuit", "sue", "ban", "crackdown", "subpoena", "cftc"])
    
    if any(w in hl_lower for w in bearish_keywords):
        sentiment = "BEARISH"
        impact = 2 if is_reg else 1
    elif any(w in hl_lower for w in bullish_keywords):
        sentiment = "BULLISH"
        impact = 2 if "etf" in hl_lower or "approval" in hl_lower else 1
    else:
        sentiment = "NEUTRAL"
        impact = 0

    return {
        "engine": "quant_reflex_fallback",
        "headline": headline,
        "sentiment": sentiment,
        "impact_level": impact,
        "is_regulatory_threat": is_reg,
        "raw_result": None,
        "latency_ms": round(latency_ms, 2),
        "status": "fallback"
    }


if __name__ == "__main__":
    print("=== Testing Laya Reflex Engine (Non-blocking) ===")
    print("Status:", get_laya_status())
    
    print("\n1. Testing Trade Setup Vetting:")
    res_trade = vet_trade_setup("BTCUSDT", "LONG", "4H", 3.2, "Broke above 4H resistance with +1800 BTC CVD absorption and EMA50 support.")
    print("Result:", res_trade)

    print("\n2. Testing Headline Classification:")
    res_news = classify_market_headline("US SEC approves first multi-crypto index ETF with $500M day-one inflows.")
    print("Result:", res_news)
