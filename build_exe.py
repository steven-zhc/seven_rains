#!/usr/bin/env python3
"""
Build script for Seven Rain Scheduler Windows executable
Usage: python build_exe.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"🔨 {description}")
    print(f"Command: {cmd}")
    print('='*50)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    else:
        print(f"✅ Success: {description} completed")
        if result.stdout:
            print(f"Output: {result.stdout}")


def main():
    """Main build process."""
    print("🚀 Seven Rain Scheduler - Build Process Starting")
    print("="*60)
    
    # Check if we're in the correct directory
    if not Path("seven_rain_cli.py").exists():
        print("❌ Error: seven_rain_cli.py not found. Please run from project root.")
        sys.exit(1)
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")
    
    # Install build dependencies
    run_command("uv sync --extra build", "Installing build dependencies")
    
    # Build the executable
    run_command(
        "uv run pyinstaller SevenRainScheduler.spec --clean --noconfirm",
        "Building Windows executable"
    )
    
    # Check if executable was created
    exe_path = Path("dist/SevenRainScheduler")
    if exe_path.exists():
        # Get file size
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ Executable created successfully!")
        print(f"📍 Location: {exe_path.absolute()}")
        print(f"📊 Size: {size_mb:.1f} MB")
        
        # Copy additional files to dist folder
        print("\n📋 Copying additional files...")
        
        # Copy sample file if exists
        if Path("sample.xls").exists():
            shutil.copy2("sample.xls", "dist/")
            print("✅ Copied sample.xls")
        
        # Copy batch file
        if Path("run_scheduler.bat").exists():
            shutil.copy2("run_scheduler.bat", "dist/")
            print("✅ Copied run_scheduler.bat")
            
        # Copy deployment readme
        if Path("README_DEPLOYMENT.md").exists():
            shutil.copy2("README_DEPLOYMENT.md", "dist/")
            print("✅ Copied README_DEPLOYMENT.md")
        
        print(f"\n🎉 Build completed successfully!")
        print(f"📁 All files are ready in: {Path('dist').absolute()}")
        print(f"\n📦 Deployment files:")
        for file_path in Path("dist").iterdir():
            if file_path.is_file():
                size = file_path.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size / 1024:.1f} KB"
                print(f"   📄 {file_path.name} ({size_str})")
    else:
        print("❌ Error: Executable not found after build")
        sys.exit(1)


if __name__ == "__main__":
    main()