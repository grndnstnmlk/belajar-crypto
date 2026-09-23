"""
monte_carlo_engine.py - Unified Monte Carlo Resilience & Parkinson Volatility Engine
Inspired by Mehul Mehta (@quantguy_usa) Institutional Quantitative Risk Framework
& Akademi Crypto Module 01 (Fundamental Macro) & Module 03 (Money Management).

Formulas Implemented:
1. Parkinson Historical Volatility:
   sigma_parkinson = sqrt( (1 / (4 * ln(2) * N)) * sum( (ln(H_i / L_i))^2 ) )
   Standard deviation on Close is blind to liquidation wicks. Parkinson captures
   the extreme High-Low span to prevent stop-loss hunting (wick traps).
2. Parametric VaR 95% from Parkinson Volatility:
   VaR_95 = sigma_parkinson * 1.6449
3. 1,000-Path Monte Carlo Bootstrap Simulation for Tail Drawdown & Probability of Ruin.
4. Dynamic Volatility-Adjusted Risk Haircut.
"""

import math
import os
import sys
from typing import Dict, Any, List, Optional

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import core simulation routines from monte_carlo_risk_simulator
from monte_carlo_risk_simulator import (
    run_monte_carlo_simulation,
    load_trade_pnls,
    CACHE_FILE,
    LEDGER_FILE,
    DATA_DIR
)

# Import quant risk engine functions
from quant_risk_engine import (
    calculate_parkinson_volatility,
    calculate_parkinson_wick_shield,
    compute_portfolio_var,
    compute_historical_trade_metrics,
    calculate_kelly_criterion
)

def calculate_parkinson_var_95(highs: List[float], lows: List[float], confidence: float = 0.95) -> Dict[str, float]:
    """
    Computes Parkinson Volatility and Parametric VaR (Value-at-Risk) at 95% and 99%:
    sigma_parkinson = sqrt( 1 / (4 * ln(2) * N) * sum((ln(H_i / L_i))^2) )
    VaR_95 = sigma_parkinson * 1.6449
    VaR_99 = sigma_parkinson * 2.3263
    """
    sigma_p = calculate_parkinson_volatility(highs, lows)
    z_score = 1.6449 if confidence == 0.95 else (2.3263 if confidence == 0.99 else 1.6449)
    var_pct = sigma_p * z_score * 100.0
    var_99_pct = sigma_p * 2.3263 * 100.0
    cvar_95_pct = sigma_p * 2.0627 * 100.0

    return {
        "parkinson_volatility_pct": round(sigma_p * 100.0, 3),
        "var_95_pct": round(var_pct, 2),
        "var_99_pct": round(var_99_pct, 2),
        "cvar_95_pct": round(cvar_95_pct, 2),
        "safe_wick_buffer_pct": round(max(0.8, min(5.0, sigma_p * 1.2 * 100.0)), 2)
    }

def run_volatility_calibrated_monte_carlo(
    symbol: str = "BTCUSDT",
    starting_equity: float = 5000.0,
    base_risk_pct: float = 2.0,
    iterations: int = 1000,
    horizon_trades: int = 50,
    candles: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Integrates 1,000-Path Monte Carlo Bootstrap Simulation with Parkinson Volatility:
    1. Runs Monte Carlo trade path simulation to obtain 95% VaR Max Drawdown.
    2. Calculates Parkinson Historical Volatility (High-Low range) for the asset.
    3. If Parkinson volatility shows severe turbulence (wick expansion > 3.0%),
       applies an additional protective risk haircut to protect capital.
    """
    base_sim = run_monte_carlo_simulation(
        iterations=iterations,
        horizon_trades=horizon_trades,
        starting_equity=starting_equity,
        base_risk_pct=base_risk_pct
    )

    highs, lows = [], []
    if candles and isinstance(candles, list):
        for c in candles:
            if isinstance(c, dict):
                highs.append(float(c.get("high", c.get("h", 0))))
                lows.append(float(c.get("low", c.get("l", 0))))

    if len(highs) < 5:
        try:
            import market_eyes
            c_data = market_eyes.fetch_candles(symbol, bar="1h", limit=30)
            if c_data:
                for c in c_data:
                    highs.append(float(c["high"]))
                    lows.append(float(c["low"]))
        except Exception:
            pass

    parkinson_metrics = calculate_parkinson_var_95(highs, lows)
    sigma_p_pct = parkinson_metrics["parkinson_volatility_pct"]
    safe_buffer = parkinson_metrics["safe_wick_buffer_pct"]

    # Calibrate risk multiplier based on combined Monte Carlo VaR and Parkinson Volatility
    rec_mult = base_sim.get("recommended_risk_multiplier", 1.0)
    if sigma_p_pct >= 4.0:
        rec_mult = min(rec_mult, 0.50)  # Extreme volatility / liquidation cascades
        vol_status = "🔴 HIGH VOLATILITY / LIQUIDATION CASCADE (Parkinson Vol >= 4.0%)"
    elif sigma_p_pct >= 2.5:
        rec_mult = min(rec_mult, 0.75)  # Elevated market noise
        vol_status = "🟡 ELEVATED VOLATILITY NOISE (Parkinson Vol >= 2.5%)"
    else:
        vol_status = "🟢 CALM / ORDERLY REGIME (Parkinson Vol < 2.5%)"

    eff_risk = round(base_risk_pct * rec_mult, 2)

    return {
        "symbol": symbol.upper(),
        "starting_equity": starting_equity,
        "base_risk_pct": base_risk_pct,
        "effective_risk_pct": eff_risk,
        "recommended_risk_multiplier": rec_mult,
        "regime_status": base_sim.get("regime_status"),
        "volatility_status": vol_status,
        "parkinson_metrics": parkinson_metrics,
        "monte_carlo_simulation": base_sim,
        "wick_trap_safe_buffer_pct": safe_buffer
    }

if __name__ == "__main__":
    print("=======================================================")
    print("  🎲 MONTE CARLO & PARKINSON VOLATILITY ENGINE")
    print("=======================================================")
    res = run_volatility_calibrated_monte_carlo("BTCUSDT", starting_equity=5000.0, base_risk_pct=2.0)
    print(f"Symbol                  : {res['symbol']}")
    print(f"Starting Equity         : ${res['starting_equity']:,.2f}")
    print(f"Parkinson Volatility    : {res['parkinson_metrics']['parkinson_volatility_pct']}%")
    print(f"Parkinson VaR 95%       : {res['parkinson_metrics']['var_95_pct']}%")
    print(f"Wick Trap Safe Buffer   : {res['wick_trap_safe_buffer_pct']}%")
    print(f"Monte Carlo 95% VaR DD  : {res['monte_carlo_simulation']['var_95_max_drawdown_pct']}%")
    print(f"Probability of Ruin     : {res['monte_carlo_simulation']['prob_of_ruin_20pct']}%")
    print(f"Effective Risk per Trade: {res['effective_risk_pct']}% ({res['volatility_status']})")
    print("=======================================================")
