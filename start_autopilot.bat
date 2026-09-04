@echo off
title AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK
color 0A

echo ====================================================================
echo        [ROBOT] AKADEMI CRYPTO - AUTONOMOUS AI TRADING DESK (24/7)
echo        Akun    : dxmade@gmail.com
echo        Mode    : Binance Futures Demo (USD-M Testnet)
echo        Genome  : Generation 4 (Min R:R 1:2.50, Max Risk 1.5%%, Multi-Regime Adaptive)
echo        Watchlist: 10 Aset (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, SUI)
echo ====================================================================
echo.
echo Memulai pemindaian otomatis setiap 15 menit...
echo Tekan Ctrl+C untuk menghentikan bot.
echo.

python -u .agents\tools\trading_desk.py run --interval 15 --user dxmade@gmail.com

pause
