"""
Institutional Quantitative Risk Engine (QuantLib-Inspired Suite)
Inspired by Fincept Terminal & Professional Hedge Fund Risk Desks.

Calculates:
1. Value-at-Risk (VaR 95% & 99% Parametric and Historical)
2. Conditional Value-at-Risk (CVaR / Expected Shortfall - Tail Risk)
3. Sharpe Ratio & Sortino Ratio (Downside Semi-Variance)
4. Kelly Criterion Optimal Capital Sizing Formula
5. Historical Drawdown & Calmar Ratio
6. Real-Time Portfolio VaR for Active Binance Futures Positions
"""

import json
import math
import os
import sys
from datetime import datetime

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
LEDGER_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")

def load_closed_trades():
    """Loads closed trade records from the persistent ledger."""
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                trades = json.load(f)
                return trades if isinstance(trades, list) else []
        except Exception:
            return []
    return []

def compute_historical_trade_metrics(trades=None):
    """
    Computes professional quantitative performance and risk metrics
    from historical closed trade records.
    """
    if trades is None:
        trades = load_closed_trades()

    if not trades:
        return {
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "kelly_fraction": 0.0,
            "max_drawdown_usd": 0.0,
            "max_drawdown_pct": 0.0,
            "var_95_usd": 0.0,
            "var_99_usd": 0.0,
            "cvar_95_usd": 0.0
        }

    pnls = []
    wins = []
    losses = []

    for t in trades:
        net = float(t.get("net_pnl_usd", t.get("pnl_usd", 0.0)))
        pnls.append(net)
        if net > 0:
            wins.append(net)
        elif net < 0:
            losses.append(abs(net))

    n = len(pnls)
    if n == 0:
        return {}

    total_net_pnl = sum(pnls)
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / n) * 100.0 if n > 0 else 0.0

    avg_win = (sum(wins) / win_count) if win_count > 0 else 0.0
    avg_loss = (sum(losses) / loss_count) if loss_count > 0 else 0.0
    profit_factor = (sum(wins) / sum(losses)) if sum(losses) > 0 else (99.0 if sum(wins) > 0 else 0.0)

    # 1. Mean & Standard Deviation
    mean_pnl = total_net_pnl / n
    variance = sum((x - mean_pnl) ** 2 for x in pnls) / n if n > 1 else 0.0
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    # 2. Sharpe Ratio (Per trade annualized approximation assuming 250 trading periods)
    # Risk-free rate assumed at 0 for short-horizon trades
    sharpe = (mean_pnl / std_dev) * math.sqrt(min(n, 252)) if std_dev > 0 else 0.0

    # 3. Sortino Ratio (Downside deviation only)
    downside_diffs = [min(0.0, x) ** 2 for x in pnls]
    downside_variance = sum(downside_diffs) / n if n > 0 else 0.0
    downside_std = math.sqrt(downside_variance) if downside_variance > 0 else 0.0
    sortino = (mean_pnl / downside_std) * math.sqrt(min(n, 252)) if downside_std > 0 else 0.0

    # 4. Kelly Criterion Optimal Fraction
    # Kelly % = W - ((1 - W) / R) where W = Win probability, R = Win/Loss ratio
    r_ratio = (avg_win / avg_loss) if avg_loss > 0 else 1.0
    p_win = win_count / n if n > 0 else 0.0
    p_loss = 1.0 - p_win
    raw_kelly = p_win - (p_loss / r_ratio) if r_ratio > 0 else 0.0
    # Half-Kelly for hedge-fund conservatism
    half_kelly = max(0.0, min(raw_kelly * 0.5, 0.25))

    # 5. Maximum Drawdown (MDD) Peak-to-Trough
    cum_equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in pnls:
        cum_equity += p
        if cum_equity > peak:
            peak = cum_equity
        dd = peak - cum_equity
        if dd > max_dd:
            max_dd = dd

    calmar = (total_net_pnl / max_dd) if max_dd > 0 else (99.0 if total_net_pnl > 0 else 0.0)

    # 6. Historical Value-at-Risk (VaR) & Expected Shortfall (CVaR)
    # VaR 95%: 5th percentile worst loss
    # VaR 99%: 1st percentile worst loss
    sorted_pnls = sorted(pnls)
    idx_95 = max(0, int(n * 0.05))
    idx_99 = max(0, int(n * 0.01))

    var_95 = abs(min(0.0, sorted_pnls[idx_95]))
    var_99 = abs(min(0.0, sorted_pnls[idx_99]))

    # CVaR 95% (Expected Shortfall): Average of losses worse than VaR 95%
    tail_losses = [abs(x) for x in sorted_pnls[:idx_95 + 1] if x < 0]
    cvar_95 = (sum(tail_losses) / len(tail_losses)) if tail_losses else var_95

    return {
        "total_trades": n,
        "win_rate_pct": round(win_rate, 2),
        "total_pnl_usd": round(total_net_pnl, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win_usd": round(avg_win, 2),
        "avg_loss_usd": round(avg_loss, 2),
        "win_loss_ratio": round(r_ratio, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "calmar_ratio": round(calmar, 2),
        "kelly_fraction": round(half_kelly, 4),
        "kelly_percent": round(half_kelly * 100.0, 2),
        "max_drawdown_usd": round(max_dd, 2),
        "var_95_usd": round(var_95, 2),
        "var_99_usd": round(var_99, 2),
        "cvar_95_usd": round(cvar_95, 2)
    }

def compute_portfolio_var(balance_usd, active_positions, daily_volatility_pct=0.035):
    """
    Computes real-time Parametric Value-at-Risk (VaR) for currently active
    Binance Futures positions based on total exposure, leverage, and volatility.
    
    VaR 95% = Portfolio Exposure * 1.645 * Daily Volatility
    VaR 99% = Portfolio Exposure * 2.326 * Daily Volatility
    CVaR 95% = Portfolio Exposure * 2.063 * Daily Volatility
    """
    if balance_usd <= 0:
        return {
            "portfolio_exposure_usd": 0.0,
            "var_95_usd": 0.0,
            "var_99_usd": 0.0,
            "cvar_95_usd": 0.0,
            "var_95_pct_of_capital": 0.0,
            "risk_status": "NORMAL"
        }

    total_exposure = 0.0
    for p in (active_positions or []):
        size = abs(float(p.get("positionAmt", p.get("size", 0.0))))
        mark_price = float(p.get("markPrice", p.get("entry_price", 0.0)))
        notional = abs(float(p.get("notional", size * mark_price)))
        total_exposure += notional

    # Parametric Z-scores for Normal Distribution
    Z_95 = 1.6449
    Z_99 = 2.3263
    ES_factor = 2.0627  # Expected Shortfall multiplier for normal distribution at 95%

    var_95_usd = total_exposure * daily_volatility_pct * Z_95
    var_99_usd = total_exposure * daily_volatility_pct * Z_99
    cvar_95_usd = total_exposure * daily_volatility_pct * ES_factor

    var_pct_cap = (var_95_usd / balance_usd * 100.0) if balance_usd > 0 else 0.0

    if var_pct_cap >= 8.0:
        status = "CRITICAL_RISK (VaR 95% >= 8% of Balance)"
    elif var_pct_cap >= 4.0:
        status = "ELEVATED_RISK (VaR 95% >= 4% of Balance)"
    elif total_exposure > 0:
        status = "HEALTHY_ALLOCATION"
    else:
        status = "CASH_PRESERVED"

    return {
        "portfolio_exposure_usd": round(total_exposure, 2),
        "var_95_usd": round(var_95_usd, 2),
        "var_99_usd": round(var_99_usd, 2),
        "cvar_95_usd": round(cvar_95_usd, 2),
        "var_95_pct_of_capital": round(var_pct_cap, 2),
        "risk_status": status
    }

def get_full_quant_risk_summary(balance_usd=1000.0, active_positions=None):
    """
    Synthesizes historical quant performance + live portfolio VaR
    into a complete Fincept-grade risk report.
    """
    hist = compute_historical_trade_metrics()
    port = compute_portfolio_var(balance_usd, active_positions)

    return {
        "historical": hist,
        "portfolio_var": port,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    print("\n=======================================================")
    print("      📐 INSTITUTIONAL QUANT RISK ENGINE (FINCEPT SUITE)")
    print("=======================================================")

    summary = get_full_quant_risk_summary(balance_usd=1000.0, active_positions=[])
    h = summary["historical"]
    p = summary["portfolio_var"]

    print(f"Total Ledger Trades  : {h.get('total_trades', 0)}")
    print(f"Historical Win Rate  : {h.get('win_rate_pct', 0.0)}%")
    print(f"Profit Factor        : {h.get('profit_factor', 0.0)}")
    print(f"Sharpe Ratio         : {h.get('sharpe_ratio', 0.0)}")
    print(f"Sortino Ratio        : {h.get('sortino_ratio', 0.0)}")
    print(f"Max Drawdown (Hist)  : ${h.get('max_drawdown_usd', 0.0):,.2f}")
    print(f"Calmar Ratio         : {h.get('calmar_ratio', 0.0)}")
    print(f"Historical VaR (95%) : ${h.get('var_95_usd', 0.0):,.2f}")
    print(f"Historical VaR (99%) : ${h.get('var_99_usd', 0.0):,.2f}")
    print(f"Expected Shortfall   : ${h.get('cvar_95_usd', 0.0):,.2f} (Tail Risk CVaR 95%)")
    print(f"Kelly Sizing Factor  : {h.get('kelly_percent', 0.0)}% (Half-Kelly Optimal Risk)")
    print("-------------------------------------------------------")
    print(f"Active Exposure      : ${p.get('portfolio_exposure_usd', 0.0):,.2f}")
    print(f"Portfolio VaR (95%)  : ${p.get('var_95_usd', 0.0):,.2f} ({p.get('var_95_pct_of_capital', 0.0)}% of Capital)")
    print(f"Portfolio CVaR (95%) : ${p.get('cvar_95_usd', 0.0):,.2f}")
    print(f"Risk Status          : {p.get('risk_status')}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
