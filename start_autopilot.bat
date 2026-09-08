@echo off
title AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK (HYBRID DUAL-ENGINE)
color 0A
chcp 65001 >nul

echo ====================================================================
echo   🤖 AKADEMI CRYPTO - AUTONOMOUS AI TRADING DESK (HYBRID AUTO)
echo   Akun      : dxmade@gmail.com
echo   Mode      : Binance Futures Demo (USD-M Testnet)
echo   Desk      : 🤖 HYBRID DUAL-ENGINE (5m Fast Scalp + 1H Swing)
echo   Timeframe : 5m Micro-Structure + 1H/4H Macro Confluence
echo   Interval  : Pemindaian Cepat Real-Time Setiap 1 Menit (60 Detik)
echo   Watchlist : 10 Aset (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, SUI)
echo   Proteksi  : Fast BE (+0.7R), 45-Min Time-Stop, Macro News Shield
echo   Dashboard : http://localhost:5000
echo ====================================================================
echo.
echo Memeriksa dan menyalakan Web Dashboard di latar belakang (Port 5000)...
start "" /B python -u .agents\tools\dashboard_server.py
echo.
echo Memulai pemindaian otomatis Dual-Engine setiap 1 menit...
echo Tekan Ctrl+C untuk menghentikan bot.
echo.

python -u .agents\tools\trading_desk.py run --mode HYBRID --interval 1 --user dxmade@gmail.com

pause
