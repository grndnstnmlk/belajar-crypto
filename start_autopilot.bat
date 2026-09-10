@echo off
title AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK (METATRADER 5 DUAL-ENGINE)
color 0A
chcp 65001 >nul

set EXECUTION_BACKEND=MT5

echo ====================================================================
echo   🤖 AKADEMI CRYPTO - AUTONOMOUS AI TRADING DESK (MT5 HYBRID)
echo   Backend   : MetaTrader 5 (MT5 Demo Execution)
echo   Saldo     : $100,000.00 USD Virtual Margin
echo   Desk      : 🤖 HYBRID DUAL-ENGINE (5m Fast Scalp + 1H Swing)
echo   Timeframe : 5m Micro-Structure + 1H/4H Macro Confluence
echo   Interval  : Pemindaian Cepat Real-Time Setiap 1 Menit (60 Detik)
echo   Watchlist : Multi-Asset (Crypto, Forex, Metals & Indices)
echo   Proteksi  : SMC Trailing Stop, Auto Breakeven (+1.0R), Macro News Shield
echo   Dashboard : http://localhost:5000
echo ====================================================================
echo.
echo Memeriksa dan menyalakan Web Dashboard di latar belakang (Port 5000)...
start "" /B python -u .agents\tools\dashboard_server.py
echo.
echo Pastikan tombol [Algo Trading] di aplikasi MetaTrader 5 berwarna HIJAU!
echo Memulai pemindaian otomatis Dual-Engine setiap 1 menit ke akun MT5...
echo Tekan Ctrl+C untuk menghentikan bot.
echo.

python -u .agents\tools\trading_desk.py run --mode HYBRID --interval 1

pause
