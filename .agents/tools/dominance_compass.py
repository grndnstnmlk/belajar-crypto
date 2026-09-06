"""
BTC Dominance (BTC.D) & USDT Dominance (USDT.D) Compass Engine
Synthesized from Akademi Crypto Module 01 (Fundamental & Macro Top-Down Analysis)
Decodes real-time capital rotation between Bitcoin, Altcoins, and Tether (Cash)
to prevent buying altcoins during BTC vampire rallies or market-wide cashouts.
"""

import json
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
DOMINANCE_HISTORY_FILE = os.path.join(DATA_DIR, "dominance_history.json")

# SSL Context to prevent Windows certificate errors
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# In-memory TTL cache (60 seconds) to avoid rate limits
_CACHE = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 60

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def fetch_coingecko_global():
    url = "https://api.coingecko.com/api/v3/global"
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as response:
            res = json.loads(response.read().decode("utf-8"))
            data = res.get("data", {})
            caps = data.get("market_cap_percentage", {})
            return {
                "source": "CoinGecko",
                "btc_d": float(caps.get("btc", 0.0)),
                "eth_d": float(caps.get("eth", 0.0)),
                "usdt_d": float(caps.get("usdt", 0.0)),
                "usdc_d": float(caps.get("usdc", 0.0)),
                "sol_d": float(caps.get("sol", 0.0)),
                "total_stable_d": round(float(caps.get("usdt", 0.0)) + float(caps.get("usdc", 0.0)), 2),
                "total_mcap_usd": float(data.get("total_market_cap", {}).get("usd", 0.0)),
                "total_volume_usd": float(data.get("total_volume", {}).get("usd", 0.0)),
                "mcap_chg_24h": float(data.get("market_cap_change_percentage_24h_usd", 0.0))
            }
    except Exception as e:
        return None

def fetch_coinpaprika_global():
    url = "https://api.coinpaprika.com/v1/global"
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as response:
            data = json.loads(response.read().decode("utf-8"))
            btc_d = float(data.get("bitcoin_dominance_percentage", 55.0))
            return {
                "source": "CoinPaprika",
                "btc_d": btc_d,
                "eth_d": 12.0,
                "usdt_d": 6.5,
                "usdc_d": 2.5,
                "sol_d": 2.2,
                "total_stable_d": 9.0,
                "total_mcap_usd": float(data.get("market_cap_usd", 0.0)),
                "total_volume_usd": float(data.get("volume_24h_usd", 0.0)),
                "mcap_chg_24h": float(data.get("market_cap_change_24h", 0.0))
            }
    except Exception as e:
        return None

def fetch_btc_price_and_change():
    """
    Fetches real-time BTC price and 24h performance from OKX.
    """
    url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as response:
            res = json.loads(response.read().decode("utf-8"))
            if res.get("data"):
                d = res["data"][0]
                o = float(d.get("open24h", 0))
                c = float(d.get("last", 0))
                chg = ((c - o) / o * 100.0) if o > 0 else 0.0
                return c, round(chg, 2)
    except Exception:
        pass
    return 65000.0, 0.0

def load_dominance_history():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DOMINANCE_HISTORY_FILE):
        try:
            with open(DOMINANCE_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_dominance_tick(tick):
    history = load_dominance_history()
    history.append(tick)
    # Keep last 200 ticks (approx 2-3 days of ticks)
    if len(history) > 200:
        history = history[-200:]
    try:
        with open(DOMINANCE_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def get_dominance_compass():
    """
    Main entry point: fetches market dominance, computes 1H/24H deltas,
    and classifies into the 4 Akademi Crypto Market Flow Quadrants.
    """
    global _CACHE
    now = time.time()
    if _CACHE["data"] and (now - _CACHE["timestamp"] < CACHE_TTL):
        return _CACHE["data"]

    # 1. Fetch live dominance data
    dom_data = fetch_coingecko_global()
    if not dom_data:
        dom_data = fetch_coinpaprika_global()

    if not dom_data:
        # Fallback defaults
        dom_data = {
            "source": "Fallback",
            "btc_d": 58.5,
            "eth_d": 12.0,
            "usdt_d": 6.8,
            "usdc_d": 2.7,
            "sol_d": 2.3,
            "total_stable_d": 9.5,
            "total_mcap_usd": 2700000000000.0,
            "total_volume_usd": 70000000000.0,
            "mcap_chg_24h": 0.0
        }

    btc_price, btc_chg_24h = fetch_btc_price_and_change()
    dom_data["btc_price"] = btc_price
    dom_data["btc_chg_24h"] = btc_chg_24h

    # 2. Historical Delta Calculation
    history = load_dominance_history()
    btc_d_cur = dom_data["btc_d"]
    usdt_d_cur = dom_data["usdt_d"]

    btc_d_delta_1h = 0.0
    usdt_d_delta_1h = 0.0
    btc_d_delta_24h = 0.0
    usdt_d_delta_24h = 0.0

    if history:
        cur_ts = time.time()
        tick_1h = None
        tick_24h = None

        for h in reversed(history):
            age = cur_ts - h.get("timestamp", cur_ts)
            if age >= 3000 and tick_1h is None:
                tick_1h = h
            if age >= 80000 and tick_24h is None:
                tick_24h = h
                break

        if not tick_1h and history:
            tick_1h = history[0]
        if not tick_24h and history:
            tick_24h = history[0]

        if tick_1h:
            btc_d_delta_1h = round(btc_d_cur - tick_1h.get("btc_d", btc_d_cur), 3)
            usdt_d_delta_1h = round(usdt_d_cur - tick_1h.get("usdt_d", usdt_d_cur), 3)

        if tick_24h:
            btc_d_delta_24h = round(btc_d_cur - tick_24h.get("btc_d", btc_d_cur), 3)
            usdt_d_delta_24h = round(usdt_d_cur - tick_24h.get("usdt_d", usdt_d_cur), 3)

    # Record current tick if enough time elapsed (> 5 mins)
    if not history or (now - history[-1].get("timestamp", 0) > 300):
        save_dominance_tick({
            "timestamp": now,
            "time_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "btc_d": btc_d_cur,
            "usdt_d": usdt_d_cur,
            "btc_price": btc_price
        })

    # 3. USDT Dominance Sentiment (Risk-On vs Risk-Off)
    # Falling USDT.D = Cash deploying into crypto (Bullish / Risk-On)
    # Rising USDT.D = Crypto selling off into Cash (Bearish / Risk-Off)
    if usdt_d_delta_1h <= -0.05 or dom_data["mcap_chg_24h"] > 1.5:
        usdt_status = "🟢 RISK-ON (Modal masuk ke kripto, likuiditas kas agresif)"
        usdt_bias = "RISK_ON"
    elif usdt_d_delta_1h >= 0.05 or dom_data["mcap_chg_24h"] < -2.0:
        usdt_status = "🔴 RISK-OFF (Modal lari ke USDT/Cash, likuiditas pasar terkuras)"
        usdt_bias = "RISK_OFF"
    else:
        usdt_status = "⚪ NETRAL (Arus kas USDT seimbang)"
        usdt_bias = "NEUTRAL"

    # 4. Akademi Crypto 4-Quadrant Market Flow Matrix
    # Inputs: btc_chg_24h, btc_d_delta_1h / btc_d_delta_24h
    btc_bullish = btc_chg_24h >= 0.5
    btc_bearish = btc_chg_24h <= -0.5
    btc_sideways = not (btc_bullish or btc_bearish)

    btcd_rising = btc_d_delta_1h > 0.02 or (btc_d_delta_1h >= 0 and btc_d_delta_24h > 0.1)
    btcd_falling = btc_d_delta_1h < -0.02 or (btc_d_delta_1h <= 0 and btc_d_delta_24h < -0.1)

    if (btc_bullish or btc_sideways) and btcd_falling:
        # KUADRAN 2: ALTSEASON BOOM!
        quadrant = 2
        regime_code = "ALTSEASON_BOOM"
        regime_title = "🚀 KUADRAN 2: ALTSEASON BOOM (Ekspansi Altcoin Masif)"
        alt_permission = True
        btc_permission = True
        alt_priority = "HIGH"
        advice = (
            "Bitcoin bergerak stabil/naik sementara dominasi BTC.D turun! "
            "Keuntungan dari BTC mengalir deras ke Altcoin (ETH, SOL, High-Beta Alts). "
            "Setup Long Altcoin memiliki ekspektansi profit & R:R tertinggi!"
        )
        alt_bonus = 6
        sizing_mult = 1.0

    elif btc_bullish and btcd_rising:
        # KUADRAN 1: BITCOIN VAMPIRE RALLY
        quadrant = 1
        regime_code = "BTC_VAMPIRE"
        regime_title = "🩸 KUADRAN 1: BITCOIN VAMPIRE (Likuiditas Terserap ke BTC)"
        alt_permission = False
        btc_permission = True
        alt_priority = "LOW"
        advice = (
            "Bitcoin naik kencang namun BTC Dominance ikut meroket! "
            "Likuiditas tersedot habis ke BTC, altcoin bergerak lesu atau berdarah vs BTC. "
            "HANYA trading Long pada Bitcoin! Hindari membuka posisi Long baru pada Altcoin."
        )
        alt_bonus = -8
        sizing_mult = 0.8

    elif btc_bearish and btcd_rising:
        # KUADRAN 3: ALTCOIN BLOODBATH / CARNAGE
        quadrant = 3
        regime_code = "ALTCOIN_BLOODBATH"
        regime_title = "🚨 KUADRAN 3: ALTCOIN BLOODBATH (Altcoin Runtuh Cepat)"
        alt_permission = False
        btc_permission = False
        alt_priority = "AVOID"
        advice = (
            "BAHAYA MAKSIMAL: Bitcoin terkoreksi dan dominasi BTC.D justru naik! "
            "Altcoin akan jatuh 2x-3x lipat lebih dalam dibanding Bitcoin. "
            "DILARANG KERAS membuka Long Altcoin! Prioritaskan Short Hedging atau amankan Cash!"
        )
        alt_bonus = -12
        sizing_mult = 0.5

    elif btc_bearish and btcd_falling:
        # KUADRAN 4: MARKET-WIDE CAPITAL FLIGHT
        quadrant = 4
        regime_code = "CAPITAL_FLIGHT"
        regime_title = "💸 KUADRAN 4: CAPITAL FLIGHT (Modal Kabur ke Kas / USDT)"
        alt_permission = False
        btc_permission = False
        alt_priority = "AVOID"
        advice = (
            "Seluruh pasar kripto terkoreksi dan modal melarikan diri ke stablecoin (USDT.D naik). "
            "Bukan waktunya membeli! Tahan kas atau buka posisi Short untuk lindung nilai portofolio."
        )
        alt_bonus = -10
        sizing_mult = 0.5

    else:
        # NETRAL / KONSOLIDASI
        quadrant = 0
        regime_code = "NEUTRAL_RANGE"
        regime_title = "⚖️ KUADRAN NETRAL: KONSOLIDASI FLUIDA"
        alt_permission = True
        btc_permission = True
        alt_priority = "MODERATE"
        advice = (
            "Arus dominasi bergerak seimbang di dalam rentang normal. "
            "Trading selektif dengan disiplin Stop Loss ketat dan konfluensi minimal 80%."
        )
        alt_bonus = 0
        sizing_mult = 1.0

    result = {
        "quadrant": quadrant,
        "regime_code": regime_code,
        "regime_title": regime_title,
        "advice": advice,
        "btc_price": btc_price,
        "btc_chg_24h": btc_chg_24h,
        "btc_d": round(btc_d_cur, 2),
        "btc_d_delta_1h": btc_d_delta_1h,
        "btc_d_delta_24h": btc_d_delta_24h,
        "usdt_d": round(usdt_d_cur, 2),
        "usdt_d_delta_1h": usdt_d_delta_1h,
        "usdt_d_delta_24h": usdt_d_delta_24h,
        "usdt_status": usdt_status,
        "usdt_bias": usdt_bias,
        "eth_d": round(dom_data["eth_d"], 2),
        "sol_d": round(dom_data.get("sol_d", 0.0), 2),
        "total_stable_d": round(dom_data["total_stable_d"], 2),
        "total_mcap_usd": dom_data["total_mcap_usd"],
        "mcap_chg_24h": round(dom_data["mcap_chg_24h"], 2),
        "alt_permission": alt_permission,
        "btc_permission": btc_permission,
        "alt_priority": alt_priority,
        "alt_bonus": alt_bonus,
        "sizing_mult": sizing_mult,
        "timestamp": now,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    _CACHE["data"] = result
    _CACHE["timestamp"] = now
    return result

def filter_candidate_by_dominance(candidate):
    """
    Evaluates proposed candidate setup against Dominance Compass rules:
    - Blocks Altcoin Longs during Kuadran 1 (BTC Vampire) or Kuadran 3 (Altcoin Bloodbath)
    - Allows BTC Longs
    - Allows Short setups (Hedging)
    Returns: (is_approved: bool, rationale: str, score_bonus: int)
    """
    compass = get_dominance_compass()
    sym = candidate.get("symbol", "")
    base = clean_coin(sym)
    side = candidate.get("side", "LONG").upper()

    is_altcoin = base not in ["BTC"]

    if side in ["BUY", "LONG"]:
        # Rule 1: Kuadran 3 (Altcoin Bloodbath) -> Strictly ban Altcoin Longs
        if compass["regime_code"] == "ALTCOIN_BLOODBATH" and is_altcoin:
            return False, (
                f"🚨 [DOMINANCE COMPASS GUARD] {sym} LONG di-skip: Berada di Kuadran 3 (ALTCOIN BLOODBATH). "
                f"BTC.D sedang naik ({compass['btc_d']}%) saat BTC turun ({compass['btc_chg_24h']:+.2f}%). "
                f"Altcoin rentan tersapu likuidasi 2x-3x lipat!"
            ), compass["alt_bonus"]

        # Rule 2: Kuadran 1 (BTC Vampire) -> Block Altcoin Longs, prioritize BTC
        if compass["regime_code"] == "BTC_VAMPIRE" and is_altcoin:
            return False, (
                f"🩸 [DOMINANCE COMPASS GUARD] {sym} LONG di-skip: Berada di Kuadran 1 (BITCOIN VAMPIRE). "
                f"Likuiditas tersedot penuh ke BTC ({compass['btc_d']}% BTC.D). Altcoin tertinggal dan rawan koreksi."
            ), compass["alt_bonus"]

        # Rule 3: Kuadran 4 (Capital Flight) -> Extreme risk-off
        if compass["regime_code"] == "CAPITAL_FLIGHT" and is_altcoin:
            return False, (
                f"💸 [DOMINANCE COMPASS GUARD] {sym} LONG di-skip: Berada di Kuadran 4 (CAPITAL FLIGHT). "
                f"Modal pasar lari ke USDT (USDT.D: {compass['usdt_d']}%). Hindari membeli di pasar yang kekurangan likuiditas."
            ), compass["alt_bonus"]

        # Rule 4: Kuadran 2 (Altseason Boom) -> Green light with bonus
        if compass["regime_code"] == "ALTSEASON_BOOM" and is_altcoin:
            return True, "🚀 [DOMINANCE COMPASS] Lolos: Kuadran 2 Altseason Boom aktif! Altcoins didukung aliran modal penuh.", compass["alt_bonus"]

    return True, f"✅ [DOMINANCE COMPASS] Setup {sym} {side} selaras dengan kompas pasar.", compass["alt_bonus"]

def format_telegram_compass(compass_info=None):
    """
    Formats institutional Telegram card for BTC.D & USDT.D Market Compass.
    """
    if not compass_info:
        compass_info = get_dominance_compass()

    btc_d = compass_info["btc_d"]
    usdt_d = compass_info["usdt_d"]
    eth_d = compass_info["eth_d"]
    sol_d = compass_info["sol_d"]
    btc_p = compass_info["btc_price"]
    btc_chg = compass_info["btc_chg_24h"]
    mcap_t = compass_info["total_mcap_usd"] / 1e12
    mcap_chg = compass_info["mcap_chg_24h"]

    btcd_arrow = "📈" if compass_info["btc_d_delta_1h"] > 0 else ("📉" if compass_info["btc_d_delta_1h"] < 0 else "➡️")
    usdtd_arrow = "📈" if compass_info["usdt_d_delta_1h"] > 0 else ("📉" if compass_info["usdt_d_delta_1h"] < 0 else "➡️")

    btc_blocks = int(round((btc_d / 70.0) * 10))
    btc_bar = "🟧" * min(10, max(1, btc_blocks)) + "⬜" * max(0, 10 - btc_blocks)

    usdt_blocks = int(round((usdt_d / 12.0) * 10))
    usdt_bar = "🟩" * min(10, max(1, usdt_blocks)) + "⬜" * max(0, 10 - usdt_blocks)

    return (
        f"🧭 <b>BTC.D & USDT.D MARKET COMPASS</b>\n"
        f"<i>Akademi Crypto Macro Top-Down Analysis (Module 01)</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>{compass_info['regime_title']}</b>\n\n"
        f"📊 <b>Peta Dominasi Modal Global:</b>\n"
        f"• <b>BTC Dominance (BTC.D):</b> <code>{btc_d:.2f}%</code> {btcd_arrow}\n"
        f"  {btc_bar} (1H: <code>{compass_info['btc_d_delta_1h']:+.3f}%</code>)\n\n"
        f"• <b>USDT Dominance (USDT.D):</b> <code>{usdt_d:.2f}%</code> {usdtd_arrow}\n"
        f"  {usdt_bar} (Total Stable: <code>{compass_info['total_stable_d']:.2f}%</code>)\n\n"
        f"• <b>Aset Lain:</b> ETH: <code>{eth_d:.2f}%</code> | SOL: <code>{sol_d:.2f}%</code>\n"
        f"• <b>Total Market Cap:</b> <code>${mcap_t:.2f}T</code> (<code>{mcap_chg:+.2f}% 24h</code>)\n"
        f"• <b>BTC Benchmark:</b> <code>${btc_p:,.2f}</code> (<code>{btc_chg:+.2f}% 24h</code>)\n\n"
        f"⚡ <b>Sentimen Arus Kas (USDT.D):</b>\n"
        f"{compass_info['usdt_status']}\n\n"
        f"🎯 <b>Rekomendasi Alokasi Akademi Crypto:</b>\n"
        f"• Izin Long Altcoin : <b>{'✅ DIIZINKAN' if compass_info['alt_permission'] else '🚫 DIBLOKIR OTOMATIS'}</b>\n"
        f"• Prioritas Altcoin : <b>{compass_info['alt_priority']}</b>\n"
        f"• Multiplier Risiko : <code>{compass_info['sizing_mult']}x</code>\n\n"
        f"💡 <i>{compass_info['advice']}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕒 <i>Diperbarui: {compass_info['updated_at']}</i>"
    )

if __name__ == "__main__":
    comp = get_dominance_compass()
    print(format_telegram_compass(comp))
    cand_alt = {"symbol": "DOGEUSDT", "side": "LONG", "base": "DOGE"}
    ok, rsn, bonus = filter_candidate_by_dominance(cand_alt)
    print("\nCandidate Alt Test:", ok, "Bonus:", bonus, "->", rsn)
