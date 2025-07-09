#!/usr/bin/env python3
"""
Setup script for SD_COMFYUI_HACKS
Automatically installs dependencies and verifies the installation.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages from requirements.txt"""
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies!")
        return False

def verify_installation():
    """Verify that all required modules can be imported"""
    
    print("🔍 Verifying installation...")
    
    required_modules = [
        ("customtkinter", "Custom Tkinter UI library"),
        ("PIL", "Pillow image processing library")
    ]
    
    all_good = True
    
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"   ✓ {module} - {description}")
        except ImportError:
            print(f"   ❌ {module} - {description} (MISSING)")
            all_good = False
    
    return all_good

def main():
    """Main setup function"""
    
    print("🎨 SD_COMFYUI_HACKS Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Setup failed during dependency installation.")
        return False
    
    # Verify installation
    if not verify_installation():
        print("\n❌ Setup failed during verification.")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nYou can now run:")
    print("   python unified_sorter.py     # Main application")
    print("   python demo_color_sorter.py  # Color sorting demo")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
