@echo off
setlocal enabledelayedexpansion
REM Windows batch file equivalent of run.sh

REM Check if year and month parameters are provided
if "%~2"=="" (
    if "%~1"=="" (
        echo Using current month
        
        REM Get current year and month using PowerShell
        for /f %%a in ('powershell -Command "Get-Date -Format yyyy"') do set CURRENT_YEAR=%%a
        for /f %%a in ('powershell -Command "Get-Date -Format MM"') do set CURRENT_MONTH=%%a
        
        REM Remove only the current month's file
        del "schedule-!CURRENT_YEAR!-!CURRENT_MONTH!.xlsx" >nul 2>&1
        
        uv run -m sevens_rain.main
    ) else (
        echo Usage: %0 [YYYY MM]
        echo Example: %0 2025 10
        echo Or run without parameters for current month
        exit /b 1
    )
) else (
    set YEAR=%1
    set MONTH=%2
    echo Generating schedule for !YEAR!-!MONTH!
    
    REM Format month with leading zero using PowerShell
    for /f %%a in ('powershell -Command "'{0:00}' -f [int]%MONTH%"') do set MONTH_FORMATTED=%%a
    
    REM Remove only files matching the specific year-month pattern
    del "schedule-!YEAR!-!MONTH_FORMATTED!.xlsx" >nul 2>&1
    
    uv run python -c "from src.sevens_rain.main import generate_excel; generate_excel(!YEAR!, !MONTH!)"
)