:: This file is a part of Open H3C System Control.
:: by Remik1r3n 2026.

@echo off
cd /d %~dp0
cls

set "ScriptPath=%~f0"
set "H3CSCPath=C:\Program Files\Megabook\SystemControl\Service"
echo Checking for admin..
NET SESSION >nul 2>&1
if %errorLevel% neq 0 (
    echo Need admin permission. Please allow.
    powershell -Command "Start-Process -Verb RunAs -FilePath \"!ScriptPath!\""
    exit /b
) else (
    echo Admin OK. Continue.
)
echo Killing task..
taskkill /f /im SystemControl.exe
echo Stopping service..
start /min /wait "STOP" "%H3CSCPath%\serviceStop.bat"
echo Uninstalling service..
start /min /wait "UNINST" "%H3CSCPath%\serviceUninstall.bat"
echo Killing task again..
taskkill /f /im SystemControl.exe

echo.
echo Done! if you need H3C Control Center again, 
echo Please use %H3CSCPath%\serviceInstall.bat.
echo.
pause
