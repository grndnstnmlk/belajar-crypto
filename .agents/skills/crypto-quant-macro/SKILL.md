---
name: crypto-quant-macro
description: Quantitative Time-Series Volatility Estimator & Global Macroeconomic Liquidity Intelligence skill synthesized from K-Dense Scientific Agent Skills and Akademi Crypto Module 01 (Fundamental Macro) & Module 03 (Money Management). Computes Parkinson volatility, Value-at-Risk (VaR 95%/99%), Conditional VaR (Expected Shortfall), US 10Y Yield, Dollar Index (DXY), and Federal Reserve Net Liquidity regime.
metadata:
  version: "1.0.0"
  author: "Belajar Kripto Quant Research"
  tags:
    - quantitative
    - macro-economics
    - timesfm
    - risk-management
    - volatility-modeling
---

# Crypto Quant & Global Macro Intelligence Skill

## Overview
This skill provides scientific, evidence-traceable macroeconomic liquidity tracking and quantitative time-series volatility modeling for crypto assets.

## Core Capabilities
1. **Global Macroeconomic Liquidity Intelligence (`fred_macro_intel.py`)**:
   - Tracks Dollar Index (DXY), US 10-Year Treasury Yield, and Federal Reserve Net Liquidity.
   - Outputs regime codes: `HIGH_LIQUIDITY_BULLISH`, `MONETARY_TIGHTENING_DEFENSIVE`, `NEUTRAL_EXPANSIONARY`.
   - Modulates trading sizing with a macro multiplier (0.85x – 1.20x).

2. **Statistical Time-Series & Volatility Estimator (`timeseries_quant_forecaster.py`)**:
   - **Parkinson High-Low Volatility**: Continuous price-path volatility estimation superior to close-to-close metrics.
   - **Value-at-Risk (VaR 95% & 99%)**: Parametric tail-risk estimation.
   - **Conditional VaR (Expected Shortfall)**: Average loss beyond the 95th percentile threshold.
   - **Dynamic SL Buffer**: Calibrates structural stop-loss buffers based on live volatility regimes.

## Usage in Trading Pipeline
- Integrated into **Pilar 2 (`nautilus_risk_engine.py`)** to scale position risk defensively during wild volatility expansion and boost sizing during quiet liquidity expansions.
- Exposes REST endpoints:
  - `GET /api/macro/fred`
  - `GET /api/quant/volatility?symbol=BTC&bar=1h`
