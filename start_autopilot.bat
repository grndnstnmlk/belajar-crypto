@echo off
title AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK
color 0A

echo ====================================================================
echo        [ROBOT] AKADEMI CRYPTO - AUTONOMOUS AI TRADING DESK (24/7)
echo        Akun    : dxmade@gmail.com
echo        Mode    : Binance Futures Demo (USD-M Testnet)
echo        Desk    : 🎯 BIG-PROFIT SWING DESK (1H/4H Macro Confluence)
echo        Genome  : Generation 5 (Min R:R 1:3.00 - 1:5.00+, Max Risk 1.5%%)
echo        Watchlist: 10 Aset (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, SUI)
echo ====================================================================
echo.
echo Memulai pemindaian otomatis setiap 15 menit...
echo Tekan Ctrl+C untuk menghentikan bot.
echo.

python -u .agents\tools\trading_desk.py run --mode SWING --interval 15 --user dxmade@gmail.com

pause
