@echo off
title Seven Rain Scheduler - 七里河北控水务排班工具
color 0A

echo =====================================================
echo           Seven Rain Scheduler
echo        七里河北控水务排班工具 v1.0.0
echo =====================================================
echo.

REM Check if executable exists
if not exist "SevenRainScheduler.exe" (
    echo 错误: 找不到 SevenRainScheduler.exe 文件
    echo Error: SevenRainScheduler.exe not found
    echo.
    echo 请确保此批处理文件与 SevenRainScheduler.exe 在同一目录中
    echo Please ensure this batch file is in the same directory as SevenRainScheduler.exe
    echo.
    pause
    exit /b 1
)

echo 使用方法 / Usage:
echo   run_scheduler.bat                  # 生成当前月份 / Generate current month
echo   run_scheduler.bat 2025-09          # 生成2025年9月 / Generate September 2025
echo   run_scheduler.bat 2024-12          # 生成2024年12月 / Generate December 2024
echo.

REM Get command line arguments
set TARGET_DATE=%1

if "%TARGET_DATE%"=="" (
    echo 正在启动排班程序（当前月份）...
    echo Starting scheduler program (current month)...
    echo.
    SevenRainScheduler.exe
) else (
    echo 正在启动排班程序（目标月份: %TARGET_DATE%）...
    echo Starting scheduler program (target month: %TARGET_DATE%)...
    echo.
    SevenRainScheduler.exe %TARGET_DATE%
)

REM Check if the program completed successfully
if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================================
    echo 排班完成! 请查看生成的Excel文件
    echo Schedule completed! Please check the generated Excel file
    echo =====================================================
) else (
    echo.
    echo =====================================================
    echo 程序执行出现错误，错误代码: %ERRORLEVEL%
    echo Program execution error, error code: %ERRORLEVEL%
    echo =====================================================
)

echo.
echo 按任意键退出...
echo Press any key to exit...
pause > nul