"""
AI Senior Quant Risk Officer & Autonomous Co-Pilot
Synthesizes Akademi Crypto Curriculum (Macro, SMC, Order Flow, and Money Management)
with LLM Cognitive Reasoning (Google Gemini, OpenAI, DeepSeek, Groq, or Algorithmic Fallback).

Performs:
1. Pre-Trade Gatekeeping (Sanity Check, Invalidation Analysis, Veto & Sizing Adjustment)
2. Post-Trade Autopsy (Evaluates SL/TP outcomes and extracts lessons for journal memory)
3. Conversational Co-Pilot (Answers user questions via Telegram /ask and Web Dashboard)
"""

import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "AIQuantRiskOfficer/1.0",
    "Content-Type": "application/json"
}

def parse_env():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return env_vars

def get_ai_credentials():
    """
    Detects available AI LLM keys in priority order:
    1. Google Gemini (GEMINI_API_KEY or GOOGLE_API_KEY)
    2. OpenAI (OPENAI_API_KEY)
    3. DeepSeek (DEEPSEEK_API_KEY)
    4. Groq (GROQ_API_KEY)
    """
    env = parse_env()
    gemini_key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        return {"provider": "gemini", "key": gemini_key.strip()}

    openai_key = env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return {"provider": "openai", "key": openai_key.strip()}

    deepseek_key = env.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        return {"provider": "deepseek", "key": deepseek_key.strip()}

    groq_key = env.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if groq_key:
        return {"provider": "groq", "key": groq_key.strip()}

    return {"provider": "fallback_quant", "key": None}

def call_llm(prompt, system_prompt=None, temperature=0.2, response_json=False):
    """
    Calls configured LLM provider or gracefully returns None to trigger heuristic engine.
    Supports response_json=True for structured JSON output.
    """
    creds = get_ai_credentials()
    provider = creds.get("provider")
    key = creds.get("key")

    if not key or provider == "fallback_quant":
        return None

    # 1. Google Gemini API Call
    if provider == "gemini":
        models_to_try = [
            "gemini-flash-latest",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-flash-lite-latest",
            "gemini-3.7-flash"
        ]
        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            gen_config = {
                "temperature": temperature,
                "maxOutputTokens": 1024
            }
            if response_json:
                gen_config["responseMimeType"] = "application/json"

            body = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": gen_config
            }
            try:
                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
                with urllib.request.urlopen(req, timeout=18, context=SSL_CTX) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception:
                continue
        return None

    # 2. OpenAI / DeepSeek / Groq Compatible Chat API
    api_configs = {
        "openai": ("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
        "deepseek": ("https://api.deepseek.com/chat/completions", "deepseek-chat"),
        "groq": ("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile")
    }

    if provider in api_configs:
        endpoint, model_name = api_configs[provider]
        headers = dict(HEADERS)
        headers["Authorization"] = f"Bearer {key}"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=18, context=SSL_CTX) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                choices = res_json.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
        except Exception:
            return None

    return None

def heuristic_quant_audit(setup, market_context=None):
    """
    High-confidence rule-based Quant Risk Officer fallback.
    Executes if no LLM key is configured or if network fails.
    """
    ctx = market_context or {}
    sym = setup.get("symbol", "UNKNOWN")
    side = setup.get("side", "BUY").upper()
    entry_p = float(setup.get("entry_price", setup.get("entry", setup.get("price", 0.0))))
    sl_p = float(setup.get("sl", setup.get("stop_loss", 0.0)))
    tp_p = float(setup.get("tp", setup.get("take_profit", 0.0)))
    rr = float(setup.get("rr", setup.get("risk_reward", 0.0)))
    if rr <= 0.0 and abs(entry_p - sl_p) > 0:
        rr = round(abs(tp_p - entry_p) / abs(entry_p - sl_p), 2)

    # Context extraction
    heat = ctx.get("heat", {})
    depth = ctx.get("depth", {})
    compass = ctx.get("compass", {})
    cb_prem = ctx.get("coinbase_premium", {})
    news = ctx.get("news_shield", {})

    key_risks = []
    decision = "APPROVE"
    suggested_scale = 1.0
    confidence = 85

    # 1. Macro News Blackout Check
    if news.get("is_blackout"):
        return {
            "decision": "VETO",
            "confidence": 95,
            "suggested_risk_scale": 0.0,
            "thesis": f"VETO: Pasar dalam periode News Blackout ({news.get('reason', 'High-Impact Event')}). Volatilitas manipulatif ekstrem berisiko memicu slippage.",
            "key_risks": ["High-impact economic news window active", "Severe spread widening risk"],
            "invalidation_scenario": "N/A - Wait until 30 minutes after news release.",
            "provider": "Algorithmic Quant Heuristics"
        }

    # 2. Directional Heat Risk
    if heat.get("is_over_exposed"):
        if (side in ["BUY", "LONG"] and heat.get("long_count", 0) >= heat.get("max_same_direction", 2)) or \
           (side in ["SELL", "SHORT"] and heat.get("short_count", 0) >= heat.get("max_same_direction", 2)):
            return {
                "decision": "VETO",
                "confidence": 92,
                "suggested_risk_scale": 0.0,
                "thesis": f"VETO: Batas Directional Heat Portofolio tercapai ({heat.get('long_count', 0)} Longs / {heat.get('short_count', 0)} Shorts). Terlalu rentan terhadap pergerakan sistemik BTC.",
                "key_risks": ["Portfolio directional correlation limit reached", "Systemic simultaneous liquidation risk"],
                "invalidation_scenario": "Tunggu salah satu posisi searah tertutup atau TP1 terlindungi.",
                "provider": "Algorithmic Quant Heuristics"
            }

    # 3. Order Book Depth Wall Collision
    imb_ratio = float(depth.get("imbalance_ratio", 1.0)) if depth else 1.0
    if side in ["BUY", "LONG"] and imb_ratio <= 0.60:
        decision = "ADJUST_RISK"
        suggested_scale = 0.5
        confidence = 78
        key_risks.append(f"Heavy overhead ask wall ({imb_ratio:.2f}x Bids/Asks) limits upward momentum")
    elif side in ["SELL", "SHORT"] and imb_ratio >= 1.65:
        decision = "ADJUST_RISK"
        suggested_scale = 0.5
        confidence = 78
        key_risks.append(f"Thick bid support floor ({imb_ratio:.2f}x Bids/Asks) threatens short breakdown")

    # 4. Dominance Flow Alignment
    regime = compass.get("regime_code", "NEUTRAL")
    if side in ["BUY", "LONG"] and "CAPITAL_FLIGHT" in regime:
        suggested_scale = min(suggested_scale, 0.75)
        key_risks.append("Capital flight to USDT.D in progress - altcoin rallies face early exhaustion")

    # 5. R:R Precision
    if rr < 2.5:
        key_risks.append(f"Marginal Risk-to-Reward ratio (1:{rr:.2f} below preferred 1:3.0)")
        if decision == "APPROVE":
            decision = "ADJUST_RISK"
            suggested_scale = min(suggested_scale, 0.7)

    # Build Thesis
    if decision == "APPROVE":
        thesis = f"APPROVED: Setup {sym} ({side}) selaras dengan struktur pasar institusional. R:R 1:{rr:.2f} memadai dan tidak berhadapan langsung dengan dinding likuiditas masif."
    else:
        thesis = f"ADJUST_RISK: Setup {sym} ({side}) diterima dengan catatan risiko kehati-hatian ({', '.join(key_risks)}). Alokasi modal disarankan dipangkas ke {suggested_scale*100:.0f}%."

    return {
        "decision": decision,
        "confidence": confidence,
        "suggested_risk_scale": suggested_scale,
        "thesis": thesis,
        "key_risks": key_risks if key_risks else ["Normal market volatility risk"],
        "invalidation_scenario": f"Penutupan candle 15m melewati level Stop Loss ${setup.get('sl', 0):,.4f}.",
        "provider": "Algorithmic Quant Heuristics"
    }

def audit_trade_setup(setup, market_context=None):
    """
    Main Pre-Trade Gatekeeper Audit:
    Feeds setup parameters and market intelligence into LLM.
    Falls back gracefully to heuristic quant engine on any error.
    """
    creds = get_ai_credentials()
    provider = creds.get("provider", "fallback_quant")

    if provider == "fallback_quant":
        return heuristic_quant_audit(setup, market_context)

    # Format rich context for LLM
    ctx = market_context or {}
    sym = setup.get("symbol", "UNKNOWN")
    side = setup.get("side", "BUY")
    entry_p = float(setup.get("entry_price", setup.get("entry", setup.get("price", 0.0))))
    sl_p = float(setup.get("sl", setup.get("stop_loss", 0.0)))
    tp_p = float(setup.get("tp", setup.get("take_profit", 0.0)))
    rr = float(setup.get("rr", setup.get("risk_reward", 0.0)))
    if rr <= 0.0 and abs(entry_p - sl_p) > 0:
        rr = round(abs(tp_p - entry_p) / abs(entry_p - sl_p), 2)

    prompt = f"""
[CANDIDATE TRADE SETUP FOR AUDIT]
- Symbol: {sym}
- Side: {side}
- Entry Price: ${entry_p:,.4f}
- Stop Loss: ${sl_p:,.4f}
- Target Take Profit: ${tp_p:,.4f}
- Risk-to-Reward Ratio: 1:{rr}
- Setup Trigger / Strategy: {setup.get('reason', setup.get('strategy', 'SMC Key Level Sweep & Structure'))}
- Structural Anchor: {setup.get('structural_level', 'Protected Swing Pivot')}

[REAL-TIME MARKET INTELLIGENCE CONTEXT]
- Macro News Shield: {json.dumps(ctx.get('news_shield', {}))}
- Directional Portfolio Heat: {json.dumps(ctx.get('heat', {}))}
- Market Flow Compass (BTC.D & USDT.D): {json.dumps(ctx.get('compass', {}))}
- Coinbase Premium Index (Wall St Flow): {json.dumps(ctx.get('coinbase_premium', {}))}
- Order Book Depth Imbalance (DOM ±2%): {json.dumps(ctx.get('depth', {}))}
- Derivatives Sentiment (OI & L/S Ratio): {json.dumps(ctx.get('derivatives', {}))}

[TASK]
Evaluate this candidate trade as an institutional Senior Quant Risk Officer.
Strictly respond in valid JSON format with this exact schema:
{{
  "decision": "APPROVE" | "VETO" | "ADJUST_RISK",
  "confidence": <integer 0-100>,
  "suggested_risk_scale": <float 0.0 to 1.0>,
  "thesis": "<1-2 sentences in Indonesian explaining your quantitative thesis>",
  "key_risks": ["<risk 1>", "<risk 2>"],
  "invalidation_scenario": "<short description of when this setup is proven wrong>"
}}
"""

    sys_prompt = (
        "You are the Senior Crypto Quant Risk Officer of an autonomous trading desk trained on Akademi Crypto Module 01-03. "
        "Your top priority is risk defense, avoiding bull/bear traps, and filtering low-probability setups. "
        "Always output clean, parseable JSON with no markdown wrapping or preamble."
    )

    raw_resp = call_llm(prompt, system_prompt=sys_prompt, temperature=0.1, response_json=True)
    if raw_resp:
        try:
            # Extract JSON block
            json_str = raw_resp
            if "```" in json_str:
                m = re.search(r"\{.*\}", json_str, re.DOTALL)
                if m:
                    json_str = m.group(0)
            parsed = json.loads(json_str)
            parsed["provider"] = provider.upper()
            return parsed
        except Exception:
            pass

    # If parsing or network failed, fallback seamlessly
    fallback_res = heuristic_quant_audit(setup, market_context)
    fallback_res["provider"] = f"Heuristic Fallback ({provider.upper()} API Timeout)"
    return fallback_res

def perform_trade_autopsy(closed_trade):
    """
    Evaluates closed trade outcome (TP or SL) and produces a concise autopsy note.
    """
    sym = closed_trade.get("symbol", "UNKNOWN")
    pnl = float(closed_trade.get("net_pnl_usd", closed_trade.get("pnl_usd", 0.0)))
    side = closed_trade.get("side", "BUY")
    r_mult = closed_trade.get("r_multiple", 0.0)
    exit_reason = closed_trade.get("exit_reason", "Target / Stop Hit")

    creds = get_ai_credentials()
    provider = creds.get("provider", "fallback_quant")

    if provider != "fallback_quant":
        prompt = f"""
[CLOSED TRADE TO AUTOPSY]
- Symbol: {sym}
- Side: {side}
- Net Realized PnL: ${pnl:,.2f} USDT
- Realized R-Multiple: {r_mult}R
- Exit Reason: {exit_reason}
- Entry Price: ${closed_trade.get('entry_price', 0):,.4f}
- Exit Price: ${closed_trade.get('exit_price', 0):,.4f}

Provide a 2-sentence institutional trade autopsy in Indonesian evaluating whether execution followed Smart Money rules and key lesson learned.
Respond in JSON:
{{
  "autopsy_summary": "...",
  "key_lesson": "...",
  "grade": "A" | "B" | "C"
}}
"""
        sys_prompt = "You are a trading psychologist and post-trade performance auditor from Akademi Crypto Module 03."
        resp = call_llm(prompt, system_prompt=sys_prompt, temperature=0.2, response_json=True)
        if resp:
            try:
                json_str = resp
                if "```" in json_str:
                    m = re.search(r"\{.*\}", json_str, re.DOTALL)
                    if m:
                        json_str = m.group(0)
                return json.loads(json_str)
            except Exception:
                pass

    # Heuristic Autopsy
    if pnl >= 0:
        return {
            "autopsy_summary": f"Eksekusi disiplin pada {sym} ({side}). Trade berhasil mengamankan profit +{r_mult}R (+${pnl:,.2f} USDT) sesuai proyeksi target.",
            "key_lesson": "Biarkan runner berjalan dipandu trailing stop struktural untuk memaksimalkan payoff ratio.",
            "grade": "A",
            "provider": "Algorithmic Autopsy"
        }
    else:
        return {
            "autopsy_summary": f"Trade {sym} ({side}) menyentuh Stop Loss (${pnl:,.2f} USDT). Proteksi risiko teruji memotong kerugian tepat pada batas 1.5% modal.",
            "key_lesson": "Evaluasi kembali sweep buffer dan perhatikan penyerapan order book sebelum entri ulang.",
            "grade": "B",
            "provider": "Algorithmic Autopsy"
        }

def answer_trader_query(user_query, portfolio_context=None):
    """
    Answers trader questions via Telegram /ask command or Web Dashboard with live market grounding.
    """
    creds = get_ai_credentials()
    provider = creds.get("provider", "fallback_quant")

    ctx = portfolio_context or {}
    bal = ctx.get("balance_usd", 5000.0)
    pos_count = len(ctx.get("positions", []))
    mode = ctx.get("mode", "SWING")
    news = ctx.get("news_shield", {}).get("status", "SAFE")

    if provider != "fallback_quant":
        prompt = f"""
[CURRENT TRADING DESK STATUS]
- Equity Balance: ${bal:,.2f} USDT
- Active Positions: {pos_count}
- Operating Mode: {mode} (Big-Profit Focus)
- Macro News Shield: {news}
- Active Positions Detail: {json.dumps(ctx.get('positions', []))}

[USER QUESTION]
"{user_query}"

[INSTRUCTIONS]
Answer the user concisely and professionally in Indonesian as the Trading Desk AI Officer.
Cite real portfolio metrics if relevant. Keep answer under 120 words.
"""
        sys_prompt = "You are the AI Senior Quant Officer of the user's autonomous Binance Trading Desk (Akademi Crypto)."
        resp = call_llm(prompt, system_prompt=sys_prompt, temperature=0.3)
        if resp:
            return resp.strip()

    # Heuristic response if LLM offline
    lower_q = user_query.lower()
    if "saldo" in lower_q or "balance" in lower_q:
        return f"💰 Saldo equity Trading Desk saat ini adalah ${bal:,.2f} USDT dengan {pos_count} posisi aktif berjalan."
    elif "status" in lower_q or "mode" in lower_q:
        return f"🤖 Trading desk beroperasi dalam Mode {mode} dengan News Shield status '{news}'. Autopilot aktif memindai setup high-confluence."
    elif "posisi" in lower_q or "position" in lower_q:
        if not ctx.get("positions"):
            return "Saat ini tidak ada posisi terbuka di market. Seluruh slot kas aman."
        pos_str = ", ".join([f"{p['symbol']} ({p['side']} PnL: ${float(p.get('pnl_usd', 0)):+.2f})" for p in ctx.get("positions", [])])
        return f"Posisi aktif saat ini ({pos_count}): {pos_str}."
    else:
        return (
            f"🤖 <b>AI Officer Report:</b> Sistem beroperasi normal pada mode {mode}. "
            f"Saldo: ${bal:,.2f} USDT | Posisi: {pos_count}. "
            f"Untuk mengaktifkan penalaran penuh AI LLM, Anda dapat menambahkan <code>GEMINI_API_KEY=...</code> di file .env."
        )

if __name__ == "__main__":
    print("Testing AI Risk Officer module...")
    creds = get_ai_credentials()
    print(f"Active Provider: {creds['provider']}")

    dummy_setup = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "entry_price": 79650.0,
        "sl": 78800.0,
        "tp": 82200.0,
        "rr": 3.0,
        "reason": "SMC Order Block Retest & MSS Sweep"
    }
    audit = audit_trade_setup(dummy_setup)
    print("\nAudit Result:")
    print(json.dumps(audit, indent=2))

    autopsy = perform_trade_autopsy({"symbol": "LINKUSDT", "side": "BUY", "net_pnl_usd": 65.17, "r_multiple": 2.0, "exit_reason": "Scale-Out TP1"})
    print("\nAutopsy Result:")
    print(json.dumps(autopsy, indent=2))

    ans = answer_trader_query("Bagaimana status trading desk saat ini?", {"balance_usd": 5283.69, "positions": [], "mode": "SWING"})
    print("\nQ&A Result:")
    print(ans)
