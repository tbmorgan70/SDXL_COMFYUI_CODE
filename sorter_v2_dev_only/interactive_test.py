#!/usr/bin/env python3
"""
Interactive test for Sorter 2.0 - simulates user interaction
to identify runtime issues that occur during actual menu usage
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from io import StringIO

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def create_test_images():
    """Create test PNG files with fake metadata"""
    test_dir = tempfile.mkdtemp()
    print(f"Test directory: {test_dir}")
    
    # Create test PNG files (just empty files for testing)
    test_files = ['image1.png', 'image2.png', 'image3.jpg', 'test_metadata.json']
    for filename in test_files:
        file_path = os.path.join(test_dir, filename)
        with open(file_path, 'wb') as f:
            # Write minimal valid PNG header for testing
            if filename.endswith('.png'):
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x18\xddXx\x00\x00\x00\x00IEND\xaeB`\x82')
            else:
                f.write(b'Test content')
    
    return test_dir

def test_option_3_interactive():
    """Test option 3 (color sorting) with simulated user input"""
    print("\n=== TESTING OPTION 3 (COLOR SORTING) - INTERACTIVE ===")
    
    try:
        from main import SorterV2
        
        # Create test environment
        test_dir = create_test_images()
        
        # Simulate user inputs for color sorting
        user_inputs = [
            test_dir,           # source directory
            '',                 # output directory (use default)
            'n',                # don't move files
            'n',                # don't create metadata 
            'n',                # don't rename files
            '0.1',              # dark threshold
            'y',                # proceed
            'n'                 # don't open output folder
        ]
        
        # Mock input function
        input_iterator = iter(user_inputs)
        
        with patch('builtins.input', side_effect=lambda prompt: next(input_iterator)):
            sorter = SorterV2()
            sorter.sort_by_color()
            
        print("✅ Option 3 (Color Sorting) completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Option 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_option_5_interactive():
    """Test option 5 (filename cleanup) with simulated user input"""
    print("\n=== TESTING OPTION 5 (FILENAME CLEANUP) - INTERACTIVE ===")
    
    try:
        from main import SorterV2
        
        # Create test environment
        test_dir = create_test_images()
        
        # Simulate user inputs for filename cleanup
        user_inputs = [
            test_dir,           # source directory
            'y',                # clean up filenames
            'y',                # remove metadata files
            'test',             # filename prefix
            'y',                # apply changes
            'n'                 # don't open folder
        ]
        
        # Mock input function
        input_iterator = iter(user_inputs)
        
        with patch('builtins.input', side_effect=lambda prompt: next(input_iterator)):
            sorter = SorterV2()
            sorter.cleanup_filenames()
            
        print("✅ Option 5 (Filename Cleanup) completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Option 5 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_option_6_interactive():
    """Test option 6 (metadata reports) with simulated user input"""
    print("\n=== TESTING OPTION 6 (METADATA REPORTS) - INTERACTIVE ===")
    
    try:
        from main import SorterV2
        
        # Create test environment
        test_dir = create_test_images()
        
        # Simulate user inputs for metadata reports
        user_inputs = [
            test_dir,           # source directory
            'y',                # create individual reports
            'y',                # create summary report
            '',                 # use default output directory
            'y',                # proceed
            'n'                 # don't open output folder
        ]
        
        # Mock input function
        input_iterator = iter(user_inputs)
        
        with patch('builtins.input', side_effect=lambda prompt: next(input_iterator)):
            sorter = SorterV2()
            sorter.generate_metadata_reports()
            
        print("✅ Option 6 (Metadata Reports) completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Option 6 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run interactive tests"""
    print("🧪 STARTING INTERACTIVE SORTER 2.0 TESTS")
    print("=" * 60)
    
    results = {
        'option_3_color_sorting': test_option_3_interactive(),
        'option_5_filename_cleanup': test_option_5_interactive(),
        'option_6_metadata_reports': test_option_6_interactive()
    }
    
    print("\n" + "=" * 60)
    print("🧪 INTERACTIVE TEST RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        return False
    else:
        print("\n✅ All interactive tests passed!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
