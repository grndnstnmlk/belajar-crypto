"""
Adversarial Debate Layer (Bull vs Bear Agent)
Inspired by Tauric Research's TradingAgents Multi-Agent Framework (arXiv:2412.20138)
Adapted for 24/7 Autonomous Crypto Trading & Execution.

Deconstructs candidate setups through an adversarial dialectic process:
1. Bull Researcher  : Formulates the strongest upside thesis, catalysts, and structural confluences.
2. Bear Researcher  : Acts as Devil's Advocate; stress-tests risks, fakeout traps, and invalidation scenarios.
3. Debate Arbiter   : Impartially adjudicates arguments against hard data feeds, assigning conviction scores
                      (Bull vs Bear, 0-100) and producing an executable verdict (APPROVE, ADJUST_RISK, VETO).

Dual-Engine Architecture:
- LLM Multi-Agent Dialog: When Gemini / OpenAI / DeepSeek / Groq API key is present.
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
DEBATE_HISTORY_FILE = os.path.join(DATA_DIR, "adversarial_debates.json")

def load_debate_history(limit=20):
    """Loads recent debate records from disk."""
    if os.path.exists(DEBATE_HISTORY_FILE):
        try:
            with open(DEBATE_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data[-limit:]
        except Exception:
            return []
    return []

def save_debate_record(record):
    """Appends a completed debate record to disk."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        history = []
        if os.path.exists(DEBATE_HISTORY_FILE):
            try:
                with open(DEBATE_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.append(record)
        # Keep last 50 debates
        if len(history) > 50:
            history = history[-50:]
        with open(DEBATE_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def run_deterministic_debate(setup, market_context=None):
    """
    Algorithmic Quant Heuristic Debate Engine:
    Evaluates Bull vs Bear balance mathematically based on order flow,
    macro regime, liquidity walls, and Akademi Crypto SMC confluences.
    """
    ctx = market_context or {}
    sym = setup.get("symbol", "UNKNOWN")
    side = setup.get("side", "BUY").upper()
    entry_p = float(setup.get("entry_price", setup.get("entry", 0.0)))
    sl_p = float(setup.get("sl", setup.get("stop_loss", 0.0)))
    tp_p = float(setup.get("tp", setup.get("take_profit", 0.0)))
    rr = float(setup.get("rr", setup.get("rr_ratio", setup.get("risk_reward", 2.0))))
    strategy = setup.get("strategy", setup.get("reason", "Institutional Structure"))
    is_scalp = setup.get("is_scalp", False)

    btc_regime = ctx.get("market_regime", {})
    btc_bias = btc_regime.get("trend_bias", "NEUTRAL")
    adx = float(btc_regime.get("adx", 25.0))
    
    depth = ctx.get("depth", {})
    imb_ratio = float(depth.get("imbalance_ratio", 1.0)) if depth else 1.0
    
    compass = ctx.get("compass", {})
    regime_code = compass.get("regime_code", "NEUTRAL")

    bull_points = 50
    bear_points = 50
    bull_arguments = []
    bear_arguments = []

    # 1. Macro Trend Gravity
    if side in ["BUY", "LONG"]:
        if btc_bias == "BULLISH":
            bull_points += 22
            bull_arguments.append(f"BTC 1H Makro Bullish ({btc_bias}) memberikan angin buritan tren yang kuat.")
        elif btc_bias == "BEARISH":
            bear_points += 35
            bear_arguments.append(f"BTC 1H Makro Bearish! Melawan gravitasi penurunan Bitcoin membawa risiko likuidasi instan.")
        else:
            bull_points += 5
            bull_arguments.append("BTC 1H Konsolidasi Netral, altcoin memiliki ruang untuk ekspansi independen.")
    else:  # SHORT
        if btc_bias == "BEARISH":
            bull_points += 22  # In a short, 'Bull Researcher' for the trade's success = short side wins
            bull_arguments.append(f"BTC 1H Makro Bearish ({btc_bias}) mengonfirmasi momentum aksi jual institusional.")
        elif btc_bias == "BULLISH":
            bear_points += 35
            bear_arguments.append(f"BTC 1H Makro Bullish! Membuka Short saat Bitcoin reli membawa risiko short squeeze.")
        else:
            bull_points += 5

    # 2. Risk-to-Reward Ratio
    if rr >= 2.0:
        bull_points += 15
        bull_arguments.append(f"Rasio Risk-to-Reward prima (1:{rr:.2f}) memenuhi standar asimetri risiko institusional.")
    else:
        bear_points += 18
        bear_arguments.append(f"Rasio Risk-to-Reward tipis (1:{rr:.2f} < 1:2.00) tidak memberikan kompensasi probabilitas yang cukup.")

    # 3. Order Book Depth Liquidity Collision
    if side in ["BUY", "LONG"]:
        if imb_ratio >= 1.25:
            bull_points += 12
            bull_arguments.append(f"Dinding bid support tebal ({imb_ratio:.2f}x Bids/Asks) menahan tekanan jual di bawah entry.")
        elif imb_ratio <= 0.70:
            bear_points += 20
            bear_arguments.append(f"Dinding ask resistansi masif ({imb_ratio:.2f}x Bids/Asks) membatasi potensi kenaikan.")
    else:
        if imb_ratio <= 0.80:
            bull_points += 12
            bull_arguments.append(f"Dinding ask resistance berat ({imb_ratio:.2f}x Bids/Asks) menekan harga ke bawah.")
        elif imb_ratio >= 1.30:
            bear_points += 20
            bear_arguments.append(f"Dinding bid pembeli tebal ({imb_ratio:.2f}x Bids/Asks) berpotensi memantulkan harga ke atas.")

    # 4. Strategy & Structure Quality
    if any(k in strategy for k in ["Rejection Block", "4H-Range", "Inverse FVG", "Akademi Crypto", "Rectangle", "20-EMA"]):
        bull_points += 16
        bull_arguments.append(f"Setup terkonfirmasi oleh model probabilitas tinggi: '{strategy}'.")
    else:
        bull_points += 8

    # 5. Volatility / ADX Chop Fakeout
    if adx < 20.0 and not is_scalp:
        bear_points += 14
        bear_arguments.append(f"Volatilitas pasar lesu (ADX {adx:.1f} < 20), sinyal swing rentan terperangkap fakeout mendatar.")

    # Default arguments if empty
    if not bull_arguments:
        bull_arguments.append("Setup teknikal dasar memenuhi syarat rasio risiko dan level support/resistance terdekat.")
    if not bear_arguments:
        bear_arguments.append("Risiko volatilitas pasar kripto umum; tidak ditemukan anomali red-flag kritis pada order book.")

    # Normalize scores to 0-100 scale
    total = bull_points + bear_points
    norm_bull = int(round((bull_points / total) * 100))
    norm_bear = 100 - norm_bull

    # Determine Arbiter Verdict
    if norm_bear >= 65:
        verdict = "VETO"
        winner = "BEAR"
        risk_scale = 0.0
        synthesis = (
            f"VETO MUTLAK: Argumen Bear menang dominan ({norm_bear}% vs {norm_bull}%). "
            f"Faktor risiko kritis: {bear_arguments[0]} Posisi dibatalkan demi proteksi modal."
        )
    elif norm_bear >= 52:
        verdict = "ADJUST_RISK"
        winner = "COMPROMISE"
        risk_scale = 0.50
        synthesis = (
            f"KOMPROMI KEHATI-HATIAN: Persaingan argumen ketat ({norm_bull}% Bull vs {norm_bear}% Bear). "
            f"Setup diizinkan masuk namun ukuran alokasi risiko dipotong ke 50% untuk meredam risiko."
        )
    else:
        verdict = "APPROVE"
        winner = "BULL"
        risk_scale = 1.00
        synthesis = (
            f"PERSETUJUAN DISKUSI: Argumen Bull unggul meyakinkan ({norm_bull}% vs {norm_bear}%). "
            f"Konfluensi struktur kuat dan risiko terkendali. Eksekusi ukuran penuh disetujui."
        )

    return {
        "symbol": sym,
        "side": side,
        "entry_price": entry_p,
        "sl_price": sl_p,
        "tp_price": tp_p,
        "rr_ratio": rr,
        "strategy": strategy,
        "bull_score": norm_bull,
        "bear_score": norm_bear,
        "winner": winner,
        "verdict": verdict,
        "suggested_risk_scale": risk_scale,
        "bull_thesis": " • " + "\n • ".join(bull_arguments),
        "bear_critique": " • " + "\n • ".join(bear_arguments),
        "arbiter_synthesis": synthesis,
        "invalidation_price": sl_p,
        "engine": "Deterministic Quant Heuristic (Tauric Protocol)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def run_llm_adversarial_debate(setup, market_context=None):
    """
    LLM Cognitive Adversarial Debate Engine:
    Executes a multi-agent debate between Bull Researcher and Bear Researcher,
    adjudicated by the Research Manager (Debate Arbiter).
    """
    try:
        import ai_risk_officer
        creds = ai_risk_officer.get_ai_credentials()
        provider = creds.get("provider", "fallback_quant")
        if provider == "fallback_quant":
            return None
    except Exception:
        return None

    sym = setup.get("symbol", "UNKNOWN")
    side = setup.get("side", "BUY").upper()
    entry_p = float(setup.get("entry_price", setup.get("entry", 0.0)))
    sl_p = float(setup.get("sl", setup.get("stop_loss", 0.0)))
    tp_p = float(setup.get("tp", setup.get("take_profit", 0.0)))
    rr = float(setup.get("rr", setup.get("rr_ratio", setup.get("risk_reward", 2.0))))
    strategy = setup.get("strategy", setup.get("reason", "Institutional Structure"))
    ctx = market_context or {}

    prompt = f"""
Anda bertindak sebagai sistem multi-agent finansial terkemuka TAURIC RESEARCH (TradingAgents, arXiv:2412.20138).
Lakukan sesi DEBAT ADVERSARIAL ketat antara Bull Researcher vs Bear Researcher, lalu adili oleh Debate Arbiter.

[INFORMASI KANDIDAT SETUP]
- Simbol: {sym}
- Posisi: {side}
- Harga Entry: ${entry_p:,.4f}
- Stop Loss: ${sl_p:,.4f}
- Target Profit: ${tp_p:,.4f}
- Rasio R:R: 1:{rr:.2f}
- Strategi: {strategy}

[KONTEKS INTELIJEN PASAR LIVE]
- Rezim Makro BTC 1H: {json.dumps(ctx.get('market_regime', {}))}
- Market Compass (BTC.D & USDT.D): {json.dumps(ctx.get('compass', {}))}
- Order Book Depth Imbalance: {json.dumps(ctx.get('depth', {}))}
- Macro News Shield Status: {json.dumps(ctx.get('news_shield', {}))}

[ATURAN PERDEBATAN]
1. BULL RESEARCHER: Wajib menyusun argumen kenaikan terkuat, katalis teknikal, FVG, liquidity pools, dan asimetri cuan.
2. BEAR RESEARCHER: Bertindak sebagai Devil's Advocate, mencari kelemahan tersembunyi, risiko BTC drag, dinding resistansi, fakeout, dan potensi likuidasi.
3. DEBATE ARBITER: Menimbang kedua argumen secara imparsial terhadap data objektif, memberi skor conviction (0-100), memutuskan VETO jika risiko terlalu tinggi, ADJUST_RISK jika ada kompromi, atau APPROVE jika aman.

Format jawaban HANYA berupa JSON valid dengan skema:
{{
  "bull_score": <integer 0-100>,
  "bear_score": <integer 0-100>,
  "winner": "BULL" | "BEAR" | "COMPROMISE",
  "verdict": "APPROVE" | "ADJUST_RISK" | "VETO",
  "suggested_risk_scale": <float 0.0 s/d 1.0>,
  "bull_thesis": "<argumen poin-poin terpenting dari Bull Researcher>",
  "bear_critique": "<bantahan tajam dan risiko dari Bear Researcher>",
  "arbiter_synthesis": "<putusan final dan ringkasan eksekutif dari Arbiter>",
  "invalidation_price": {sl_p}
}}
"""
    try:
        import ai_risk_officer
        res = ai_risk_officer.call_llm(prompt, system_prompt="You are the Tauric Research Multi-Agent Trading Debate System.", response_json=True)
        if res and isinstance(res, dict) and "verdict" in res and "bull_score" in res:
            res["symbol"] = sym
            res["side"] = side
            res["entry_price"] = entry_p
            res["sl_price"] = sl_p
            res["tp_price"] = tp_p
            res["rr_ratio"] = rr
            res["strategy"] = strategy
            res["engine"] = f"Tauric Cognitive LLM ({creds.get('provider').upper()})"
            res["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return res
    except Exception:
        pass

    return None

def run_adversarial_debate(setup, market_context=None):
    """
    Main Gateway Function:
    Runs LLM Cognitive Multi-Agent Debate if API key is available;
    otherwise seamlessly fails over to Deterministic Quant Matrix (< 5ms).
    Records the completed debate for visual dashboard audit.
    """
    # 1. Try Cognitive LLM Engine
    result = run_llm_adversarial_debate(setup, market_context)

    # 2. Deterministic Quant Engine Fallback
    if not result:
        result = run_deterministic_debate(setup, market_context)

    # 3. Persist debate record
    save_debate_record(result)

    return result

if __name__ == "__main__":
    print("=================================================================")
    print("   🐂 vs 🐻 TAURIC ADVERSARIAL DEBATE LAYER TEST")
    print("=================================================================")
    sample_setup = {
        "symbol": "SOLUSDT",
        "side": "LONG",
        "entry": 103.80,
        "sl": 102.50,
        "tp": 106.40,
        "rr_ratio": 2.0,
        "strategy": "5m Akademi Crypto High Win-Rate Scalp",
        "is_scalp": True
    }
    mock_ctx = {
        "market_regime": {"trend_bias": "BULLISH", "adx": 28.5},
        "compass": {"regime_code": "ALT_SEASON_RISK_ON"},
        "depth": {"imbalance_ratio": 1.45}
    }
    outcome = run_adversarial_debate(sample_setup, mock_ctx)
    print(f"Winner   : {outcome['winner']} (Bull {outcome['bull_score']}% vs Bear {outcome['bear_score']}%)")
    print(f"Verdict  : {outcome['verdict']} (Risk Scale: {outcome['suggested_risk_scale']})")
    print(f"Engine   : {outcome['engine']}")
    print(f"\n[BULL THESIS]:\n{outcome['bull_thesis']}")
    print(f"\n[BEAR CRITIQUE]:\n{outcome['bear_critique']}")
    print(f"\n[ARBITER SYNTHESIS]:\n{outcome['arbiter_synthesis']}")
