@echo off
echo ===== SO-101 Serial Port Reset Script =====
echo This script will terminate processes that might be using the serial ports.
echo.

REM List processes that might be using serial ports
echo Checking for processes that might be using serial ports...
tasklist /fi "imagename eq python.exe"
echo.

REM Kill any running python processes
echo Attempting to close any Python processes...
taskkill /F /IM python.exe
echo.

REM Try to reset COM ports
echo Attempting to restart serial devices...
echo You may see some errors if the device is not in use - this is normal.
echo.

REM Reset COM3
echo Resetting COM3...
mode COM3:9600,n,8,1
echo.

REM Reset COM4
echo Resetting COM4...
mode COM4:9600,n,8,1
echo.

REM Restart Windows Device Services
echo Restarting Windows Device Services...
net stop "Device Install Service"
net start "Device Install Service"
echo.

echo Serial port reset complete.
echo Please run test_final.py after this script completes.
pause