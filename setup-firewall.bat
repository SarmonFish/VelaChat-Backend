@echo off
title WXAuto API WALL

echo.
echo WXAuto API
echo ================================================
echo.

REM CHECK GLY
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo GLY
    pause
    exit /b 1
)

REM IPv4
echo IPv4
netsh advfirewall firewall add rule name="WXAuto API IPv4" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo IPv4 ADDED
) else (
    echo IPv4 CUNZAI
)

REM IPv6
echo IPv6
netsh advfirewall firewall add rule name="WXAuto API IPv6" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo IPv6 ADDED
) else (
    echo ICUNZAI
)

REM SHOW
echo.
echo SHOW:
netsh advfirewall firewall show rule name="WXAuto API IPv4" >nul 2>&1 && echo   - IPv4: 8000
netsh advfirewall firewall show rule name="WXAuto API IPv6" >nul 2>&1 && echo   - IPv6: 8000

echo.
echo OK!
echo.
echo IF DEL:
echo    netsh advfirewall firewall delete rule name="WXAuto API IPv4"
echo    netsh advfirewall firewall delete rule name="WXAuto API IPv6"

echo.
pause