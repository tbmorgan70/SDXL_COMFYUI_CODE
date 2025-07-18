"""
Sorter 2.0 - Quick Start

Launch script for easy access to Sorter 2.0 functionality.
Just double-click this file or run: python run_sorter_v2.py
"""

import os
import sys

# Add sorter_v2 to Python path
sorter_v2_path = os.path.join(os.path.dirname(__file__), 'sorter_v2')
sys.path.insert(0, sorter_v2_path)

try:
    from main import main
    main()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all Sorter 2.0 files are in the correct location.")
    input("Press Enter to exit...")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    input("Press Enter to exit...")
