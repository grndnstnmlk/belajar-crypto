import sys
import json
import urllib.request

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Top coins on Tokocrypto (IDR pairs available)
COINS = [
    ("SOL", "SOL/IDR"),
    ("ARB", "ARB/IDR"),
    ("XRP", "XRP/IDR"),
    ("DOGE", "DOGE/IDR"),
    ("ADA", "ADA/IDR"),
    ("ETH", "ETH/IDR"),
    ("BTC", "BTC/IDR"),
    ("AVAX", "AVAX/IDR"),
    ("SUI", "SUI/IDR")
]

headers = {"User-Agent": "Mozilla/5.0"}

def analyze_coin(base, idr_pair):
    url = f"https://www.okx.com/api/v5/market/candles?instId={base}-USDT&bar=1H&limit=30"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))["data"]
            closes = [float(c[4]) for c in data]
            highs = [float(c[2]) for c in data]
            lows = [float(c[3]) for c in data]
            cur = closes[0]
            
            # RSI 14
            deltas = [closes[i] - closes[i+1] for i in range(len(closes)-1)]
            period = 14
            gains = [max(d, 0) for d in deltas[:period]]
            losses = [max(-d, 0) for d in deltas[:period]]
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            rs = avg_gain / (avg_loss or 0.0001)
            rsi = round(100 - (100 / (1 + rs)), 1)
            
            h24 = max(highs[:24])
            l24 = min(lows[:24])
            # Posisi harga di range 24h (0% = di support terendah, 100% = di puncak tertinggi)
            range_pct = ((cur - l24) / (h24 - l24)) * 100 if (h24 > l24) else 50.0
            
            # 24h Price Change
            open_24h = float(data[min(23, len(data)-1)][1])
            chg_pct = ((cur - open_24h) / open_24h) * 100 if open_24h > 0 else 0.0
            
            return {
                "base": base,
                "idr_pair": idr_pair,
                "price_usd": cur,
                "rsi_1h": rsi,
                "range_pct": range_pct,
                "chg_pct": chg_pct,
                "low_usd": l24,
                "high_usd": h24
            }
    except Exception as e:
        return None

print("\n================================================================================")
print("       📊 SCREENER INTELIJEN PASAR - MENCARI KOIN SEDANG DISKON / PULLBACK")
print("================================================================================")
print(f"{'Koin':<6} | {'Pair IDR':<10} | {'Harga ($)':<12} | {'1H RSI':<8} | {'Posisi dr Low':<14} | {'Status Setup'}")
print("-" * 75)

candidates = []
for base, idr_pair in COINS:
    res = analyze_coin(base, idr_pair)
    if res:
        candidates.append(res)

# Sort by lowest range_pct (paling dekat dengan area Support / dasar)
candidates.sort(key=lambda x: x["range_pct"])

for c in candidates:
    pos_str = f"{c['range_pct']:.1f}% dr Low"
    if c['range_pct'] <= 40 or c['rsi_1h'] <= 50:
        status = "🟢 DISKON / DEKAT SUPPORT (Layak Beli)"
    elif c['range_pct'] >= 80 or c['rsi_1h'] >= 70:
        status = "🔴 OVERBOUGHT / DI PUCUK (Hindari Beli)"
    else:
        status = "🟡 KONSOLIDASI TENGAH"
        
    print(f"{c['base']:<6} | {c['idr_pair']:<10} | ${c['price_usd']:<11.4f} | {c['rsi_1h']:<8} | {pos_str:<14} | {status}")

print("================================================================================\n")
