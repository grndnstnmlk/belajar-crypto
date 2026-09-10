@echo off
title AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK (METATRADER 5 DUAL-ENGINE)
color 0A
chcp 65001 >nul

set EXECUTION_BACKEND=BOTH

echo ====================================================================
echo   🤖 AKADEMI CRYPTO - AUTONOMOUS AI TRADING DESK (DUAL-BACKEND)
echo   Backend   : ⚡ DUAL SIMULTANEOUS (Binance Futures + MetaTrader 5)
echo   Saldo     : $100k MT5 Virtual + ~$4.6k Binance USDT Demo
echo   Desk      : ⚡ FAST SCALPER 5M (High-Frequency Micro-Structure)
echo   Timeframe : 5m Micro-Structure (Order Block, Sweeps, FVG, Rejections)
echo   Interval  : Pemindaian Cepat Real-Time Setiap 15 Detik
echo   Watchlist : Multi-Asset (BTC, ETH, SOL, XRP, DOGE, NEAR, SUI, LINK)
echo   Proteksi  : SMC Trailing Stop, Auto Breakeven (+0.6R), Dynamic Kelly
echo   Dashboard : http://localhost:5000
echo ====================================================================
echo.
echo Memeriksa dan menyalakan Web Dashboard di latar belakang (Port 5000)...
start "" /B python -u .agents\tools\dashboard_server.py
echo.
echo Pastikan tombol [Algo Trading] di aplikasi MetaTrader 5 berwarna HIJAU!
echo Memulai pemindaian otomatis Fast Scalper setiap 15 detik ke akun Binance & MT5...
echo Tekan Ctrl+C untuk menghentikan bot.
echo.

python -u .agents\tools\trading_desk.py run --mode SCALP

pause
