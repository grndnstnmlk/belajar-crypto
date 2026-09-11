@echo off
title AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK (BINANCE FUTURES AUTONOMOUS)
color 0A
chcp 65001 >nul

set EXECUTION_BACKEND=BINANCE

echo ====================================================================
echo   🤖 AKADEMI CRYPTO - AUTONOMOUS AI TRADING DESK (DUAL-BACKEND)
echo   Backend   : ⚡ BINANCE FUTURES TESTNET/LIVE
echo   Desk      : 🎯 SWING INTRADAY DESK (1H / 4H Macro Confluence - Profit Maksimal)
echo   Setup     : SMC Liquidity Sweeps, 3R-5R Asymmetric Targets, Order Blocks, FVG
echo   Interval  : Pemindaian Siklus Makro Berkala
echo   Watchlist : Multi-Asset (BTC, ETH, SOL, XRP, DOGE, NEAR, SUI, LINK)
echo   Proteksi  : SMC Trailing Stop (+2R/+3R), Auto Breakeven (+1.0R), Dynamic Kelly
echo   Dashboard : http://localhost:5000
echo ====================================================================
echo.
echo Memeriksa dan menyalakan Web Dashboard di latar belakang (Port 5000)...
start "" /B python -u .agents\tools\dashboard_server.py
echo.
echo Pastikan tombol [Algo Trading] di aplikasi MetaTrader 5 berwarna HIJAU!
echo Memulai pemindaian otomatis Swing Intraday (1H/4H Macro Confluence) ke akun Binance & MT5...
echo Tekan Ctrl+C untuk menghentikan bot.
echo.

python -u .agents\tools\trading_desk.py run --mode SWING

pause
