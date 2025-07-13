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
import subprocess
import sys
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

def execute_git_setup(base_path):
    """Actually execute the Git setup commands."""
    
    print("\n🚀 EXECUTING GIT SETUP...")
    print("=" * 40)
    
    commands = [
        ("git init", "Initialize Git repository"),
        ("git add *.py README.md requirements.txt .gitignore", "Stage essential files"),
        ('git commit -m "Initial commit: SD ComfyUI unified sorter"', "Create initial commit"),
        ("git branch -M main", "Set main branch")
    ]
    
    # Change to project directory
    original_dir = os.getcwd()
    os.chdir(base_path)
    
    try:
        for command, description in commands:
            print(f"\n📋 {description}...")
            print(f"   Running: {command}")
            
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"   ✅ Success!")
                    if result.stdout.strip():
                        print(f"   Output: {result.stdout.strip()}")
                else:
                    print(f"   ⚠️  Warning: {result.stderr.strip()}")
                    if "already exists" in result.stderr.lower():
                        print(f"   (This is normal if Git was already initialized)")
                    
            except subprocess.TimeoutExpired:
                print(f"   ❌ Command timed out")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Create a new repository on GitHub named 'SD-ComfyUI-Sorter'")
        print(f"2. Run these commands to push:")
        print(f"   git remote add origin https://github.com/yourusername/SD-ComfyUI-Sorter.git")
        print(f"   git push -u origin main")
        
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    print("🚀 SD_COMFYUI_HACKS Git Migration Helper")
    print("=" * 60)
    
    # Check project structure
    is_ready = check_project_structure()
    
    # Show project summary
    create_project_summary()
    
    if is_ready:
        print("🎉 Project is ready for Git migration!")
        
        # Ask user if they want to execute Git setup
        response = input("\n🤔 Would you like me to execute the Git setup commands now? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            base_path = Path(__file__).parent
            execute_git_setup(base_path)
        else:
            print("\n📋 Manual Git setup commands:")
            base_path = Path(__file__).parent
            print("cd", f'"{base_path}"')
            print("git init")
            print("git add *.py README.md requirements.txt .gitignore")
            print('git commit -m "Initial commit: SD ComfyUI unified sorter"')
            print("git branch -M main")
            print("git remote add origin <your-repo-url>")
            print("git push -u origin main")
    else:
        print("⚠️  Please address missing files before Git migration.")
