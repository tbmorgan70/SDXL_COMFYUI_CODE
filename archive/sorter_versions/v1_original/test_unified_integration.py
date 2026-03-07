#!/usr/bin/env python3
"""
Test script to verify that the unified_sorter can import flatten_images
and has the new flattener functionality integrated.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flatten_images
        print("✓ flatten_images module imported successfully")
        
        # Test that flatten_images has the expected functions
        assert hasattr(flatten_images, 'flatten_images'), "flatten_images function not found"
        assert hasattr(flatten_images, 'remove_empty_dirs'), "remove_empty_dirs function not found"
        print("✓ flatten_images functions are available")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"✗ Function missing: {e}")
        return False

def test_unified_sorter_structure():
    """Test that unified_sorter has the new flattener integration"""
    try:
        # We can't fully import due to customtkinter dependency, but we can check the file content
        with open('unified_sorter.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key integration points
        checks = [
            ('import flatten_images', 'flatten_images import'),
            ('Image Flattener', 'Image Flattener in options'),
            ('_build_flatten_frame', 'flatten frame builder'),
            ('_do_flatten_images', 'flatten execution method'),
            ('flatten_src', 'flatten source variable'),
            ('flatten_out', 'flatten output variable')
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✓ {description} found")
            else:
                print(f"✗ {description} NOT found")
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        print("✗ unified_sorter.py not found")
        return False
    except Exception as e:
        print(f"✗ Error checking unified_sorter.py: {e}")
        return False

def main():
    print("Testing Unified Sorter Integration with Image Flattener")
    print("=" * 60)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    test1_passed = test_imports()
    print()
    test2_passed = test_unified_sorter_structure()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! Image Flattener integration looks good!")
        print("\nTo use the new feature:")
        print("1. Run unified_sorter.py")
        print("2. Select 'Image Flattener' from the mode dropdown")
        print("3. Choose your nested image folder (e.g., a ComfyUI sorted folder)")
        print("4. Optionally choose an output folder")
        print("5. Click Run to flatten all images into a single folder")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
