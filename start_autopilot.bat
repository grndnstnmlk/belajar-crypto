@echo off
title AKADEMI CRYPTO - AUTONOMOUS TRADING DESK MISSION CONTROL
chcp 65001 >nul
cd /d "%~dp0"

:: Activate Windows ANSI Escape processing
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

:: Seamless Cloud Sync (Pull latest trades & settings from GitHub)
echo [CLOUD SYNC] Pulling latest data from GitHub...
git pull --rebase --autostash origin main >nul 2>&1

:: Launch interactive Python launcher
python -u .agents\tools\launcher.py
if errorlevel 1 pause
