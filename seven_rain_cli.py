#!/usr/bin/env python3
"""
Seven Rain Scheduling Tool - Windows Executable Entry Point
A tool for generating employee scheduling Excel files with advanced rules.
"""

import sys
import os
import argparse
import re
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sevens_rain.main import main as seven_rain_main

def parse_year_month(date_str):
    """Parse yyyy-mm format and validate the date."""
    if not date_str:
        return None, None
        
    # Check format
    if not re.match(r'^\d{4}-\d{1,2}$', date_str):
        raise ValueError(f"Invalid format '{date_str}'. Please use YYYY-MM format (e.g., 2025-09)")
    
    try:
        year, month = map(int, date_str.split('-'))
    except ValueError:
        raise ValueError(f"Invalid date format '{date_str}'. Please use YYYY-MM format")
    
    # Validate year
    current_year = datetime.now().year
    if year < 2020 or year > current_year + 10:
        raise ValueError(f"Year {year} is out of reasonable range (2020-{current_year + 10})")
    
    # Validate month
    if month < 1 or month > 12:
        raise ValueError(f"Month {month} is invalid. Please use 1-12")
    
    return year, month


def main():
    """Entry point for the Seven Rain executable."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="七里河北控水务排班工具 / Seven Rain Scheduling Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  SevenRainScheduler.exe                 # Generate current month
  SevenRainScheduler.exe 2025-09         # Generate September 2025
  SevenRainScheduler.exe 2024-12         # Generate December 2024
  
Date format: YYYY-MM (e.g., 2025-09 for September 2025)
        """
    )
    parser.add_argument(
        'date', 
        nargs='?', 
        help='Target month in YYYY-MM format (default: current month)'
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version='Seven Rain Scheduler v1.0.0'
    )
    
    try:
        args = parser.parse_args()
        target_year, target_month = parse_year_month(args.date)
    except ValueError as e:
        print(f"❌ 参数错误 / Parameter Error: {e}")
        print("\n使用方法 / Usage:")
        print("  SevenRainScheduler.exe [YYYY-MM]")
        print("  例如 / Example: SevenRainScheduler.exe 2025-09")
        if os.name == 'nt':
            input("\n按任意键退出... / Press any key to exit...")
        sys.exit(1)
    except SystemExit:
        # argparse calls sys.exit for --help or --version
        if os.name == 'nt':
            input("\n按任意键退出... / Press any key to exit...")
        raise
    
    print("="*60)
    print("             七里河北控水务排班工具")  
    print("           Seven Rain Scheduling Tool")
    print("="*60)
    print("Version: 1.0.0")
    
    if target_year and target_month:
        month_names_cn = ["", "一月", "二月", "三月", "四月", "五月", "六月",
                          "七月", "八月", "九月", "十月", "十一月", "十二月"]
        print(f"生成目标月份 / Target month: {target_year}年{month_names_cn[target_month]} / {target_year}-{target_month:02d}")
    else:
        print("生成当前月份 / Generating current month")
    
    print("Generating employee schedules with advanced rules...")
    print()
    
    try:
        # Change to the script directory to ensure relative paths work
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Run the main application with target date
        seven_rain_main(target_year, target_month)
        
        print("\n" + "="*60)
        print("✅ 排班完成! Schedule generation completed!")
        print("请检查生成的Excel文件 / Please check the generated Excel file")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户取消操作 / Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误 / Error: {e}")
        print("\n请联系技术支持 / Please contact technical support")
        print("如果问题持续，请提供错误信息截图")
        print("If the problem persists, please provide error message screenshots")
        sys.exit(1)
    
    # Keep window open on Windows
    if os.name == 'nt':  # Windows
        input("\n按任意键退出... / Press any key to exit...")

if __name__ == "__main__":
    main()