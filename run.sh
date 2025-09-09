#!/bin/bash

# Check if year and month parameters are provided
if [ $# -eq 2 ]; then
    YEAR=$1
    MONTH=$2
    echo "Generating schedule for $YEAR-$MONTH"
    
    # Format month with leading zero if needed
    MONTH_FORMATTED=$(printf "%02d" $MONTH)
    
    # Remove only files matching the specific year-month pattern
    rm ./schedule-$YEAR-$MONTH_FORMATTED.xlsx 2>/dev/null || true
    
    uv run python -c "from src.sevens_rain.main import generate_excel; generate_excel($YEAR, $MONTH)"
elif [ $# -eq 0 ]; then
    echo "Using current month"
    
    # Get current year and month
    CURRENT_YEAR=$(date +%Y)
    CURRENT_MONTH=$(date +%m)
    
    # Remove only the current month's file
    rm ./schedule-$CURRENT_YEAR-$CURRENT_MONTH.xlsx 2>/dev/null || true
    
    uv run -m sevens_rain.main
else
    echo "Usage: $0 [YYYY MM]"
    echo "Example: $0 2025 10"
    echo "Or run without parameters for current month"
    exit 1
fi
