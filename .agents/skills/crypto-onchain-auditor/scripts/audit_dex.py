"""
DEX Token & On-Chain Liquidity Auditor (Zero-Dependency)
Powered by DexScreener Public API.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Error] Failed to fetch {url}: {e}", file=sys.stderr)
        return None

def audit_pair(pair):
    base_token = pair.get("baseToken", {})
    quote_token = pair.get("quoteToken", {})
    chain = pair.get("chainId", "unknown").upper()
    dex = pair.get("dexId", "unknown").upper()
    price_usd = float(pair.get("priceUsd", 0) or 0)
    liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0) or 0)
    fdv = float(pair.get("fdv", 0) or 0)
    vol_24h = float(pair.get("volume", {}).get("h24", 0) or 0)
    price_chg_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0)
    txns_24h = pair.get("txns", {}).get("h24", {})
    buys_24h = txns_24h.get("buys", 0)
    sells_24h = txns_24h.get("sells", 0)

    print("\n=======================================================")
    print(f"       DEX SECURITY AUDIT: {base_token.get('symbol')} / {quote_token.get('symbol')}")
    print("=======================================================")
    print(f"Chain           : {chain}")
    print(f"DEX Protocol    : {dex}")
    print(f"Token Name      : {base_token.get('name')} ({base_token.get('symbol')})")
    print(f"Contract Address: {base_token.get('address')}")
    print(f"Current Price   : ${price_usd:,.6f}")
    print(f"24h Price Change: {price_chg_24h:+.2f}%")
    print(f"Liquidity (USD) : ${liquidity_usd:,.2f}")
    print(f"FDV             : ${fdv:,.2f}")
    print(f"24h Volume      : ${vol_24h:,.2f}")
    print(f"24h Transactions: {buys_24h} Buys | {sells_24h} Sells")

    # Risk Assessment
    print("\n--- Risk & Liquidity Health Assessment ---")
    warnings = []
    
    if liquidity_usd < 20_000:
        warnings.append("CRITICAL: Liquidity is below $20,000 USD (High slippage, easy rugpull)")
    elif liquidity_usd < 100_000:
        warnings.append("CAUTION: Liquidity between $20k-$100k. Limit position size strictly.")
    else:
        print(" [OK] Liquidity Depth: Healthy ($100k+ USD)")

    if fdv > 0 and liquidity_usd > 0:
        ratio = fdv / liquidity_usd
        if ratio > 50:
            warnings.append(f"WARNING: Extremely high FDV to Liquidity ratio ({ratio:.1f}x). Unbalanced market.")

    if buys_24h > 50 and sells_24h == 0:
        warnings.append("CRITICAL: 0 Sells detected with multiple Buys! Potential HONEYPOT!")

    if warnings:
        for w in warnings:
            print(f" [!] {w}")
    else:
        print(" [OK] No critical liquidity anomalies detected.")

    print(f"\nExternal Verify Links:")
    if chain.lower() == "solana":
        print(f" - RugCheck : https://rugcheck.xyz/tokens/{base_token.get('address')}")
    else:
        print(f" - Honeypot : https://honeypot.is/?address={base_token.get('address')}")
        print(f" - TokenSnif: https://tokensniffer.com/token/{chain.lower()}/{base_token.get('address')}")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="DEX Token & Liquidity Auditor")
    parser.add_argument("--query", type=str, default=None, help="Token ticker or name (e.g. JUP, PEPE)")
    parser.add_argument("--address", type=str, default=None, help="Token contract address")
    args = parser.parse_args()

    if args.address:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{args.address}"
    elif args.query:
        encoded = urllib.parse.quote(args.query)
        url = f"https://api.dexscreener.com/latest/dex/search?q={encoded}"
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Querying DexScreener for: {args.address or args.query}...")
    res = fetch_json(url)
    if not res or not res.get("pairs"):
        print("No DEX pairs found matching this query.")
        return

    # Sort pairs by highest liquidity
    pairs = sorted(res["pairs"], key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
    audit_pair(pairs[0])

if __name__ == "__main__":
    main()
