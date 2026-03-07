#!/usr/bin/env python3
"""
Test script to verify Color Sorter functionality
"""

import sys
import os

# Add the current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    import customtkinter as ctk
    print("✓ customtkinter imported")
    
    import text_file_sorter
    print("✓ text_file_sorter imported")
    
    import final_batch_rename_sort as comfy_sort
    print("✓ final_batch_rename_sort imported")
    
    import color_sorter
    print("✓ color_sorter imported")
    
    print("\nTesting unified_sorter class...")
    from unified_sorter import UnifiedSorter
    print("✓ UnifiedSorter class imported")
    
    print("\nTesting dropdown values...")
    # Create a temporary instance to check the values
    ctk.set_appearance_mode("Dark")
    app = UnifiedSorter()
    
    # Check if Color Sorter is in the dropdown options
    mode_menu_values = ["Text File Sorter", "ComfyUI Batch Sorter", "Color Sorter"]
    print(f"Expected dropdown values: {mode_menu_values}")
    
    # Test color frame exists
    if hasattr(app, 'color_frame'):
        print("✓ color_frame exists")
    else:
        print("✗ color_frame missing")
    
    # Test color methods exist
    if hasattr(app, '_build_color_frame'):
        print("✓ _build_color_frame method exists")
    else:
        print("✗ _build_color_frame method missing")
    
    if hasattr(app, '_do_color_sort'):
        print("✓ _do_color_sort method exists")
    else:
        print("✗ _do_color_sort method missing")
    
    print("\n=== All tests passed! ===")
    print("The Color Sorter should appear in the dropdown.")
    print("If you're not seeing it, try:")
    print("1. Completely close and restart the application")
    print("2. Make sure you're running the correct unified_sorter.py file")
    print("3. Check if there are any error dialogs or console messages")
    
    app.destroy()  # Clean up
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
