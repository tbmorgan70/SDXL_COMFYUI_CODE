"""
Test script for the enhanced batch sorter
This implements the working algorithm from your original final_batch_rename_sort.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_batch_sorter_clean import EnhancedBatchSorter

def test_enhanced_sorter():
    """Test the enhanced batch sorter"""
    
    print("🧪 Enhanced Batch Sorter Test")
    print("=" * 50)
    
    # Get test parameters
    source_dir = input("Enter source directory with PNG images: ").strip().strip('"\'')
    
    if not os.path.exists(source_dir):
        print("❌ Source directory not found")
        return
    
    # Count PNG files
    png_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.png')]
    if not png_files:
        print("❌ No PNG files found in source directory")
        return
    
    print(f"📊 Found {len(png_files)} PNG files")
    
    user_string = input("Enter user string for renaming (e.g., 'test_batch'): ").strip()
    if not user_string:
        print("❌ User string is required")
        return
    
    # Set up test output
    output_dir = os.path.join(source_dir, "test_enhanced_sorted")
    
    print(f"\n📋 TEST CONFIGURATION:")
    print(f"   Source: {source_dir}")
    print(f"   Output: {output_dir}")
    print(f"   User String: {user_string}")
    print(f"   Files: {len(png_files)} PNG files")
    print(f"   Operation: COPY (safe for testing)")
    print(f"   Metadata: Enhanced text format")
    
    confirm = input("\nRun test? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Test cancelled")
        return
    
    # Run the enhanced sorter
    try:
        sorter = EnhancedBatchSorter()
        
        print(f"\n🚀 Starting enhanced batch sort...")
        
        results = sorter.enhanced_batch_sort(
            source_dir=source_dir,
            user_string=user_string,
            output_dir=output_dir,
            move_files=False,  # Copy for safety
            create_metadata_files=True
        )
        
        # Show results
        stats = results['stats']
        print(f"\n✅ ENHANCED BATCH SORT COMPLETE!")
        print(f"   Total images: {stats['total_images']}")
        print(f"   Renamed: {stats['renamed_images']}")
        print(f"   Sorted: {stats['sorted_images']}")
        print(f"   Metadata files: {stats['metadata_files']}")
        
        success_rate = (stats['sorted_images'] / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        print(f"\n📂 Check results in: {output_dir}")
        
        # Show folder structure
        if os.path.exists(output_dir):
            print(f"\n📁 CREATED STRUCTURE:")
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    if item == "Gen Data":
                        file_count = len([f for f in os.listdir(item_path) if f.endswith('.txt')])
                        print(f"   📝 {item}: {file_count} metadata files")
                    else:
                        file_count = len([f for f in os.listdir(item_path) if f.lower().endswith('.png')])
                        print(f"   🖼️  {item}: {file_count} images")
        
        # Offer to open output folder
        if input("\nOpen output folder? (y/n): ").lower() == 'y':
            os.startfile(output_dir)
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    test_enhanced_sorter()
