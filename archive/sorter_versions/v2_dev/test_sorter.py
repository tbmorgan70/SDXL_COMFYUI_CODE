"""
Quick test script for the enhanced checkpoint sorter
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sorters.checkpoint_sorter import CheckpointSorter
from core.diagnostics import SortLogger

def test_checkpoint_sorter():
    """Test the checkpoint sorter with enhanced metadata formatting"""
    
    # Get test directory from user
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
    
    # Set up output directory
    output_dir = os.path.join(source_dir, "test_sorted")
    
    # Test options
    print("\n🎯 TEST OPTIONS:")
    print("1. Basic checkpoint sorting")
    print("2. Checkpoint + LoRA stack sorting")
    
    test_choice = input("Choose test type (1-2, default=1): ").strip()
    group_by_lora_stack = test_choice == "2"
    
    print(f"\n📋 TEST CONFIGURATION:")
    print(f"   Source: {source_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Files: {len(png_files)} PNG files")
    print(f"   Grouping: {'Checkpoint + LoRA Stack' if group_by_lora_stack else 'Checkpoint Only'}")
    print(f"   Operation: COPY (safe test)")
    print(f"   Metadata files: Yes (enhanced text format)")
    
    confirm = input("\nRun test? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Test cancelled")
        return
    
    # Run the test
    try:
        logger = SortLogger()
        sorter = CheckpointSorter(logger)
        
        print(f"\n🚀 Starting test sorting...")
        
        results = sorter.sort_by_checkpoint(
            source_dir=source_dir,
            output_dir=output_dir,
            move_files=False,  # Copy for safety during testing
            create_metadata_files=True,
            group_by_lora_stack=group_by_lora_stack
        )
        
        # Show results
        stats = results['sorter_stats']
        print(f"\n✅ TEST COMPLETE!")
        print(f"   Processed: {stats['total_images']} images")
        print(f"   Sorted: {stats['sorted_images']} images")
        print(f"   Folders created: {stats['folders_created']}")
        print(f"   Unknown checkpoints: {stats['unknown_checkpoint']}")
        print(f"   Failed extractions: {stats['failed_extractions']}")
        
        success_rate = (stats['sorted_images'] / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        print(f"\n📂 Check results in: {output_dir}")
        
        # Show created folders
        if 'checkpoint_folders' in results:
            print(f"\n📁 CREATED FOLDERS:")
            for folder_name, folder_path in results['checkpoint_folders'].items():
                file_count = len([f for f in os.listdir(folder_path) if f.lower().endswith('.png')])
                print(f"   {folder_name}: {file_count} images")
        
        # Offer to open output folder
        if input("\nOpen output folder? (y/n): ").lower() == 'y':
            os.startfile(output_dir)
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    test_checkpoint_sorter()
