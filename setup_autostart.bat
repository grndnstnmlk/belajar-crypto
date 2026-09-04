@echo off
title AKADEMI CRYPTO - PASANG AUTOSTART WINDOWS
color 0B

echo ====================================================================
echo   🚀 PASANG AUTO-START TRADING DESK DI WINDOWS STARTUP
echo ====================================================================
echo.
echo Skrip ini akan mendaftarkan bot agar otomatis berjalan sendiri
echo setiap kali komputer Anda dinyalakan atau direstart!
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set TARGET_BAT=%~dp0start_autopilot.bat
set RUNNER_BAT=%STARTUP_DIR%\AkademiCryptoAutopilot.bat

echo Menulis peluncur otomatis ke Startup Windows:
echo %RUNNER_BAT%
echo.

(
  echo @echo off
  echo cd /d "%~dp0"
  echo start "AKADEMI CRYPTO - 24/7 AUTONOMOUS AI TRADING DESK" cmd /c "start_autopilot.bat"
) > "%RUNNER_BAT%"

echo ====================================================================
echo  ✅ BERHASIL! Bot telah didaftarkan di Windows Startup.
echo  Mulai sekarang, setiap kali komputer menyala, bot otomatis aktif!
echo ====================================================================
echo.
echo Jika suatu saat ingin menonaktifkannya, cukup hapus file:
echo "%RUNNER_BAT%"
echo.
pause
