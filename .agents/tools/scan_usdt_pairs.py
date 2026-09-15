import sys
import ccxt
import urllib3
import json
import urllib.request

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

urllib3.disable_warnings()

# Top potential altcoins with USDT pairs on Tokocrypto
CANDIDATE_SYMBOLS = [
    "SEI", "APT", "NEAR", "RENDER", "ARB", "SUI", "SOL", "TIA", "DOT", "LINK"
]

headers = {"User-Agent": "Mozilla/5.0"}

def run_scan():
    exchange = ccxt.tokocrypto({"enableRateLimit": True})
    if hasattr(exchange, "session") and exchange.session:
        exchange.session.verify = False

    markets = exchange.load_markets()

    print("\n================================================================================")
    print("       🌐 TOKOCRYPTO USDT MARKET SCANNER (MODAL: 11.30 USDT)")
    print("================================================================================")
    print(f"{'Pair':<12} | {'Harga ($)':<10} | {'1H RSI':<8} | {'Min Order':<10} | {'Status Setup'}")
    print("-" * 75)

    for base in CANDIDATE_SYMBOLS:
        pair_name = f"{base}/USDT"
        m = markets.get(pair_name)
        if not m:
            continue
            
        min_notional = 5.0
        for f in m["info"].get("filters", []):
            if f["filterType"] == "NOTIONAL":
                min_notional = float(f.get("minNotional", 5.0))

        # Fetch 1H candle & RSI from OKX
        try:
            url = f"https://www.okx.com/api/v5/market/candles?instId={base}-USDT&bar=1H&limit=30"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))["data"]
                closes = [float(c[4]) for c in data]
                cur = closes[0]
                
                # RSI 14
                deltas = [closes[i] - closes[i+1] for i in range(len(closes)-1)]
                period = 14
                gains = [max(d, 0) for d in deltas[:period]]
                losses = [max(-d, 0) for d in deltas[:period]]
                rs = (sum(gains)/period) / ((sum(losses)/period) or 0.0001)
                rsi = round(100 - (100 / (1 + rs)), 1)
                
                if rsi <= 55:
                    status = "🟢 DISKON / PANTULAN DARI DASAR (Ideal)"
                elif rsi >= 75:
                    status = "🔴 OVERBOUGHT / RAWAN KOREKSI"
                else:
                    status = "🟡 KONSOLIDASI SEHAT"
                    
                print(f"{pair_name:<12} | ${cur:<9.4f} | {rsi:<8} | ${min_notional:<9.1f} | {status}")
        except Exception as e:
            pass

    print("================================================================================\n")

if __name__ == "__main__":
    run_scan()
