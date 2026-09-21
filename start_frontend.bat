@echo off
title AKADEMI CRYPTO - REACT 19 MODERN WORKSTATION
color 0A

echo ====================================================================
echo        ⚛️  AKADEMI CRYPTO - REACT 19 WORKSTATION (PORT 5173)
echo        Stack   : Vite + React 19 + TypeScript + Modern CSS
echo        Backend : http://localhost:5000 (Vite Reverse Proxy)
echo        URL     : http://localhost:5173
echo ====================================================================
echo.
echo Membuka browser ke http://localhost:5173 ...
start http://localhost:5173

cd frontend
npm run dev

pause
