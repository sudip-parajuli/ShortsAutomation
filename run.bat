@echo off
REM YouTube Shorts Automation Runner
REM This script is designed to run via Windows Task Scheduler

cd /d "c:\Users\Acer\Desktop\quotes-shorts-automation"

:: Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! >> automation.log
    exit /b 1
)

:: Log start time
echo ============================================ >> automation.log
echo [%date% %time%] Starting automation... >> automation.log

:: Run the main script
python src/main.py >> automation.log 2>&1

:: Log completion
if %errorlevel% neq 0 (
    echo [%date% %time%] Job FAILED with error code %errorlevel% >> automation.log
    exit /b %errorlevel%
) else (
    echo [%date% %time%] Job completed successfully. >> automation.log
)

exit /b 0
