# Seven Rain Scheduler - Windows Deployment Guide

## 概述 / Overview

七里河北控水务排班工具 (Seven Rain Scheduler) Windows 可执行文件部署指南。

This guide explains how to deploy the Seven Rain Scheduling Tool as a Windows executable.

## 文件说明 / File Description

### 可执行文件 / Executable File
- **`SevenRainScheduler.exe`** - 主程序可执行文件 / Main program executable
  - 大小约 23MB / Size approximately 23MB
  - 包含所有依赖库 / Includes all dependencies
  - 无需安装Python环境 / No Python installation required

### 配置文件 / Configuration Files  
- **`sample.xls`** - 员工名单样本文件 / Employee list sample file (optional)

## 系统要求 / System Requirements

- **操作系统 / OS**: Windows 10/11 (64-bit)
- **内存 / RAM**: 至少 512MB 可用内存 / At least 512MB available RAM
- **磁盘空间 / Disk**: 至少 50MB 可用空间 / At least 50MB free space

## 安装说明 / Installation Instructions

### 1. 下载文件 / Download Files
将以下文件复制到目标Windows电脑的任意文件夹：
Copy the following files to any folder on the target Windows computer:

```
SevenRainScheduler.exe
sample.xls (可选 / optional)
```

### 2. 运行程序 / Run Program
- 双击 `SevenRainScheduler.exe` 运行程序
- Double-click `SevenRainScheduler.exe` to run the program

## 使用说明 / Usage Instructions

### 命令行参数 / Command Line Arguments

程序支持指定目标年月 / Program supports specifying target year-month:

#### 基本用法 / Basic Usage
```bash
# 生成当前月份排班 / Generate current month schedule
SevenRainScheduler.exe

# 生成指定月份排班 / Generate specific month schedule  
SevenRainScheduler.exe 2025-09    # 生成2025年9月 / Generate September 2025
SevenRainScheduler.exe 2024-12    # 生成2024年12月 / Generate December 2024
```

#### 批处理文件使用 / Batch File Usage
```bash
# 生成当前月份 / Generate current month
run_scheduler.bat

# 生成指定月份 / Generate specific month
run_scheduler.bat 2025-09
run_scheduler.bat 2024-12
```

#### 参数格式 / Parameter Format
- 日期格式 / Date format: `YYYY-MM`
- 年份范围 / Year range: 2020 - (当前年+10年) / 2020 - (current year + 10)
- 月份范围 / Month range: 1-12

#### 帮助信息 / Help Information
```bash
# 显示帮助 / Show help
SevenRainScheduler.exe --help

# 显示版本 / Show version
SevenRainScheduler.exe --version
```

### 程序功能 / Program Features
1. **灵活日期选择** / Flexible date selection
2. **自动生成排班表** / Automatic schedule generation
3. **智能规则引擎** / Intelligent rule engine  
4. **Excel输出格式** / Excel output format
5. **员工统计报告** / Employee statistics report

### 输出文件 / Output Files
程序会在运行目录生成以下文件：
The program generates the following files in the running directory:

- **`schedule-YYYY-MM.xlsx`** - 排班表Excel文件 / Schedule Excel file
- **`plan.json`** - 排班数据缓存文件 / Schedule data cache file

### 规则说明 / Scheduling Rules
1. **周末值班后休息** / Rest after weekend on-call
   - 周末值班后，下周一周二必须休息
   - After weekend on-call, Monday and Tuesday of next week must be rest days

2. **周五值班后休息** / Rest after Friday on-call
   - 周五值班后，周六周日加下周一必须休息
   - After Friday on-call, Saturday, Sunday, and next Monday must be rest days

3. **值班轮换** / On-call rotation
   - 每人每周值班一天，避免连续同一天值班
   - Each person has one on-call day per week, avoiding consecutive same-day on-call

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

1. **程序无法启动 / Program won't start**
   - 检查是否有足够磁盘空间 / Check for sufficient disk space
   - 以管理员身份运行 / Run as administrator
   - 检查Windows安全软件是否阻止 / Check if Windows security software is blocking

2. **Excel文件无法打开 / Excel file won't open**
   - 确保安装了Microsoft Excel或兼容软件 / Ensure Microsoft Excel or compatible software is installed
   - 检查文件权限 / Check file permissions

3. **程序运行慢 / Program runs slowly**
   - 首次运行需要初始化，请耐心等待 / First run requires initialization, please wait patiently
   - 关闭不必要的其他程序 / Close unnecessary other programs

### 日志文件 / Log Files
如果遇到问题，查看运行目录中的日志文件：
If you encounter problems, check the log files in the running directory:

- 错误信息会显示在控制台窗口中 / Error messages will be displayed in the console window

## 技术支持 / Technical Support

如需技术支持，请提供以下信息：
For technical support, please provide the following information:

1. Windows版本 / Windows version
2. 错误信息截图 / Error message screenshots  
3. 程序运行日志 / Program run logs
4. 操作步骤描述 / Description of operation steps

## 版本信息 / Version Information

- **版本 / Version**: 1.0.0
- **构建日期 / Build Date**: 2025-08-28
- **Python版本 / Python Version**: 3.13.5
- **支持架构 / Supported Architecture**: x64

## 许可协议 / License

本软件仅供内部使用，禁止未经授权的分发。
This software is for internal use only. Unauthorized distribution is prohibited.