"""
Test script for the enhanced file operations that move metadata with images.

This script creates test files and tests the new FileOperationsHandler to ensure
PNG images are moved along with their associated .txt metadata files.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.file_operations import FileOperationsHandler
from core.diagnostics import SortLogger

def create_test_files():
    """Create temporary test files for testing"""
    # Create temporary directory
    test_dir = tempfile.mkdtemp(prefix="sorter_test_")
    
    # Create test PNG file (mock - just a text file with .png extension)
    png_path = os.path.join(test_dir, "test_image.png")
    with open(png_path, 'w') as f:
        f.write("This is a mock PNG file for testing\n")
    
    # Create associated metadata file
    txt_path = os.path.join(test_dir, "test_image.txt")
    with open(txt_path, 'w') as f:
        f.write("=== COMFYUI METADATA REPORT ===\n")
        f.write("File: test_image.png\n")
        f.write("Base Model: realvisxlV50_v50Bakedvae.safetensors\n")
        f.write("LoRAs: DetailTweaker.safetensors, FilmGrain.safetensors\n")
        f.write("Positive Prompt: masterpiece, best quality, 1girl\n")
        f.write("Negative Prompt: worst quality, low quality\n")
    
    return test_dir, png_path, txt_path

def test_file_operations():
    """Test the FileOperationsHandler"""
    logger = SortLogger()
    handler = FileOperationsHandler(logger)
    
    print("🧪 Testing File Operations with Metadata...")
    print("=" * 50)
    
    # Create test files
    test_dir, png_path, txt_path = create_test_files()
    
    try:
        print(f"📁 Test directory: {test_dir}")
        print(f"🖼️ PNG file: {os.path.basename(png_path)}")
        print(f"📄 Metadata file: {os.path.basename(txt_path)}")
        print()
        
        # Test 1: Check metadata detection
        print("Test 1: Metadata Detection")
        metadata_files = handler.get_associated_metadata_files(png_path)
        print(f"Found metadata files: {[os.path.basename(f) for f in metadata_files]}")
        assert len(metadata_files) == 1, f"Expected 1 metadata file, found {len(metadata_files)}"
        assert metadata_files[0] == txt_path, "Metadata file path doesn't match"
        print("✅ Metadata detection works correctly")
        print()
        
        # Test 2: Move operation
        print("Test 2: Move Operation")
        dest_dir = os.path.join(test_dir, "sorted", "test_model")
        dest_png = os.path.join(dest_dir, "test_image.png")
        
        success, moved_files = handler.move_image_with_metadata(png_path, dest_png, move_files=True)
        
        print(f"Move success: {success}")
        print(f"Files moved: {len(moved_files)}")
        for moved_file in moved_files:
            print(f"  - {moved_file}")
        
        # Verify files were moved
        assert os.path.exists(dest_png), "PNG file was not moved to destination"
        assert os.path.exists(os.path.join(dest_dir, "test_image.txt")), "Metadata file was not moved"
        assert not os.path.exists(png_path), "Original PNG file still exists (should be moved)"
        assert not os.path.exists(txt_path), "Original metadata file still exists (should be moved)"
        
        print("✅ Move operation works correctly")
        print()
        
        # Test 3: Copy operation (recreate files first)
        print("Test 3: Copy Operation")
        
        # Create new test files
        test_dir2, png_path2, txt_path2 = create_test_files()
        dest_dir2 = os.path.join(test_dir2, "copied", "test_model") 
        dest_png2 = os.path.join(dest_dir2, "test_image_copy.png")
        
        success2, copied_files = handler.move_image_with_metadata(png_path2, dest_png2, move_files=False)
        
        print(f"Copy success: {success2}")
        print(f"Files copied: {len(copied_files)}")
        for copied_file in copied_files:
            print(f"  - {copied_file}")
        
        # Verify files were copied
        assert os.path.exists(dest_png2), "PNG file was not copied to destination"
        assert os.path.exists(os.path.join(dest_dir2, "test_image_copy.txt")), "Metadata file was not copied"
        assert os.path.exists(png_path2), "Original PNG file was removed (should be copied)"
        assert os.path.exists(txt_path2), "Original metadata file was removed (should be copied)"
        
        print("✅ Copy operation works correctly")
        print()
        
        print("🎉 All tests passed! The FileOperationsHandler is working correctly.")
        print("📋 Summary:")
        print("  - Metadata files are automatically detected")
        print("  - Move operations relocate both PNG and .txt files")
        print("  - Copy operations duplicate both PNG and .txt files")
        print("  - Directory structure is created as needed")
        
        # Cleanup
        shutil.rmtree(test_dir)
        shutil.rmtree(test_dir2)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        # Still cleanup on failure
        try:
            shutil.rmtree(test_dir)
        except:
            pass
        try:
            shutil.rmtree(test_dir2)
        except:
            pass
        return False
    
    return True

if __name__ == "__main__":
    test_file_operations()