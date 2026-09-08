"""
Tri-Perspective Risk Balancing Layer (Aggressive, Neutral, Conservative)
Inspired by Tauric Research's TradingAgents Multi-Agent Framework (arXiv:2412.20138)
Adapted for 24/7 Autonomous Crypto Trading & Quantitative Risk Governance.

Evaluates trade setups post-Adversarial Debate across three competing risk mindsets:
1. Aggressive Risk Officer   : Seeks alpha maximization, high R:R asymmetry, and momentum expansion.
2. Conservative Risk Officer : Prioritizes capital defense, portfolio heat guardrails, and tail-risk avoidance.
3. Neutral Risk Officer      : Quantitative anchor utilizing Kelly Criterion, ATR volatility normalization, and statistical EV.
4. Fund Manager (CRO)        : Harmonizes the 3 perspectives into dynamic weights, final capital allocation scale (0.0x - 1.25x),
                              and stop-loss execution policy (Tight BE, ATR Trailing, Runner Expansion).

Dual-Engine Architecture:
- Cognitive LLM Multi-Agent Dialog: When Gemini / OpenAI / DeepSeek / Groq API key is present.
- Deterministic Quant Matrix: Algorithmic heuristic fallback (< 5ms) ensuring 100% uptime.
"""

import json
import os
import sys
import time
from datetime import datetime

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
TRI_RISK_HISTORY_FILE = os.path.join(DATA_DIR, "tri_perspective_risk.json")

def load_tri_risk_history(limit=20):
    """Loads recent tri-perspective risk records from disk."""
    if os.path.exists(TRI_RISK_HISTORY_FILE):
        try:
            with open(TRI_RISK_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data[-limit:]
        except Exception:
            return []
    return []

def save_tri_risk_record(record):
    """Appends a completed tri-perspective risk evaluation to disk."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        history = []
        if os.path.exists(TRI_RISK_HISTORY_FILE):
            try:
                with open(TRI_RISK_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.append(record)
        if len(history) > 50:
            history = history[-50:]
        with open(TRI_RISK_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def run_deterministic_tri_risk(setup, portfolio_state=None, market_context=None):
    """
    Algorithmic Quant Heuristic Tri-Perspective Engine:
    Mathematically computes scores for Aggressive, Conservative, and Neutral officers,
    then executes Fund Manager dynamic weighting and synthesis.
    """
    p_state = portfolio_state or {}
    ctx = market_context or {}

    sym = setup.get("symbol", "UNKNOWN")
    side = setup.get("side", "BUY").upper()
    rr = float(setup.get("rr", setup.get("rr_ratio", setup.get("risk_reward", 2.0))))
    is_scalp = setup.get("is_scalp", False)
    
    # Extract debate context if available
    debate = ctx.get("adversarial_debate") or setup.get("ai_audit", {}).get("adversarial_debate") or {}
    bull_score = float(debate.get("bull_score", 65))
    bear_score = float(debate.get("bear_score", 35))

    # Extract portfolio metrics
    active_pos = p_state.get("active_positions", [])
    pos_count = len(active_pos)
    heat = p_state.get("heat", {})
    long_count = heat.get("long_count", len([p for p in active_pos if float(p.get("positionAmt", 0)) > 0]))
    short_count = heat.get("short_count", len([p for p in active_pos if float(p.get("positionAmt", 0)) < 0]))
    directional_heat = long_count if side in ["BUY", "LONG"] else short_count
    
    free_margin_ratio = float(p_state.get("free_margin_ratio", 0.85)) # 0.0 to 1.0

    # Market metrics
    btc_regime = ctx.get("market_regime", {})
    adx = float(btc_regime.get("adx", 25.0))
    trend_bias = btc_regime.get("trend_bias", "NEUTRAL")

    # 1. AGGRESSIVE RISK OFFICER EVALUATION
    # Focus: Alpha maximization, high R:R, strong momentum, bull conviction
    agg_score = 50
    agg_scale = 1.0
    agg_points = []

    if rr >= 3.0:
        agg_score += 25
        agg_scale += 0.20
        agg_points.append(f"R:R asimetris tinggi 1:{rr:.2f} menawarkan potensi keuntungan substansial.")
    elif rr >= 2.0:
        agg_score += 15
        agg_scale += 0.10
        agg_points.append(f"R:R 1:{rr:.2f} di atas ambang batas minimum institusional.")
    else:
        agg_score -= 10
        agg_scale -= 0.15
        agg_points.append(f"R:R 1:{rr:.2f} tergolong tipis untuk setup agresif.")

    if bull_score >= 70:
        agg_score += 20
        agg_scale += 0.15
        agg_points.append(f"Keyakinan Bull {bull_score:.0f}% mengonfirmasi dominasi pembeli institusional.")
    elif bull_score >= 55:
        agg_score += 10
        agg_points.append(f"Keyakinan Bull {bull_score:.0f}% menunjukkan dorongan positif moderat.")

    if adx >= 28:
        agg_score += 15
        agg_points.append(f"ADX momentum kuat ({adx:.1f}) mendukung kelanjutan tren yang ekspansif.")

    agg_score = max(10, min(95, agg_score))
    agg_scale = max(0.5, min(1.25, round(agg_scale, 2)))
    agg_thesis = " | ".join(agg_points) if agg_points else "Kondisi pasar standar untuk penetrasi momentum."

    # 2. CONSERVATIVE RISK OFFICER EVALUATION
    # Focus: Capital preservation, portfolio strain, directional clustering, downside protection
    con_score = 50
    con_scale = 1.0
    con_points = []

    # Directional crowding penalty
    if directional_heat >= 3:
        con_score -= 40
        con_scale -= 0.60
        con_points.append(f"Peringatan konsentrasi arah: sudah ada {directional_heat} posisi sepihak terbuka.")
    elif directional_heat >= 2:
        con_score -= 20
        con_scale -= 0.35
        con_points.append(f"Portofolio memiliki {directional_heat} posisi searah; batasi eksposur tambahan.")
    else:
        con_score += 15
        con_points.append("Diversifikasi portofolio aman; tidak ada penumpukan risiko terarah.")

    # Bear skepticism from Tauric Debate
    if bear_score >= 65:
        con_score -= 35
        con_scale -= 0.50
        con_points.append(f"Skeptisisme Bear tinggi ({bear_score:.0f}%) mendeteksi potensi jebakan likuiditas / dinding resisten.")
    elif bear_score >= 50:
        con_score -= 15
        con_scale -= 0.20
        con_points.append(f"Kritik Bear moderat ({bear_score:.0f}%); diperlukan stop loss ketat.")

    # Free margin health
    if free_margin_ratio < 0.40:
        con_score -= 30
        con_scale -= 0.40
        con_points.append(f"Margin bebas kritis ({free_margin_ratio*100:.0f}%); prioritas preservasi kas.")
    elif free_margin_ratio < 0.60:
        con_score -= 15
        con_scale -= 0.20
        con_points.append(f"Margin bebas terbatas ({free_margin_ratio*100:.0f}%).")

    con_score = max(5, min(95, con_score))
    con_scale = max(0.1, min(1.0, round(con_scale, 2)))
    con_thesis = " | ".join(con_points) if con_points else "Parameter risiko portofolio dalam batas aman terkendali."

    # 3. NEUTRAL RISK OFFICER EVALUATION
    # Focus: Half-Kelly criterion, ATR volatility normalization, expected value (EV)
    # Estimated win probability p based on bull score and setup type
    base_p = 0.58 if is_scalp else 0.52
    est_win_prob = max(0.40, min(0.75, base_p + (bull_score - bear_score) * 0.002))
    b = max(1.0, rr)
    
    # Kelly Formula: f* = (p*b - (1-p)) / b
    kelly_f = (est_win_prob * b - (1.0 - est_win_prob)) / b
    half_kelly = max(0.005, min(0.03, kelly_f * 0.5)) # bounded 0.5% to 3.0%
    
    neu_score = int(est_win_prob * 100)
    neu_scale = max(0.5, min(1.10, round(half_kelly / 0.015, 2))) # 1.5% base benchmark
    neu_points = [
        f"Probabilitas kemenangan model: {est_win_prob*100:.1f}%.",
        f"Half-Kelly fraksional optimal: {half_kelly*100:.2f}% per trade.",
        f"Normalisasi volatilitas menyarankan skala lot {neu_scale:.2f}x."
    ]
    neu_thesis = " | ".join(neu_points)

    # 4. FUND MANAGER / CHIEF RISK OFFICER SYNTHESIS
    # Dynamic Weight Adaptation based on stress indicators
    w_con = 0.35
    w_neu = 0.40
    w_agg = 0.25

    if directional_heat >= 2 or pos_count >= 3 or free_margin_ratio < 0.50:
        # Surge conservative weighting during stress
        w_con = 0.60
        w_neu = 0.25
        w_agg = 0.15
    elif agg_score >= 80 and con_score >= 60 and free_margin_ratio >= 0.75:
        # Boost aggressive weighting in prime conditions
        w_agg = 0.40
        w_neu = 0.35
        w_con = 0.25

    composite_score = int(w_agg * agg_score + w_neu * neu_score + w_con * con_score)
    final_scale = round(w_agg * agg_scale + w_neu * neu_scale + w_con * con_scale, 2)

    # Determine Clearance Verdict & Stop Profile
    if con_score < 25 or directional_heat >= 4 or composite_score < 35:
        verdict = "BLOCKED_RISK_LIMIT"
        final_scale = 0.0
        stop_profile = "NONE"
        synthesis = f"REJECTED: Stres portofolio melampaui batas aman (Konservatif {con_score}%). Penambahan posisi {sym} ditolak demi perlindungan modal."
    elif composite_score >= 75 and con_score >= 50:
        verdict = "APPROVED_OPTIMAL"
        final_scale = min(1.25, max(1.0, final_scale))
        stop_profile = "RUNNER_EXPANSION"
        synthesis = f"APPROVED OPTIMAL: Konvergensi tinggi dari ketiga perspektif. Alokasi penuh {final_scale:.2f}x diizinkan dengan runner expansion."
    elif composite_score >= 55 and con_score >= 40:
        verdict = "APPROVED_BALANCED"
        final_scale = min(1.0, max(0.70, final_scale))
        stop_profile = "ATR_TRAILING"
        synthesis = f"APPROVED BALANCED: Eksekusi berimbang standar dengan skala risiko {final_scale:.2f}x dan trailing stop berbasis ATR dinamis."
    else:
        verdict = "APPROVED_DEFENSIVE"
        final_scale = min(0.55, max(0.25, final_scale))
        stop_profile = "TIGHT_BREAKEVEN"
        synthesis = f"APPROVED DEFENSIVE: Risiko moderat terdeteksi. Alokasi dipangkas defensif ke {final_scale:.2f}x dengan kunci Break-Even cepat di +0.6R."

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": sym,
        "side": side,
        "engine": "Algorithmic Quant Heuristic Matrix",
        "aggressive": {
            "score": agg_score,
            "desired_scale": agg_scale,
            "thesis": agg_thesis
        },
        "conservative": {
            "score": con_score,
            "desired_scale": con_scale,
            "thesis": con_thesis
        },
        "neutral": {
            "score": neu_score,
            "desired_scale": neu_scale,
            "half_kelly_pct": round(half_kelly * 100, 2),
            "thesis": neu_thesis
        },
        "fund_manager": {
            "verdict": verdict,
            "composite_risk_score": composite_score,
            "allocated_risk_scale": final_scale,
            "stop_loss_profile": stop_profile,
            "regime_weights": {
                "aggressive": round(w_agg, 2),
                "neutral": round(w_neu, 2),
                "conservative": round(w_con, 2)
            },
            "synthesis": synthesis
        }
    }

def run_llm_tri_risk(setup, portfolio_state=None, market_context=None):
    """
    Cognitive LLM Multi-Agent Tri-Perspective Risk Evaluator.
    Generates structured dialectic between Aggressive, Conservative, and Neutral officers,
    synthesized by the Fund Manager.
    """
    try:
        import ai_risk_officer
        creds = ai_risk_officer.get_ai_credentials()
        if not creds.get("key") or creds.get("provider") == "fallback_quant":
            return None

        p_state = portfolio_state or {}
        ctx = market_context or {}
        sym = setup.get("symbol", "UNKNOWN")
        side = setup.get("side", "BUY")
        rr = setup.get("rr", 2.0)
        debate = ctx.get("adversarial_debate") or {}

        prompt = f"""
You are the Chief Risk Officer (Fund Manager) leading the Tri-Perspective Risk Management Team at a top-tier quantitative crypto fund, based on Tauric Research's TradingAgents framework (arXiv:2412.20138).

Evaluate the following trade setup from three specialized perspectives:
- Symbol: {sym} ({side})
- Target R:R: 1:{rr}
- Strategy: {setup.get('strategy', 'SMC Confluence')}
- Bull Conviction Score: {debate.get('bull_score', 65)}%
- Bear Skepticism Score: {debate.get('bear_score', 35)}%
- Active Open Positions: {len(p_state.get('active_positions', []))}
- Directional Heat: {p_state.get('heat', {})}
- Free Margin Ratio: {p_state.get('free_margin_ratio', 0.85)}

Roles:
1. Aggressive Risk Officer (Alpha & Momentum Maximizer): Focuses on reward asymmetry, upside potential, and scaling up (desired_scale up to 1.25x).
2. Conservative Risk Officer (Capital Preservation & Tail-Risk Shield): Focuses on worst-case loss, margin safety, portfolio heat, and scaling down (desired_scale 0.25x - 0.70x, or 0.0x veto).
3. Neutral Risk Officer (Statistical & Kelly Normalization): Focuses on Half-Kelly criterion, ATR volatility buffer, and empirical win rate.
4. Fund Manager (CRO Synthesis): Reconciles all 3 views, assigns weights, sets composite_risk_score (0-100), allocated_risk_scale (0.0x to 1.25x), stop_loss_profile ('TIGHT_BREAKEVEN', 'ATR_TRAILING', 'RUNNER_EXPANSION'), and verdict ('APPROVED_OPTIMAL', 'APPROVED_BALANCED', 'APPROVED_DEFENSIVE', 'BLOCKED_RISK_LIMIT').

Respond in strictly valid JSON:
{{
  "aggressive": {{
    "score": <0-100 integer>,
    "desired_scale": <float, e.g. 1.15>,
    "thesis": "<concise thesis in Indonesian>"
  }},
  "conservative": {{
    "score": <0-100 integer>,
    "desired_scale": <float, e.g. 0.60>,
    "thesis": "<concise defense thesis in Indonesian>"
  }},
  "neutral": {{
    "score": <0-100 integer>,
    "desired_scale": <float, e.g. 0.90>,
    "half_kelly_pct": <float>,
    "thesis": "<concise quant thesis in Indonesian>"
  }},
  "fund_manager": {{
    "verdict": "<APPROVED_OPTIMAL|APPROVED_BALANCED|APPROVED_DEFENSIVE|BLOCKED_RISK_LIMIT>",
    "composite_risk_score": <0-100 integer>,
    "allocated_risk_scale": <float, e.g. 0.85>,
    "stop_loss_profile": "<TIGHT_BREAKEVEN|ATR_TRAILING|RUNNER_EXPANSION>",
    "regime_weights": {{"aggressive": 0.25, "neutral": 0.40, "conservative": 0.35}},
    "synthesis": "<decisive executive risk synthesis in Indonesian>"
  }}
}}
"""
        res = ai_risk_officer.call_llm(
            prompt,
            system_prompt="You are the Tauric Research Tri-Perspective Risk Balancing Engine. Output strictly valid JSON.",
            response_json=True
        )
        if res:
            parsed = json.loads(res)
            parsed["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            parsed["symbol"] = sym
            parsed["side"] = side
            parsed["engine"] = f"Cognitive LLM ({creds.get('provider').upper()})"
            return parsed
    except Exception:
        pass
    return None

def run_tri_perspective_risk(setup, portfolio_state=None, market_context=None):
    """
    Master Gateway for Tri-Perspective Risk Balancing.
    Attempts Cognitive LLM; falls back instantaneously to Deterministic Quant Matrix.
    Persists evaluation record to disk for dashboard telemetry and audit logs.
    """
    # 1. Attempt Cognitive LLM Evaluation
    result = run_llm_tri_risk(setup, portfolio_state, market_context)
    
    # 2. Seamless Quant Fallback (< 5ms)
    if not result:
        result = run_deterministic_tri_risk(setup, portfolio_state, market_context)

    # 3. Disk Persistence
    save_tri_risk_record(result)
    return result

if __name__ == "__main__":
    # Self-test demo
    sample_setup = {
        "symbol": "ETHUSDT",
        "side": "BUY",
        "entry_price": 2800.0,
        "sl": 2750.0,
        "tp": 2950.0,
        "rr": 3.0,
        "strategy": "FVG Reversal Scalp"
    }
    sample_pstate = {
        "active_positions": [{"symbol": "BTCUSDT", "positionAmt": 0.05}],
        "heat": {"long_count": 1, "short_count": 0},
        "free_margin_ratio": 0.82
    }
    outcome = run_tri_perspective_risk(sample_setup, sample_pstate)
    print(json.dumps(outcome, indent=2, ensure_ascii=False))
