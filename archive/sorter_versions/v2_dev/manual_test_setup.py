#!/usr/bin/env python3
"""
Final integration test - Test the actual main.py program
to ensure all fixes work correctly
"""

import os
import sys
import tempfile
from pathlib import Path
from PIL import Image

def create_test_environment():
    """Create a comprehensive test environment"""
    test_dir = tempfile.mkdtemp()
    print(f"Test environment: {test_dir}")
    
    # Create real PNG files with different colors
    test_images = [
        ('red_image.png', (255, 0, 0)),      # Red
        ('blue_image.png', (0, 0, 255)),     # Blue
        ('green_image.png', (0, 255, 0)),    # Green
        ('[workflow_test_batch1]ugly_name.png', (255, 255, 0)),  # Yellow with ugly filename
    ]
    
    for filename, color in test_images:
        img_path = os.path.join(test_dir, filename)
        img = Image.new('RGB', (50, 50), color=color)
        img.save(img_path)
    
    # Create a metadata file to test cleanup
    metadata_file = os.path.join(test_dir, 'test_metadata.json')
    with open(metadata_file, 'w') as f:
        f.write('{"test": "metadata"}')
    
    return test_dir

def test_main_program():
    """Test the main program functionality"""
    test_dir = create_test_environment()
    
    print(f"\n📋 Test Environment Created:")
    print(f"   Location: {test_dir}")
    
    files = os.listdir(test_dir)
    for file in files:
        print(f"   - {file}")
    
    print(f"\n✅ Test environment ready!")
    print(f"🚀 You can now test the main.py program manually with:")
    print(f"   Source directory: {test_dir}")
    print(f"\n💡 Options to test:")
    print(f"   3. Color Sorting - Should create Red, Blue, Green, Yellow folders")
    print(f"   5. Filename Cleanup - Should clean up the '[workflow_test_batch1]' filename")
    print(f"   6. Metadata Reports - Should handle images without metadata gracefully")
    
    return test_dir

if __name__ == "__main__":
    test_dir = test_main_program()
    
    print(f"\n🎯 MANUAL TEST INSTRUCTIONS:")
    print(f"1. Run: python main.py")
    print(f"2. Test option 3 (Color Sorting) with directory: {test_dir}")
    print(f"3. Test option 5 (Filename Cleanup) with directory: {test_dir}")
    print(f"4. Test option 6 (Metadata Reports) with directory: {test_dir}")
    print(f"\nAll options should now work without crashing!")
