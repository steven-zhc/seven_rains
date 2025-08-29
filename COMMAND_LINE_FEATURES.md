# Seven Rain Scheduler - Command Line Features

## ✅ New Command-Line Functionality Added!

The Seven Rain Scheduling Tool now supports flexible command-line arguments for specifying target year and month.

### 🎯 **Key Features**

1. **✅ Flexible Date Input**: Specify any month/year in YYYY-MM format
2. **✅ Input Validation**: Comprehensive error checking and user-friendly messages
3. **✅ Bilingual Interface**: Chinese/English error messages and help text
4. **✅ Backward Compatibility**: Defaults to current month if no parameters provided
5. **✅ Help System**: Built-in help and version information

### 📋 **Usage Examples**

#### Direct Executable Usage
```bash
# Generate current month schedule
SevenRainScheduler.exe

# Generate specific month schedules
SevenRainScheduler.exe 2025-09    # September 2025
SevenRainScheduler.exe 2024-12    # December 2024
SevenRainScheduler.exe 2025-03    # March 2025

# Show help information
SevenRainScheduler.exe --help

# Show version
SevenRainScheduler.exe --version
```

#### Batch File Usage
```bash
# Generate current month
run_scheduler.bat

# Generate specific months
run_scheduler.bat 2025-09
run_scheduler.bat 2024-12
run_scheduler.bat 2025-03
```

### 🔍 **Input Validation**

The program validates all input parameters:

#### **Date Format Validation**
- ✅ Accepts: `2025-09`, `2024-12`, `2025-3` 
- ❌ Rejects: `25-09`, `2025/09`, `2025-9-1`, `202509`

#### **Year Range Validation**
- ✅ Accepts: 2020 - (current year + 10)
- ❌ Rejects: Years before 2020 or more than 10 years in the future

#### **Month Range Validation**
- ✅ Accepts: 1-12
- ❌ Rejects: 0, 13, or non-numeric values

### 🚨 **Error Handling Examples**

```bash
# Invalid month
$ SevenRainScheduler.exe 2025-13
❌ 参数错误 / Parameter Error: Month 13 is invalid. Please use 1-12

# Invalid format
$ SevenRainScheduler.exe 25-09
❌ 参数错误 / Parameter Error: Invalid format '25-09'. Please use YYYY-MM format (e.g., 2025-09)

# Invalid year
$ SevenRainScheduler.exe 2019-09
❌ 参数错误 / Parameter Error: Year 2019 is out of reasonable range (2020-2034)
```

### 📱 **User Interface Improvements**

#### **Bilingual Messages**
- All error messages displayed in both Chinese and English
- Help text includes usage examples in both languages
- Target month confirmation shows Chinese month names

#### **Enhanced Feedback**
- Clear indication of target month being generated
- Month names displayed in both English and Chinese
- Improved error messages with specific guidance

### 🔧 **Technical Implementation**

#### **New Functions Added**
1. **`parse_year_month()`**: Validates and parses YYYY-MM format
2. **Enhanced `main()`**: Accepts optional year/month parameters
3. **`argparse` Integration**: Professional command-line argument parsing

#### **Parameter Flow**
```
Command Line → argparse → parse_year_month() → main() → generate_month_schedule_new()
```

#### **Default Behavior**
- If no parameters provided: Uses current month/year
- If invalid parameters: Shows error and usage information
- If valid parameters: Generates schedule for specified month

### 📊 **Output Examples**

#### **Success Output**
```
============================================================
             七里河北控水务排班工具
           Seven Rain Scheduling Tool
============================================================
Version: 1.0.0
生成目标月份 / Target month: 2025年三月 / 2025-03
Generating employee schedules with advanced rules...

🔄 Generating March 2025 schedule...
Excel generated: schedule-2025-03.xlsx

✅ Excel generated: schedule-2025-03.xlsx
```

#### **Help Output**
```
usage: SevenRainScheduler [-h] [--version] [date]

七里河北控水务排班工具 / Seven Rain Scheduling Tool

positional arguments:
  date        Target month in YYYY-MM format (default: current month)

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit

Examples:
  SevenRainScheduler.exe                 # Generate current month
  SevenRainScheduler.exe 2025-09         # Generate September 2025
  SevenRainScheduler.exe 2024-12         # Generate December 2024
  
Date format: YYYY-MM (e.g., 2025-09 for September 2025)
```

### 🎉 **Benefits**

1. **Flexibility**: Generate schedules for any target month
2. **Batch Processing**: Can be easily scripted for multiple months
3. **User-Friendly**: Clear error messages and help system
4. **Professional**: Standard command-line interface conventions
5. **Reliable**: Comprehensive input validation prevents errors

### 🔄 **Backward Compatibility**

- ✅ Existing workflows continue to work unchanged
- ✅ Double-clicking executable still generates current month
- ✅ All existing batch files continue to function
- ✅ No breaking changes to core functionality

The Seven Rain Scheduler now offers enterprise-grade command-line flexibility while maintaining its user-friendly interface! 🚀