#!/usr/bin/env python3
"""
Git Migration Setup Script for SD_COMFYUI_HACKS
This script helps prepare your project for Git migration by:
1. Listing all relevant files
2. Checking file integrity
3. Providing migration recommendations
"""

import os
import shutil
from pathlib import Path

def check_project_structure():
    """Check the current project structure and provide migration recommendations."""
    
    base_path = Path(__file__).parent
    print(f"🔍 Analyzing project structure in: {base_path}")
    print("=" * 60)
    
    # Essential files for the sorter system
    essential_files = [
        "unified_sorter.py",
        "color_sorter.py", 
        "text_file_sorter.py",
        "final_batch_rename_sort.py",
        "requirements.txt",
        "README.md"
    ]
    
    # Optional/Demo files
    optional_files = [
        "demo_color_sorter.py",
        "test_color_sorter.py",
        "test_methods.py",
        "ui_text_file_sorter.py"
    ]
    
    # Files/folders to exclude from Git
    exclude_items = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".vscode",
        "Thumbs.db"
    ]
    
    print("✅ ESSENTIAL FILES (required for Git):")
    missing_essential = []
    for file in essential_files:
        file_path = base_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✓ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file} (MISSING)")
            missing_essential.append(file)
    
    print("\n📦 OPTIONAL FILES (demo/testing):")
    for file in optional_files:
        file_path = base_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ○ {file} ({size} bytes)")
        else:
            print(f"   - {file} (not found)")
    
    print("\n🗂️ DIRECTORIES:")
    for item in base_path.iterdir():
        if item.is_dir() and item.name not in ["__pycache__", ".git"]:
            file_count = len(list(item.glob("*")))
            print(f"   📁 {item.name}/ ({file_count} items)")
    
    print("\n🚨 EXCLUSIONS (will be ignored by Git):")
    for item in exclude_items:
        print(f"   🚫 {item}")
    
    # Check if .gitignore exists
    gitignore_path = base_path / ".gitignore"
    if gitignore_path.exists():
        print(f"\n✅ .gitignore file exists ({gitignore_path.stat().st_size} bytes)")
    else:
        print(f"\n❌ .gitignore file missing - create one!")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("🎯 MIGRATION RECOMMENDATIONS:")
    
    if missing_essential:
        print(f"❗ Missing essential files: {', '.join(missing_essential)}")
    else:
        print("✅ All essential files present!")
    
    print("\n📋 GIT SETUP COMMANDS:")
    print("cd", f'"{base_path}"')
    print("git init")
    print("git add *.py README.md requirements.txt .gitignore")
    print('git commit -m "Initial commit: SD ComfyUI Hacks unified sorter"')
    print("git branch -M main")
    print("git remote add origin <your-repo-url>")
    print("git push -u origin main")
    
    return len(missing_essential) == 0

def create_project_summary():
    """Create a summary of what this project does."""
    
    summary = """
🎨 SD_COMFYUI_HACKS Project Summary
==================================

This is a unified sorting tool for AI image generation workflows with three main modes:

1. **Text File Sorter** 📝
   - Organizes text files with customizable placeholders
   - Move or copy operations
   - Perfect for prompts and documentation

2. **ComfyUI Batch Sorter** 🖼️  
   - Renames images by Base+LoRA format
   - Generates metadata files
   - Sorts by checkpoint filenames

3. **Color Sorter** 🌈
   - Analyzes dominant colors using HSV
   - Sorts into 11 color categories
   - Creates visual distribution charts
   - Perfect for final organization

USAGE:
   python unified_sorter.py    # Main application
   python demo_color_sorter.py # Color sorting demo

REQUIREMENTS:
   pip install -r requirements.txt
"""
    
    print(summary)

if __name__ == "__main__":
    print("🚀 SD_COMFYUI_HACKS Git Migration Helper")
    print("=" * 60)
    
    # Check project structure
    is_ready = check_project_structure()
    
    # Show project summary
    create_project_summary()
    
    if is_ready:
        print("🎉 Project is ready for Git migration!")
    else:
        print("⚠️  Please address missing files before Git migration.")
