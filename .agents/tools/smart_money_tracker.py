"""
Smart Money & On-Chain Copy-Trade Auditor (Pelacak Whale & Copy-Trade Institusional)
Synthesized from DaviddTech FOMO Copy-Trading Strategy & Akademi Crypto Module 02 & 06.
Audits whale wallet consistency, follower crowding risk, token liquidity, and safe position sizing.
"""

import argparse
import json
import math
import os
import re
import ssl
import sys
import urllib.request

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

def audit_whale_metrics(wallet, win_rate, total_trades, realized_pnl, followers_count=250, avg_hold_minutes=120):
    print("\n" + "=" * 68)
    print(f"       🐋 ON-CHAIN SMART MONEY WALLET AUDIT")
    print(f"       Address/Trader : {wallet}")
    print("=" * 68)

    score = 100
    red_flags = []
    strengths = []

    # 1. Win Rate Check
    if win_rate >= 65.0:
        strengths.append(f"Win Rate Tinggi ({win_rate}%) — Menunjukkan akurasi eksekusi konsisten.")
    elif win_rate >= 50.0:
        score -= 10
        strengths.append(f"Win Rate Cukup ({win_rate}%).")
    else:
        score -= 35
        red_flags.append(f"Win Rate Rendah ({win_rate}% < 50%) — Risiko kekalahan beruntun tinggi.")

    # 2. Trade Count (Consistency vs 1-Hit Wonder)
    if total_trades >= 30:
        strengths.append(f"Sampel Transaksi Matang ({total_trades} trade) — Bukan keberuntungan sesaat.")
    elif total_trades >= 15:
        score -= 10
        strengths.append(f"Sampel Transaksi Cukup ({total_trades} trade).")
    else:
        score -= 30
        red_flags.append(f"Sampel Terlalu Sedikit ({total_trades} trade) — Kemungkinan '1-Hit Wonder' / Hoki semata.")

    # 3. Follower Crowding Risk (Anti-Frontrunning Rule)
    if followers_count < 1000:
        strengths.append(f"Anti-Crowding Aman ({followers_count} pengikut) — Risiko frontrunning & slippage rendah.")
    elif followers_count <= 2500:
        score -= 15
        red_flags.append(f"Pengikut Cukup Ramai ({followers_count} pengikut) — Waspada slippage saat mengeksekusi.")
    else:
        score -= 40
        red_flags.append(f"OVERCROWDED DANGER ({followers_count} pengikut) — Terlalu banyak bot copy trade! Anda berisiko membeli di pucuk dan menjadi Exit Liquidity whale.")

    # 4. Average Hold Duration
    if avg_hold_minutes < 10:
        score -= 20
        red_flags.append(f"Gaya Scalping Kilat ({avg_hold_minutes} menit) — Sulit di-copy manual/bot tanpa kena slippage.")
    else:
        strengths.append(f"Durasi Hold Sehat ({avg_hold_minutes} menit / ~{avg_hold_minutes/60:.1f} jam) — Aman untuk disalin.")

    score = max(0, min(100, score))

    if score >= 80:
        grade = "🌟 GRADE A+ (SANGAT DIREKOMENDASIKAN UNTUK COPY-TRADE)"
    elif score >= 65:
        grade = "🟢 GRADE B (LAYAK DIIKUTI DENGAN ALOKASI KECIL)"
    elif score >= 50:
        grade = "🟡 GRADE C (HIGH RISK / OVERCROWDED - PERLU FILTER KETAT)"
    else:
        grade = "🔴 GRADE D (REJECT / TIDAK LAYAK DIIKUTI)"

    print(f"Skor Kelayakan Copy   : {score} / 100")
    print(f"Kualifikasi Akhir     : {grade}")
    print("-" * 68)
    print("📊 Parameter Statistik:")
    print(f" * Win Rate           : {win_rate}%")
    print(f" * Total Selesai      : {total_trades} Transaksi")
    print(f" * Total Realized PnL : {'+' if realized_pnl>=0 else ''}${realized_pnl:,.2f}")
    print(f" * Jumlah Copy-Trader : {followers_count:,} Pengikut")
    print(f" * Rata-rata Durasi   : {avg_hold_minutes} Menit")
    print("-" * 68)

    print("✅ Keunggulan Terverifikasi:")
    for s in strengths:
        print(f"  [+] {s}")

    if red_flags:
        print("\n⚠️ Peringatan Risiko (Red Flags):")
        for r in red_flags:
            print(f"  [-] {r}")
    print("=" * 68 + "\n")

    return {"score": score, "grade": grade, "red_flags": red_flags}

def audit_binance_lead_trader(name, roi_90d, mdd, sharpe, win_rate, leverage=10, trading_days=90):
    print("\n" + "=" * 68)
    print(f"       🏛️ BINANCE COPY TRADING — LEAD TRADER AUDIT")
    print(f"       Nickname / Trader : {name}")
    print("=" * 68)

    score = 100
    red_flags = []
    strengths = []

    # MDD Check (Most Important)
    if mdd <= 12.0:
        strengths.append(f"Max Drawdown Sangat Rendah ({mdd}%) — Disiplin manajemen risiko tingkat tinggi.")
    elif mdd <= 20.0:
        strengths.append(f"Max Drawdown Sehat ({mdd}%).")
    elif mdd <= 30.0:
        score -= 20
        red_flags.append(f"Max Drawdown Agak Lebar ({mdd}%) — Waspada penurunan modal saat badai pasar.")
    else:
        score -= 50
        red_flags.append(f"BAHAYA DRAWDOWN EKSTRIM ({mdd}% > 30%) — Tanda trader martingal / menahan floating loss!")

    # Sharpe Ratio Check
    if sharpe >= 2.0:
        strengths.append(f"Sharpe Ratio Sempurna ({sharpe}) — Keuntungan konsisten dengan risiko minimal.")
    elif sharpe >= 1.2:
        strengths.append(f"Sharpe Ratio Sehat ({sharpe}).")
    else:
        score -= 20
        red_flags.append(f"Sharpe Ratio Rendah ({sharpe} < 1.2) — Keuntungan diperoleh dari spekulasi berisiko tinggi.")

    # Win Rate Sanity Check
    if 60.0 <= win_rate <= 80.0:
        strengths.append(f"Win Rate Proporsional ({win_rate}%) — Tanda trader disiplin melakukan Cut Loss.")
    elif win_rate > 95.0:
        score -= 30
        red_flags.append(f"Win Rate Terlalu Tinggi ({win_rate}%) — AWAS! Trader hampir pasti tidak pernah cut loss.")
    elif win_rate < 50.0:
        score -= 20
        red_flags.append(f"Win Rate Rendah ({win_rate}%).")

    # Trading Days
    if trading_days >= 90:
        strengths.append(f"Rekam Jejak Matang ({trading_days} Hari) — Sudah teruji melintasi berbagai siklus.")
    else:
        score -= 25
        red_flags.append(f"Rekam Jejak Singkat ({trading_days} Hari < 90 Hari) — Risiko 'hoki pemula'.")

    # Leverage
    if leverage <= 5:
        strengths.append(f"Leverage Konservatif ({leverage}x).")
    elif leverage > 20:
        score -= 30
        red_flags.append(f"Leverage Terlalu Tinggi ({leverage}x) — Rawan likuidasi.")

    score = max(0, min(100, score))
    if score >= 80:
        grade = "🌟 GRADE A+ (SANGAT DIREKOMENDASIKAN UNTUK DI-COPY)"
    elif score >= 65:
        grade = "🟢 GRADE B (LAYAK DIIKUTI DENGAN ALOKASI KECIL)"
    elif score >= 50:
        grade = "🟡 GRADE C (HIGH RISK - HANYA UNTUK DANA DINGIN)"
    else:
        grade = "🔴 GRADE D (REJECT / JANGAN PERNAH DI-COPY!)"

    print(f"Skor Audit Risiko     : {score} / 100")
    print(f"Kualifikasi Akhir     : {grade}")
    print("-" * 68)
    print("📊 Parameter Statistik 90 Hari:")
    print(f" * 90D ROI            : {roi_90d}%")
    print(f" * Max Drawdown (MDD) : {mdd}%")
    print(f" * Sharpe Ratio       : {sharpe}")
    print(f" * Win Rate           : {win_rate}%")
    print(f" * Masa Aktif         : {trading_days} Hari")
    print(f" * Estimasi Leverage  : {leverage}x")
    print("-" * 68)

    print("✅ Keunggulan Terverifikasi:")
    for s in strengths:
        print(f"  [+] {s}")

    if red_flags:
        print("\n⚠️ Peringatan Risiko:")
        for r in red_flags:
            print(f"  [-] {r}")
    print("=" * 68 + "\n")

def audit_dex_token(token_address):
    clean_addr = token_address.strip()
    url = f"https://api.dexscreener.com/latest/dex/tokens/{clean_addr}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pairs = data.get("pairs", [])
            if not pairs:
                print(f"Error: Token {clean_addr} tidak ditemukan di DexScreener.")
                return None

            best_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
            name = best_pair.get("baseToken", {}).get("name", "Unknown")
            symbol = best_pair.get("baseToken", {}).get("symbol", "UNKNOWN")
            chain = best_pair.get("chainId", "unknown")
            price_usd = float(best_pair.get("priceUsd", 0) or 0)
            liq_usd = float(best_pair.get("liquidity", {}).get("usd", 0) or 0)
            fdv = float(best_pair.get("fdv", 0) or 0)
            vol24h = float(best_pair.get("volume", {}).get("h24", 0) or 0)
            tx24h = best_pair.get("txns", {}).get("h24", {})
            buys = int(tx24h.get("buys", 0))
            sells = int(tx24h.get("sells", 0))

            print("\n" + "=" * 68)
            print(f"       🪙 ON-CHAIN TOKEN SECURITY AUDIT: {symbol} ({chain.upper()})")
            print(f"       Nama Token : {name} | Kontrak: {clean_addr[:8]}...{clean_addr[-6:]}")
            print("=" * 68)
            print(f"Harga Terkini         : ${price_usd:,.8f}")
            print(f"Likuiditas Pool (USD) : ${liq_usd:,.2f}")
            print(f"Market Cap / FDV      : ${fdv:,.2f}")
            print(f"Volume 24 Jam         : ${vol24h:,.2f}")
            print(f"Aktivitas Txns (24h)  : {buys:,} Buys | {sells:,} Sells")
            print("-" * 68)

            # Honeypot Check
            is_honeypot = False
            if buys > 20 and sells == 0:
                is_honeypot = True
                print("🚨 BAHAYA UTAMA: 100% HONEYPOT DETECTED! (Tidak ada yang bisa menjual / Sell = 0) ❌")

            # FDV to Liquidity Ratio
            fdv_liq_ratio = (fdv / liq_usd) if liq_usd > 0 else 999.0
            print(f"Rasio FDV / Likuiditas: {fdv_liq_ratio:.1f}x")

            if liq_usd < 25000:
                print("⚠️ Peringatan: Likuiditas sangat tipis (< $25,000). Rawan slippage parah atau rugpull.")
            elif fdv_liq_ratio > 30.0:
                print("⚠️ Peringatan: Rasio FDV terlalu tinggi dibanding pool likuiditas. Rawan dump oleh dev/whale.")
            else:
                print("✅ Likuiditas & Rasio FDV dalam batas wajar institusional.")

            print("=" * 68 + "\n")
            return {
                "symbol": symbol,
                "chain": chain,
                "liq_usd": liq_usd,
                "fdv": fdv,
                "is_honeypot": is_honeypot
            }
    except Exception as e:
        print(f"Gagal mengaudit token {clean_addr}: {e}")
        return None

def calculate_copy_sizing(whale_size_usd, user_balance_usd=1000.0, risk_pct=1.5, max_collateral_usd=100.0):
    print("\n" + "=" * 68)
    print("       ⚖️ COPY-TRADE PROPORTIONAL RISK SIZING CALCULATOR")
    print("=======================================================")
    print(f"Modal Akun Anda       : ${user_balance_usd:,.2f} USDT")
    print(f"Ukuran Order Whale    : ${whale_size_usd:,.2f} USD")
    print(f"Batas Resiko Akun     : {risk_pct}% per transaksi")
    print("-" * 68)

    # Calculate Max Dollar Risk
    max_risk_usd = user_balance_usd * (risk_pct / 100.0)

    # Sizing: Assume max tolerable loss is 20% on meme coin or SL 20%
    target_position_usd = min(max_risk_usd / 0.20, max_collateral_usd)
    copy_percentage = (target_position_usd / whale_size_usd) * 100.0

    print(f"Ukuran Posisi Anda    : ${target_position_usd:,.2f} USDT")
    print(f"Copy Percentage       : {copy_percentage:.3f}% dari order whale")
    print(f"Maksimal Resiko (SL)  : ${max_risk_usd:,.2f} (Hanya 1.5% modal)")
    print("-" * 68)
    print("💡 Rekomendasi Pengaturan di Bot Copy-Trade:")
    print(f" * Buy Mode           : Fixed Amount (${target_position_usd:,.2f}) ATAU {copy_percentage:.2f}%")
    print(f" * Max Buy Cap        : ${target_position_usd:,.2f}")
    print(f" * Max Slippage       : 2.0% (Mencegah beli di pucuk)")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Smart Money & Copy-Trade Auditor")
    sub = parser.add_subparsers(dest="command")

    # Audit wallet
    w_p = sub.add_parser("audit", help="Audit kelayakan dompet whale untuk copy-trade")
    w_p.add_argument("--wallet", type=str, required=True, help="Alamat dompet atau nama trader")
    w_p.add_argument("--wr", type=float, required=True, help="Win rate persen (misal: 68.5)")
    w_p.add_argument("--trades", type=int, required=True, help="Total trade historis (misal: 45)")
    w_p.add_argument("--pnl", type=float, default=50000.0, help="Total realized profit USD")
    w_p.add_argument("--followers", type=int, default=300, help="Jumlah copy-traders pengikut")
    w_p.add_argument("--hold-mins", type=int, default=120, help="Rata-rata durasi hold menit")

    # Audit token
    t_p = sub.add_parser("token", help="Audit keamanan kontrak token DEX via DexScreener")
    t_p.add_argument("--address", type=str, required=True, help="Alamat smart contract token")

    # Size calculator
    s_p = sub.add_parser("size", help="Hitung ukuran porsi aman copy-trade")
    s_p.add_argument("--whale-size", type=float, required=True, help="Nominal order whale dalam USD")
    s_p.add_argument("--balance", type=float, default=1000.0, help="Modal akun Anda USD (default: 1000)")
    s_p.add_argument("--risk", type=float, default=1.5, help="Resiko maksimal persen (default: 1.5)")
    s_p.add_argument("--max-collateral", type=float, default=100.0, help="Batas maksimal posisi USD (default: 100)")

    # Audit Binance Lead Trader
    b_p = sub.add_parser("binance", help="Audit kelayakan Lead Trader Binance Copy Trading")
    b_p.add_argument("--name", type=str, required=True, help="Nickname trader Binance")
    b_p.add_argument("--roi", type=float, required=True, help="90D ROI persen (misal: 85.0)")
    b_p.add_argument("--mdd", type=float, required=True, help="Max Drawdown persen (misal: 12.5)")
    b_p.add_argument("--sharpe", type=float, required=True, help="Sharpe Ratio (misal: 2.1)")
    b_p.add_argument("--wr", type=float, required=True, help="Win Rate persen (misal: 70.0)")
    b_p.add_argument("--leverage", type=int, default=5, help="Rata-rata leverage (default: 5)")
    b_p.add_argument("--days", type=int, default=90, help="Masa trading hari (default: 90)")

    args = parser.parse_args()
    if args.command == "audit":
        audit_whale_metrics(args.wallet, args.wr, args.trades, args.pnl, args.followers, args.hold_mins)
    elif args.command == "binance":
        audit_binance_lead_trader(args.name, args.roi, args.mdd, args.sharpe, args.wr, args.leverage, args.days)
    elif args.command == "token":
        audit_dex_token(args.address)
    elif args.command == "size":
        calculate_copy_sizing(args.whale_size, args.balance, args.risk, args.max_collateral)
    else:
        print("Gunakan perintah: binance, audit, token, atau size. Ketik --help untuk bantuan.")

if __name__ == "__main__":
    main()
