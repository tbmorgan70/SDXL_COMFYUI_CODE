"""
Quick Fix: Robust Large Batch ComfyUI Sorter
Temporary solution while we build Sorter 2.0
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path

# Add sorter to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'sorter'))

try:
    from sorter.final_batch_rename_sort import (
        extract_comfyui_metadata, 
        rename_files, 
        create_gen_meta_files, 
        sort_by_base
    )
    print("✅ Imported ComfyUI sorting functions")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def robust_comfy_sort(source_dir, user_string, output_dir=None, move_files=True):
    """
    Robust ComfyUI sorting that handles large batches without UI threading issues
    """
    print(f"\n🎯 Starting robust ComfyUI sort...")
    print(f"📁 Source: {source_dir}")
    print(f"👤 User string: {user_string}")
    print(f"📤 Output: {output_dir or 'auto-generated'}")
    print(f"🔄 Operation: {'MOVE' if move_files else 'COPY'}")
    
    start_time = time.time()
    
    try:
        # Step 1: Setup output directory
        if not output_dir:
            output_dir = os.path.join(source_dir, "sorted")
        
        print(f"\n📋 Step 1: Setting up output directory...")
        if os.path.exists(output_dir):
            response = input(f"Output directory exists. Remove it? (y/n): ").lower()
            if response == 'y':
                shutil.rmtree(output_dir)
                print("🗑️  Removed existing output directory")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 2: Rename files (with progress tracking)
        print(f"\n📋 Step 2: Renaming PNG files...")
        renamed_files = rename_files(source_dir, user_string)
        print(f"✅ Renamed {len(renamed_files)} files")
        
        # Step 3: Create metadata files
        print(f"\n📋 Step 3: Creating metadata files...")
        gen_data_dir = os.path.join(output_dir, 'Gen Data')
        create_gen_meta_files(source_dir, renamed_files, gen_data_dir)
        print(f"✅ Created metadata in {gen_data_dir}")
        
        # Step 4: Sort by base checkpoint
        print(f"\n📋 Step 4: Sorting by base checkpoint...")
        sort_by_base(source_dir, output_dir, move=move_files)
        print(f"✅ Sorted files by checkpoint")
        
        # Step 5: Handle other files
        print(f"\n📋 Step 5: Moving other files...")
        other_root = os.path.join(output_dir, 'Other Files')
        os.makedirs(other_root, exist_ok=True)
        
        other_count = 0
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            if os.path.isfile(file_path) and not filename.lower().endswith('.png'):
                shutil.move(file_path, os.path.join(other_root, filename))
                other_count += 1
        
        print(f"✅ Moved {other_count} other files")
        
        # Summary
        total_time = time.time() - start_time
        print(f"\n🎉 SUCCESS! Completed in {total_time:.1f} seconds")
        print(f"📊 Summary:")
        print(f"   - Renamed: {len(renamed_files)} PNG files")
        print(f"   - Other files: {other_count}")
        print(f"   - Output: {output_dir}")
        
        # Offer to open output folder
        open_folder = input(f"\nOpen output folder? (y/n): ").lower()
        if open_folder == 'y':
            os.startfile(output_dir)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        return False

def main():
    print("🚀 Robust ComfyUI Batch Sorter")
    print("=" * 50)
    
    # Get user inputs
    source_dir = input("Enter source directory path: ").strip().strip('"').strip("'")
    if not os.path.exists(source_dir):
        print(f"❌ Directory not found: {source_dir}")
        return
    
    user_string = input("Enter user string for naming: ").strip()
    if not user_string:
        print("❌ User string is required")
        return
    
    output_dir = input("Enter output directory (press Enter for auto): ").strip()
    if not output_dir:
        output_dir = None
    
    move_files = input("Move files? (y/n, default=y): ").lower() != 'n'
    
    # Confirm before starting
    png_count = len([f for f in os.listdir(source_dir) if f.lower().endswith('.png')])
    print(f"\n📊 Found {png_count} PNG files to process")
    
    confirm = input("Proceed? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled")
        return
    
    # Start processing
    success = robust_comfy_sort(source_dir, user_string, output_dir, move_files)
    
    if success:
        print("\n✅ All done! Your files have been sorted.")
    else:
        print("\n❌ Processing failed. Check the error messages above.")

if __name__ == "__main__":
    main()
