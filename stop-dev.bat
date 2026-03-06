@echo off
setlocal

echo Stopping app-L5x dev servers...

taskkill /FI "WINDOWTITLE eq app-L5x Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq app-L5x Frontend" /T /F >nul 2>&1

echo Done. If any server is still running, close its terminal window manually.
