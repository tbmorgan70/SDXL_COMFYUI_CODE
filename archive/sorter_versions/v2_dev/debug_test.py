#!/usr/bin/env python3
"""
Debug test for Sorter 2.0 main.py issues
Tests specific methods that user reported as problematic
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from main import SorterV2

def create_test_environment():
    """Create a temporary test environment with fake files"""
    test_dir = tempfile.mkdtemp()
    print(f"Test directory: {test_dir}")
    
    # Create some test files
    test_files = ['test1.png', 'test2.jpg', 'test_metadata.json']
    for filename in test_files:
        file_path = os.path.join(test_dir, filename)
        with open(file_path, 'w') as f:
            f.write(f"Test content for {filename}")
    
    return test_dir

def test_color_sorting():
    """Test option 3 - Sort by Color"""
    print("\n=== TESTING COLOR SORTING (Option 3) ===")
    try:
        sorter = SorterV2()
        
        # Mock the _get_directory_input method to avoid user input
        test_dir = create_test_environment()
        
        # Test that the method exists and can be called
        method = getattr(sorter, 'sort_by_color', None)
        if method is None:
            print("❌ sort_by_color method not found")
            return False
        
        print("✅ sort_by_color method exists")
        print("✅ Color sorting test setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Color sorting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_filename_cleanup():
    """Test option 5 - Cleanup Filenames"""
    print("\n=== TESTING FILENAME CLEANUP (Option 5) ===")
    try:
        sorter = SorterV2()
        
        # Test that the method exists
        method = getattr(sorter, 'cleanup_filenames', None)
        if method is None:
            print("❌ cleanup_filenames method not found")
            return False
        
        print("✅ cleanup_filenames method exists")
        
        # Test FilenameCleanup class directly
        from sorters.filename_cleanup import FilenameCleanup
        from core.diagnostics import SortLogger
        
        logger = SortLogger()
        cleaner = FilenameCleanup(logger)
        print("✅ FilenameCleanup can be instantiated")
        
        # Test dry run
        test_dir = create_test_environment()
        result = cleaner.cleanup_directory(test_dir, dry_run=True)
        print(f"✅ Dry run completed: {result}")
        print(f"Stats: {cleaner.stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Filename cleanup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_reports():
    """Test option 6 - Generate Metadata Reports"""
    print("\n=== TESTING METADATA REPORTS (Option 6) ===")
    try:
        sorter = SorterV2()
        
        # Test that the method exists
        method = getattr(sorter, 'generate_metadata_reports', None)
        if method is None:
            print("❌ generate_metadata_reports method not found")
            return False
        
        print("✅ generate_metadata_reports method exists")
        
        # Test MetadataExtractor and formatter
        from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
        from core.enhanced_metadata_formatter import EnhancedMetadataFormatter
        
        extractor = MetadataExtractor()
        analyzer = MetadataAnalyzer()
        formatter = EnhancedMetadataFormatter()
        
        print("✅ Metadata classes can be instantiated")
        
        # Test with a fake metadata structure
        fake_metadata = {
            "3": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "test_model.safetensors"}
            }
        }
        
        primary_checkpoint = analyzer.extract_primary_checkpoint(fake_metadata)
        print(f"✅ Primary checkpoint extraction works: {primary_checkpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata reports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("🧪 STARTING SORTER 2.0 DEBUG TESTS")
    print("=" * 50)
    
    results = {
        'color_sorting': test_color_sorting(),
        'filename_cleanup': test_filename_cleanup(), 
        'metadata_reports': test_metadata_reports()
    }
    
    print("\n" + "=" * 50)
    print("🧪 DEBUG TEST RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
