# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Seven Rain is an Excel generation tool that creates Excel files with custom logic. The project analyzes a sample Excel file (`sample.xlsx`) to understand the structure and generates new Excel files based on that template.

## Project Structure

```
src/seven_rain/
├── __init__.py          # Package initialization
└── main.py              # Main Excel generation logic
tests/
├── __init__.py
└── test_main.py         # Tests for main module
sample.xlsx              # Example Excel file for reference
pyproject.toml           # Project configuration
```

## Development Commands

### Setup
```bash
# Install package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Running the Tool
```bash
# Run the main script to analyze sample Excel
python -m sevens_rain.main

# Or use the installed CLI command
seven-rain
```

### Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=sevens_rain
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .
ruff format .

# Type checking
mypy src/
```

## Key Dependencies

- `pandas>=2.0.0` - Data manipulation and Excel reading
- `openpyxl>=3.1.0` - Excel file reading/writing
- `xlsxwriter>=3.1.0` - Excel file creation with formatting

## Architecture

The main module (`src/seven_rain/main.py`) contains:
- `analyze_sample_excel()` - Analyzes the structure of sample.xlsx
- `generate_excel()` - Generates new Excel files based on logic derived from the sample

The tool first analyzes the sample Excel file to understand its structure, then applies custom logic to generate new Excel files.