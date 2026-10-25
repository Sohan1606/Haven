@echo off
cd /d "%~dp0"
echo Open http://127.0.0.1:8765 in Chrome or Edge after the server starts.
where py >nul 2>nul
if %errorlevel% equ 0 (
 py -3 local_server.py
) else (
 python local_server.py
)
pause
