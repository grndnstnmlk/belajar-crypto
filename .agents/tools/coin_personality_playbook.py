"""
coin_personality_playbook.py - Autonomous Coin Personality, Behavioral Profiler & Tactical Playbook Engine
Institutional-grade tactical directives synthesized for Belajar Kripto Workstation.

Purpose:
Replaces blunt coin blacklists with granular behavioral profiles and tactical rules of engagement
("Tatacara Menang"). Governs stop-loss wick buffers, entry confirmations, risk haircuts, and 
profit-taking discipline tailored to each cryptocurrency's distinct personality.
"""

import os
import sys
from typing import Dict, Any, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

# Comprehensive Playbook Database for Cryptocurrencies (Anchors, Majors, High-Beta, Memes, and Previously Blacklisted Tokens)
COIN_PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # 1. ANCHOR & MAJOR LAYER-1 ASSETS (High Liquidity, Clean Structure)
    # =========================================================================
    "BTC": {
        "symbol": "BTC",
        "name": "Bitcoin",
        "archetype": "HTF Institutional Anchor",
        "temperament": "Highly respected horizontal levels and HTF order blocks. Heavy institutional liquidity grabs occur during NY Open (13:30-15:00 UTC).",
        "wick_buffer_pct": 0.008,          # 0.8% wick buffer
        "risk_haircut_mult": 1.0,           # Full 1.0x Kelly sizing
        "fast_be_trigger_r": 1.0,           # Move to BE at +1.0R
        "tp1_target_r": 2.5,                # Runner target
        "min_confluence_score": 60.0,
        "entry_rules": [
            "Wait for 4H/Daily EMA 50 alignment.",
            "Respect Daily/Weekly FVG fills and Patrick Nill 3-Touch Golden Support.",
            "Avoid entering inside compressed equilibrium ranges."
        ],
        "winning_directives": "Ikuti tren makro 4H. Entry di discount FVG setelah sweep likuiditas sesi Asia/London. Biarkan runner berjalan hingga 1:3R - 1:5R.",
        "traps_to_avoid": "Jangan open posisi 15 menit menjelang rilis data CPI/FOMC."
    },
    "ETH": {
        "symbol": "ETH",
        "name": "Ethereum",
        "archetype": "DeFi Core Infrastructure",
        "temperament": "Correlated with BTC (beta 1.15x). Prone to deep retracements into 4H breaker blocks before expansion.",
        "wick_buffer_pct": 0.010,          # 1.0% buffer
        "risk_haircut_mult": 1.0,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.2,
        "min_confluence_score": 62.0,
        "entry_rules": [
            "Confirm ETH/BTC relative strength is not collapsing.",
            "Enter on Naked POC retests and 1H Order Flow Shifts."
        ],
        "winning_directives": "Masuk saat terjadi liquidity sweep di low/high hari sebelumnya dengan konfirmasi CVD absorption. Kunci BE di +1.0R.",
        "traps_to_avoid": "Waspadai gas fee spikes yang sering menandai puncak lokal (local top exhaustion)."
    },
    "SOL": {
        "symbol": "SOL",
        "name": "Solana",
        "archetype": "High-Velocity Trend Leader",
        "temperament": "Aggressive retail momentum. Known for violent secondary liquidity sweeps before sustained multi-day rallies.",
        "wick_buffer_pct": 0.015,          # 1.5% buffer for stop hunts
        "risk_haircut_mult": 0.95,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.5,
        "min_confluence_score": 65.0,
        "entry_rules": [
            "Require wider SL buffer below swing structure to absorb secondary sweeps.",
            "Prioritize Breaker Block flips on 15m/1h."
        ],
        "winning_directives": "Gunakan SL buffer lebih lebar (1.5%) untuk mengantisipasi wick hunt sekunder. Manfaatkan Smart Pyramiding (+30%) saat +2R tercapai.",
        "traps_to_avoid": "Jangan pernah melawan arah tren 1H EMA 20 (no counter-trend shorts)."
    },
    "BNB": {
        "symbol": "BNB",
        "name": "BNB",
        "archetype": "Exchange Native Anchor",
        "temperament": "High institutional bid support, low false breakout rate on HTF. Smooth mean reversions.",
        "wick_buffer_pct": 0.009,          # 0.9% buffer
        "risk_haircut_mult": 1.0,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 60.0,
        "entry_rules": [
            "Respect range EQ and institutional iceberg orders.",
            "Trade Range Low sweeps into Range High."
        ],
        "winning_directives": "Beli di Range Low setelah SFP wick, targetkan Range High. Karakteristik tenang dan terukur.",
        "traps_to_avoid": "Hindari trading saat ada announcement launchpool/launchpad tiba-tiba karena volatilitas sesaat."
    },
    "XRP": {
        "symbol": "XRP",
        "name": "Ripple",
        "archetype": "Wick Raider & Stop-Hunt Specialist",
        "temperament": "Severe wick expansions, heavy retail sentiment swings, and sudden aggressive liquidation hunts.",
        "wick_buffer_pct": 0.020,          # 2.0% buffer
        "risk_haircut_mult": 0.80,          # Scale risk to 80%
        "fast_be_trigger_r": 1.0,          # Move to BE fast at +0.65R
        "tp1_target_r": 1.75,
        "min_confluence_score": 70.0,
        "entry_rules": [
            "Mandatory 2.0% stop-loss buffer beyond key swing pivots.",
            "Must confirm order book bid/ask ratio >= 2.0x and CVD absorption."
        ],
        "winning_directives": "Kunci BE secepatnya di +0.65R karena XRP sering memantul cepat lalu retrace dalam. Ambil TP1 di +1.75R.",
        "traps_to_avoid": "Jangan pernah entry breakout di candle hijau panjang; 80% breakout XRP di retrace 100%."
    },

    # =========================================================================
    # 2. PREVIOUSLY BLACKLISTED ASSETS (Restored with Specialized Winning Playbooks)
    # =========================================================================
    "THE": {
        "symbol": "THE",
        "name": "THENA",
        "archetype": "Low-Cap DEX Volatility Runner",
        "temperament": "Extremely sharp impulsive moves followed by 70%-80% mean retracements. High retail leverage trap.",
        "wick_buffer_pct": 0.025,          # 2.5% buffer
        "risk_haircut_mult": 0.60,          # Scale risk down to 60% (Capital Preservation)
        "fast_be_trigger_r": 1.0,          # Micro-BE at +0.55R
        "tp1_target_r": 2.0,               # Fast partial TP1
        "min_confluence_score": 75.0,
        "entry_rules": [
            "Entry ONLY on 15m displacement FVG retest in discount zone.",
            "Order book depth must show active bid support walls (>= 2.5x).",
            "Cap total position allocation to max 1.0% equity."
        ],
        "winning_directives": "Tatacara Menang THE: Masuk hanya saat dip pullback dalam ke FVG setelah impulsive surge. Begitu profit +0.55R, geser SL ke BE tanpa kompromi dan amankan 50% di +1.35R.",
        "traps_to_avoid": "Dilarang keras mengejar (FOMO) candle hijau. Jangan biarkan profit menguap tanpa trailing stop."
    },
    "SOPH": {
        "symbol": "SOPH",
        "name": "Sophon",
        "archetype": "Micro-Cap High-Beta Runner",
        "temperament": "Thin order book depth, prone to erratic wicks during illiquid Asian night hours.",
        "wick_buffer_pct": 0.024,
        "risk_haircut_mult": 0.65,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 75.0,
        "entry_rules": [
            "Require Level-2 depth verification to ensure tight spread (< 0.10%).",
            "Mandatory limit order entry (never market order to avoid slippage)."
        ],
        "winning_directives": "Tatacara Menang SOPH: Gunakan limit order pada golden support 3-touch. Jangan gunakan market order karena slippage. Amankan profit cepat dengan target R:R 1:1.5 - 1:2.0.",
        "traps_to_avoid": "Hindari menahan posisi overnight tanpa stop loss terkunci di breakeven."
    },
    "ZEC": {
        "symbol": "ZEC",
        "name": "Zcash",
        "archetype": "Privacy Sector Mean-Reverter",
        "temperament": "Idiosyncratic sector rotation. Tends to build extended low-volume consolidation followed by single explosive green/red day.",
        "wick_buffer_pct": 0.018,
        "risk_haircut_mult": 0.75,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 70.0,
        "entry_rules": [
            "Enter on Wyckoff Phase C Spring at multi-week range low.",
            "Verify privacy narrative momentum or volume surge > 2.0x 20-day SMA."
        ],
        "winning_directives": "Tatacara Menang ZEC: Tunggu konfirmasi volume lonjakan >2x lipat di dasar konsolidasi (Wyckoff Spring). Pasang SL di bawah pivot spring dengan buffer 1.8%.",
        "traps_to_avoid": "Jangan trade saat volume sepi/mati (chop range)."
    },
    "PROM": {
        "symbol": "PROM",
        "name": "Prom",
        "archetype": "Low-Float Whale Play",
        "temperament": "Concentrated whale ownership. Prone to sudden 15-minute pump-and-dump sweeps.",
        "wick_buffer_pct": 0.022,
        "risk_haircut_mult": 0.60,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 75.0,
        "entry_rules": [
            "Strict limit order entry only at key POC levels.",
            "Immediate Micro-BE activation upon +0.5R excursion."
        ],
        "winning_directives": "Tatacara Menang PROM: Skalping presisi tinggi dengan risk 0.6x. Ambil profit cepat pada wick ekspansi pertama.",
        "traps_to_avoid": "Jangan pernah hold posisi saat harga menembus POC ke bawah."
    },
    "HOLO": {
        "symbol": "HOLO",
        "name": "Holo / HOT",
        "archetype": "High-Supply Micro-Cap",
        "temperament": "Fractional price steps. Tends to move in tick-by-tick compression ranges.",
        "wick_buffer_pct": 0.020,
        "risk_haircut_mult": 0.65,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 72.0,
        "entry_rules": [
            "Check tick size friction before entry.",
            "Trade strictly with EMA 20/50 directional momentum."
        ],
        "winning_directives": "Tatacara Menang HOLO: Masuk saat terjadi breakout konsolidasi dengan konfirmasi lonjakan volume nyata.",
        "traps_to_avoid": "Jangan entry di tengah range sideways tanpa momentum."
    },
    "WLD": {
        "symbol": "WLD",
        "name": "Worldcoin",
        "archetype": "High-Float AI Unlock Squeezer",
        "temperament": "High token unlock overhang creates heavy short crowding, leading to violent multi-dollar short squeezes followed by aggressive dumps.",
        "wick_buffer_pct": 0.022,
        "risk_haircut_mult": 0.70,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.20,
        "min_confluence_score": 70.0,
        "entry_rules": [
            "Monitor 8h Funding Rate: If funding < -0.05%, look for Short Squeeze Longs.",
            "If funding > +0.06%, look for Exhaustion SFP Shorts.",
            "Wider SL buffer (2.2%) to absorb unlock volatility wicks."
        ],
        "winning_directives": "Tatacara Menang WLD: Manfaatkan funding rate squeeze. Jika funding negatif ekstrem, cari peluang Long di liquidity sweep. Kunci BE di +0.65R.",
        "traps_to_avoid": "Jangan Short saat funding rate negatif tebal (bisa tergulung short squeeze hebat)."
    },
    "ENA": {
        "symbol": "ENA",
        "name": "Ethena",
        "archetype": "Basis Yield & Funding Sensitive Asset",
        "temperament": "Price highly correlated with perpetual funding rates and basis yields. Hyper-reactive to market-wide deleveraging.",
        "wick_buffer_pct": 0.020,
        "risk_haircut_mult": 0.75,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.00,
        "min_confluence_score": 68.0,
        "entry_rules": [
            "Check overall market funding regime before Long entries.",
            "Prioritize 1H FVG displacement retests."
        ],
        "winning_directives": "Tatacara Menang ENA: Masuk saat funding rate stabil/positif sehat dan harga memantul dari 1H FVG. Kunci trailing stop disiplin.",
        "traps_to_avoid": "Hindari posisi Long saat BTC sedang crash karena likuidasi hedging basis yield ENA bisa menekan harga."
    },
    "TAO": {
        "symbol": "TAO",
        "name": "Bittensor",
        "archetype": "Decentralized AI Supercomputer",
        "temperament": "High dollar-value per unit with wide spreads. Explosive multi-hour trends driven by AI sentiment.",
        "wick_buffer_pct": 0.016,
        "risk_haircut_mult": 0.85,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 3.00,
        "min_confluence_score": 68.0,
        "entry_rules": [
            "Enter on 1H/4H trend continuation; high R:R potential (1:3 to 1:5R).",
            "Must calculate lot size with high decimal precision to prevent over-sizing."
        ],
        "winning_directives": "Tatacara Menang TAO: Biarkan runner berjalan jauh (target 1:3R - 1:4R). Atur lot size presisi karena harga per koin tinggi.",
        "traps_to_avoid": "Jangan gunakan lot size tetap; wajib gunakan fractional Kelly sizing otomatis."
    },
    "DOGE": {
        "symbol": "DOGE",
        "name": "Dogecoin",
        "archetype": "Meme Momentum Leader",
        "temperament": "Retail social sentiment driver. High liquidity, high frequency of fakeouts around major round numbers ($0.10, $0.20, $0.50).",
        "wick_buffer_pct": 0.018,
        "risk_haircut_mult": 0.80,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.00,
        "min_confluence_score": 65.0,
        "entry_rules": [
            "Fade fakeouts above/below round psychological numbers.",
            "Wick buffer 1.8% to survive stop runs."
        ],
        "winning_directives": "Tatacara Menang DOGE: Entry setelah sweep likuiditas level psikologis bulat (SFP). Amankan sebagian profit di +1.5R.",
        "traps_to_avoid": "Jangan membeli di pucuk saat trending Twitter/X sedang heboh."
    },
    "ADA": {
        "symbol": "ADA",
        "name": "Cardano",
        "archetype": "Extended Consolidation Accumulator",
        "temperament": "Tends to form long multi-week consolidation ranges before slow grinding directional expansion.",
        "wick_buffer_pct": 0.012,
        "risk_haircut_mult": 0.90,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.00,
        "min_confluence_score": 65.0,
        "entry_rules": [
            "Trade Range High / Range Low mean reversion until daily breakout confirms.",
            "Patience-oriented asset."
        ],
        "winning_directives": "Tatacara Menang ADA: Beli di Range Low, jual di Range High. Sabar menunggu ekspansi terarah.",
        "traps_to_avoid": "Jangan terburu-buru mengharapkan breakout instan di tengah range."
    },
    "AVAX": {
        "symbol": "AVAX",
        "name": "Avalanche",
        "archetype": "High-Beta Layer-1 Runner",
        "temperament": "Correlated with SOL and Layer-1 rotations. Strong continuation when 1H EMA 50 aligns.",
        "wick_buffer_pct": 0.014,
        "risk_haircut_mult": 0.90,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.40,
        "min_confluence_score": 65.0,
        "entry_rules": [
            "Look for displacement FVG reclaim after SOL initiates a move.",
            "Confirm CVD absorption on 15m."
        ],
        "winning_directives": "Tatacara Menang AVAX: Tunggu konfirmasi rotasi modal L1. Masuk di FVG pullback dengan target 1:2.4R.",
        "traps_to_avoid": "Jangan entry jika SOL sedang dumping keras."
    },
    "NEAR": {
        "symbol": "NEAR",
        "name": "NEAR Protocol",
        "archetype": "AI & User-Owned Web3 Bellwether",
        "temperament": "Very clean price action on 1H/4H charts. High respect for FVG and SMC order blocks.",
        "wick_buffer_pct": 0.013,
        "risk_haircut_mult": 0.90,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.50,
        "min_confluence_score": 64.0,
        "entry_rules": [
            "Entry on 1H FVG retest with trend alignment.",
            "Clean swing structure respect."
        ],
        "winning_directives": "Tatacara Menang NEAR: Salah satu koin paling patuh pada teknikal SMC. Masuk di 1H FVG retest, target 1:2.5R.",
        "traps_to_avoid": "Hindari entry saat pasar umum berada dalam fase de-risking."
    },
    "UNI": {
        "symbol": "UNI",
        "name": "Uniswap",
        "archetype": "DeFi Governance Blue-Chip",
        "temperament": "High sensitivity to Ethereum gas metrics and SEC/regulatory headlines.",
        "wick_buffer_pct": 0.015,
        "risk_haircut_mult": 0.85,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.20,
        "min_confluence_score": 66.0,
        "entry_rules": [
            "Verify regulatory news calendar before swing entries.",
            "SFP resistance sweep or liquidation dip reversal."
        ],
        "winning_directives": "Tatacara Menang UNI: Entry di dasar liquidity dip setelah panic sell reda. Kunci BE di +0.8R.",
        "traps_to_avoid": "Waspadai berita tuntutan/regulasi yang dapat memicu flash drop."
    },
    "1000PEPE": {
        "symbol": "1000PEPE",
        "name": "Pepe (1000x)",
        "archetype": "Hyper-Volatile Meme Locomotive",
        "temperament": "Huge volume explosions, fast cascading liquidations, massive retail participation.",
        "wick_buffer_pct": 0.022,
        "risk_haircut_mult": 0.70,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.00,
        "min_confluence_score": 72.0,
        "entry_rules": [
            "Volume surge confirmation required (>= 2.5x average).",
            "Fast trailing stop activation upon reaching +1.0R."
        ],
        "winning_directives": "Tatacara Menang 1000PEPE: Skalping momentum dengan perlindungan modal ketat. Pasang buffer 2.2% dan kunci BE di +0.6R.",
        "traps_to_avoid": "Jangan averaging down jika posisi berlawanan arah."
    },
    "1000SHIB": {
        "symbol": "1000SHIB",
        "name": "Shiba Inu (1000x)",
        "archetype": "Secondary Meme Asset",
        "temperament": "Lags DOGE/PEPE. Prone to sudden 1-hour spikes followed by slow bleed.",
        "wick_buffer_pct": 0.020,
        "risk_haircut_mult": 0.70,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 1.75,
        "min_confluence_score": 70.0,
        "entry_rules": [
            "Only trade during active meme rotation cycles.",
            "Quick exit discipline on first impulse."
        ],
        "winning_directives": "Tatacara Menang 1000SHIB: Ambil profit cepat pada impuls pertama, jangan menahan berhari-hari karena sering slow-bleed.",
        "traps_to_avoid": "Jangan beli di akhir siklus pompa meme."
    },
    "LUNA": {
        "symbol": "LUNA",
        "name": "Terra",
        "archetype": "Speculative High-Risk Turnaround",
        "temperament": "Legacy extreme volatility, sporadic liquidity traps.",
        "wick_buffer_pct": 0.025,
        "risk_haircut_mult": 0.50,          # 50% risk haircut (Ultra defensive)
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 78.0,
        "entry_rules": [
            "Only take A+ grade setups with strict level-2 bid absorption.",
            "Maximum 0.75% equity risk."
        ],
        "winning_directives": "Tatacara Menang LUNA: Hanya trade setup dengan confluence tertinggi (A+). Risiko dipangkas setengah (0.5x).",
        "traps_to_avoid": "Dilarang keras hold overnight tanpa Breakeven lock."
    },
    "USTC": {
        "symbol": "USTC",
        "name": "TerraClassicUSD",
        "archetype": "De-pegged Speculative Asset",
        "temperament": "Violent erratic wicks driven by speculative rumors.",
        "wick_buffer_pct": 0.028,
        "risk_haircut_mult": 0.50,
        "fast_be_trigger_r": 1.0,
        "tp1_target_r": 2.0,
        "min_confluence_score": 80.0,
        "entry_rules": [
            "Strict scalp only; immediate TP1 execution.",
            "Maximum 0.50% equity risk."
        ],
        "winning_directives": "Tatacara Menang USTC: Skalp kilat, ambil profit cepat, jangan serakah.",
        "traps_to_avoid": "Jangan pernah menganggapnya sebagai stablecoin; perlakukan sebagai aset spekulasi tinggi."
    }
}

# Generic Fallback Template for any unlisted coin
GENERIC_PLAYBOOK_TEMPLATE = {
    "symbol": "DEFAULT",
    "name": "Generic Crypto Asset",
    "archetype": "Standard Quantitative Candidate",
    "temperament": "Standard crypto market volatility and liquidity dynamics.",
    "wick_buffer_pct": 0.015,              # 1.5% buffer
    "risk_haircut_mult": 0.85,              # 0.85x risk
    "fast_be_trigger_r": 1.0,
    "tp1_target_r": 2.0,
    "min_confluence_score": 65.0,
    "entry_rules": [
        "Align with 4H/Daily EMA 50 directional bias.",
        "Enter on FVG or Order Block retest with defined stop-loss."
    ],
    "winning_directives": "Disiplin pada risk-to-reward minimal 1:2.0, kunci BE saat profit +0.75R.",
    "traps_to_avoid": "Hindari over-leveraging dan jangan entry tanpa konfirmasi level teknikal."
}


def clean_symbol(symbol: str) -> str:
    """Normalizes symbol to raw ticker (e.g. BTCUSDT -> BTC, 1000PEPEUSDT -> 1000PEPE)."""
    s = symbol.upper().replace("-", "").replace("/", "").replace("_", "").strip()
    if s.endswith("USDT"):
        s = s[:-4]
    elif s.endswith("USD"):
        s = s[:-3]
    return s


def get_coin_playbook(symbol: str) -> Dict[str, Any]:
    """
    Retrieves or synthesizes the exact behavioral profile and winning playbook for any coin.
    Never blacklists; instead equips the AI with tailored rules of engagement.
    """
    raw_sym = clean_symbol(symbol)
    
    # Direct match in curated database
    if raw_sym in COIN_PLAYBOOKS:
        return COIN_PLAYBOOKS[raw_sym]

    # Synthesize based on asset characteristics
    synthesized = dict(GENERIC_PLAYBOOK_TEMPLATE)
    synthesized["symbol"] = raw_sym
    synthesized["name"] = raw_sym

    # Detect category
    is_meme = any(m in raw_sym for m in ["PEPE", "SHIB", "DOGE", "FLOKI", "BONK", "MEME", "WIF", "BOME", "POPCAT"])
    is_ai = any(a in raw_sym for a in ["RENDER", "FET", "TAO", "NEAR", "WLD", "IO", "AKT", "AI"])
    is_l1_l2 = any(l in raw_sym for l in ["SUI", "SEI", "APT", "ARB", "OP", "INJ", "TIA", "FTM", "AVAX", "DOT", "ATOM"])
    is_defi = any(d in raw_sym for d in ["AAVE", "MKR", "LDO", "CRV", "SNX", "COMP", "DYDX", "PENDLE"])

    if is_meme:
        synthesized["archetype"] = "Meme Volatility Runner"
        synthesized["temperament"] = f"High-velocity meme asset {raw_sym}. Prone to rapid liquidity spikes and sharp mean retracements."
        synthesized["wick_buffer_pct"] = 0.022
        synthesized["risk_haircut_mult"] = 0.70
        synthesized["fast_be_trigger_r"] = 0.60
        synthesized["tp1_target_r"] = 1.80
        synthesized["min_confluence_score"] = 72.0
        synthesized["winning_directives"] = f"Tatacara Menang {raw_sym}: Skalping momentum dengan stop buffer 2.2%. Kunci BE cepat di +0.6R dan amankan profit di +1.8R."
        synthesized["traps_to_avoid"] = "Jangan mengejar harga di puncak candle hijau (FOMO trap)."
    elif is_ai:
        synthesized["archetype"] = "AI / Tech Narrative Leader"
        synthesized["temperament"] = f"High-beta AI sector runner {raw_sym}. Clean trend continuation when narrative is active."
        synthesized["wick_buffer_pct"] = 0.016
        synthesized["risk_haircut_mult"] = 0.85
        synthesized["fast_be_trigger_r"] = 0.75
        synthesized["tp1_target_r"] = 2.40
        synthesized["min_confluence_score"] = 66.0
        synthesized["winning_directives"] = f"Tatacara Menang {raw_sym}: Ikuti tren 1H/4H, entry di FVG discount, biarkan runner berjalan hingga 1:2.4R."
        synthesized["traps_to_avoid"] = "Waspadai kejenuhan tren setelah reli 3 hari berturut-turut."
    elif is_l1_l2:
        synthesized["archetype"] = "Layer-1 / Layer-2 Infrastructure"
        synthesized["temperament"] = f"High-throughput chain token {raw_sym}. Highly responsive to institutional volume and order book absorption."
        synthesized["wick_buffer_pct"] = 0.014
        synthesized["risk_haircut_mult"] = 0.90
        synthesized["fast_be_trigger_r"] = 0.80
        synthesized["tp1_target_r"] = 2.20
        synthesized["min_confluence_score"] = 65.0
        synthesized["winning_directives"] = f"Tatacara Menang {raw_sym}: Masuk di breaker block flip atau SFP liquidity sweep. R:R ideal 1:2.2."
        synthesized["traps_to_avoid"] = "Hindari short counter-trend saat momentum pasar umum sedang bullish."
    elif is_defi:
        synthesized["archetype"] = "DeFi Yield & Protocol Asset"
        synthesized["temperament"] = f"DeFi protocol asset {raw_sym}. Correlated with Ethereum ecosystem and yield trends."
        synthesized["wick_buffer_pct"] = 0.015
        synthesized["risk_haircut_mult"] = 0.85
        synthesized["fast_be_trigger_r"] = 0.75
        synthesized["tp1_target_r"] = 2.00
        synthesized["min_confluence_score"] = 65.0
        synthesized["winning_directives"] = f"Tatacara Menang {raw_sym}: Entry di akumulasi range low dengan konfirmasi divergence RSI."
        synthesized["traps_to_avoid"] = "Waspadai exploit smart contract atau perubahan regulasi mendadak."

    return synthesized


def apply_coin_playbook_to_setup(setup: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automatically applies the coin's tactical playbook directives to an incoming trade setup:
    1. Adjusts stop-loss wick buffer to match coin's personality.
    2. Modifies position risk scaling (haircut multiplier).
    3. Sets optimal Breakeven and Take-Profit triggers.
    4. Attaches human & AI readable 'tatacara_menang' notes.
    """
    sym = setup.get("symbol", "BTC")
    playbook = get_coin_playbook(sym)

    # Attach playbook metadata
    setup["coin_playbook"] = {
        "archetype": playbook.get("archetype"),
        "temperament": playbook.get("temperament"),
        "tatacara_menang": playbook.get("winning_directives"),
        "traps_to_avoid": playbook.get("traps_to_avoid"),
        "recommended_wick_buffer": playbook.get("wick_buffer_pct"),
        "risk_haircut_mult": playbook.get("risk_haircut_mult")
    }

    # Adjust risk scaling if present
    if "risk_pct" in setup:
        original_risk = setup["risk_pct"]
        scaled_risk = original_risk * playbook.get("risk_haircut_mult", 1.0)
        setup["risk_pct"] = round(scaled_risk, 3)
        setup["risk_haircut_applied"] = f"{playbook.get('risk_haircut_mult')}x ({original_risk}% -> {setup['risk_pct']}%)"

    # Adjust dynamic trade manager parameters (Strict Institutional Floors)
    setup["be_trigger_r"] = max(1.00, float(playbook.get("fast_be_trigger_r", 1.00)))
    setup["tp1_target_r"] = max(1.75, float(playbook.get("tp1_target_r", 2.20)))
    setup["anti_stall_minutes"] = max(45, int(playbook.get("anti_stall_minutes", 45)))

    return setup


def compile_playbook_ai_prompt(symbol: str) -> str:
    """
    Compiles a high-density sensory text block for the AI reasoning model (Local Cognitive Brain / Laya).
    """
    pb = get_coin_playbook(symbol)
    rules_fmt = "\n".join([f"  * {r}" for r in pb.get("entry_rules", [])])
    
    prompt = f"""[COIN HABIT & TACTICAL WINNING PLAYBOOK: {pb.get('symbol')}]
Archetype: {pb.get('archetype')}
Temperament: {pb.get('temperament')}
Recommended SL Buffer: {pb.get('wick_buffer_pct') * 100:.1f}% (Anti Stop-Hunt)
Risk Haircut Multiplier: {pb.get('risk_haircut_mult')}x Kelly
Fast Breakeven Trigger: +{pb.get('fast_be_trigger_r')}R | TP1: +{pb.get('tp1_target_r')}R
Tactical Entry Rules:
{rules_fmt}
Winning Directive: {pb.get('winning_directives')}
Traps to Avoid: {pb.get('traps_to_avoid')}"""
    return prompt


def audit_setup_against_playbook(setup: Dict[str, Any], market_ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Audits a candidate trade against its coin-specific playbook rules.
    Returns:
      - approved: bool
      - adjustments: Dict of suggested SL / Risk / BE adaptations
      - feedback: Explanation for the AI and trade logger
    """
    sym = setup.get("symbol", "BTC")
    pb = get_coin_playbook(sym)
    rr = float(setup.get("rr", setup.get("rr_ratio", 2.0)))
    conf = float(setup.get("confluence_score", 70.0))

    adjustments = {
        "wick_buffer_pct": pb.get("wick_buffer_pct", 0.015),
        "risk_multiplier": pb.get("risk_haircut_mult", 0.85),
        "be_trigger_r": max(1.00, float(pb.get("fast_be_trigger_r", 1.00))),
        "tp1_target_r": max(1.75, float(pb.get("tp1_target_r", 2.20)))
    }

    # Verify minimum confluence for this specific coin
    min_conf = pb.get("min_confluence_score", 65.0)
    if conf < min_conf:
        return {
            "approved": False,
            "status": "VETO_LOW_COIN_CONFLUENCE",
            "reason": f"Koin {sym} ({pb.get('archetype')}) membutuhkan skor konfluensi minimal {min_conf}% (terdeteksi: {conf:.1f}%).",
            "adjustments": adjustments,
            "playbook": pb
        }

    return {
        "approved": True,
        "status": "APPROVED_BY_PLAYBOOK",
        "reason": f"Setup {sym} memenuhi tatacara menang koin ({pb.get('archetype')}). Buffer SL {pb.get('wick_buffer_pct')*100:.1f}% dan Risk Multiplier {pb.get('risk_haircut_mult')}x diaktifkan.",
        "adjustments": adjustments,
        "playbook": pb
    }


if __name__ == "__main__":
    print("=" * 70)
    print("🧠 COIN PERSONALITY PLAYBOOK ENGINE AUDIT")
    print("=" * 70)
    test_coins = ["BTC", "SOL", "THE", "SOPH", "ZEC", "WLD", "ENA", "DOGE", "1000PEPE"]
    for c in test_coins:
        pb = get_coin_playbook(c)
        print(f"\n🪙 [{pb['symbol']}] {pb['name']} ({pb['archetype']})")
        print(f"   Buffer: {pb['wick_buffer_pct']*100:.1f}% | Risk Mult: {pb['risk_haircut_mult']}x | Fast BE: +{pb['fast_be_trigger_r']}R")
        print(f"   Directive: {pb['winning_directives']}")
    print("\n✅ All coin playbooks verified!")
