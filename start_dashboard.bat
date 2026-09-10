@echo off
title AKADEMI CRYPTO - VISUAL MISSION CONTROL DASHBOARD
color 0B

echo ====================================================================
echo        🖥️  AKADEMI CRYPTO - VISUAL MISSION CONTROL (PORT 5000)
echo        Backend : MetaTrader 5 (MT5 Demo) / Multi-Asset
echo        URL     : http://localhost:5000
echo ====================================================================
echo.
echo Membuka browser ke http://localhost:5000 ...
start http://localhost:5000

echo Menjalankan Mission Control Web Server...
echo Tekan Ctrl+C untuk menutup server.
echo.

python -u .agents\tools\dashboard_server.py 5000

pause
