#!/usr/bin/env python3
"""
Demo script to show how the Image Flattener handles ComfyUI metadata folders.
This creates a realistic ComfyUI sorted structure and demonstrates the flattening options.
"""

import os
import sys
from pathlib import Path
import shutil

def create_comfyui_demo_structure():
    """Create a realistic ComfyUI sorted folder structure"""
    demo_dir = Path("demo_comfyui_sorted")
    
    # Create the typical ComfyUI sorted structure
    folders = [
        "demo_comfyui_sorted/checkpoint_a",
        "demo_comfyui_sorted/checkpoint_b/lora1", 
        "demo_comfyui_sorted/checkpoint_b/lora2",
        "demo_comfyui_sorted/Gen Data",
        "demo_comfyui_sorted/Other Files"
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    # Create sample image files (what we want to flatten)
    image_files = [
        "demo_comfyui_sorted/checkpoint_a/image1.png",
        "demo_comfyui_sorted/checkpoint_a/image2.jpg", 
        "demo_comfyui_sorted/checkpoint_b/lora1/image3.png",
        "demo_comfyui_sorted/checkpoint_b/lora2/image4.jpeg",
        "demo_comfyui_sorted/checkpoint_b/lora2/image5.png"
    ]
    
    # Create sample metadata files (what we DON'T want to flatten)
    metadata_files = [
        "demo_comfyui_sorted/Gen Data/metadata1.txt",
        "demo_comfyui_sorted/Gen Data/workflow_summary.json",
        "demo_comfyui_sorted/Gen Data/generation_log.html",
        "demo_comfyui_sorted/Other Files/readme.txt",
        "demo_comfyui_sorted/Other Files/config.yaml"
    ]
    
    all_files = image_files + metadata_files
    
    for file_path in all_files:
        with open(file_path, 'w') as f:
            if file_path.endswith(('.png', '.jpg', '.jpeg')):
                f.write(f"[Fake image data for {Path(file_path).name}]")
            else:
                f.write(f"Sample metadata content for {Path(file_path).name}")
    
    print(f"✓ Created realistic ComfyUI structure in {demo_dir}")
    return str(demo_dir)

def show_structure(directory, title):
    """Display the directory structure"""
    print(f"\n{title}")
    print("=" * len(title))
    
    if not Path(directory).exists():
        print("Directory does not exist!")
        return
    
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = '  ' * level
        folder_name = os.path.basename(root) if level > 0 else os.path.basename(directory)
        print(f"{indent}{folder_name}/")
        subindent = '  ' * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

def cleanup_demo():
    """Remove demo directories"""
    demo_dirs = ["demo_comfyui_sorted", "demo_flattened_with_metadata", "demo_flattened_without_metadata"]
    for dir_name in demo_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned up {dir_name}")

def main():
    print("🧪 ComfyUI Image Flattener Demo")
    print("This demonstrates how the flattener handles 'Gen Data' and 'Other Files' folders")
    print("=" * 80)
    
    choice = input("\nChoose an option:\n1. Create demo and show behavior\n2. Clean up demo files\n3. Exit\n\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n📁 Creating realistic ComfyUI sorted structure...")
        demo_source = create_comfyui_demo_structure()
        
        show_structure(demo_source, "📋 Original ComfyUI Structure")
        
        print(f"\n🔍 ANALYSIS:")
        print(f"- Images are in: checkpoint_a/, checkpoint_b/lora1/, checkpoint_b/lora2/")
        print(f"- Metadata is in: Gen Data/ (contains .txt, .json, .html files)")
        print(f"- Other files are in: Other Files/ (contains .txt, .yaml files)")
        
        print(f"\n🧪 Testing flattener behavior...")
        
        # Import our unified_sorter to use the new flattening function
        from unified_sorter import UnifiedSorter
        
        # Create a dummy instance to use the method
        dummy_sorter = UnifiedSorter()
        dummy_sorter.flatten_src = demo_source
        dummy_sorter.flatten_out = "demo_flattened_with_metadata"
        
        # Test 1: Include metadata folders (old behavior)
        print(f"\n🔄 Test 1: Flattening WITH metadata folders...")
        dummy_sorter.flatten_skip_metadata_var.set(False)
        dummy_sorter.flatten_cleanup_var.set(False)
        dummy_sorter._flatten_with_exclusions_copy(demo_source, "demo_flattened_with_metadata", set(), cleanup=False)
        
        show_structure("demo_flattened_with_metadata", "📂 Result: WITH metadata processing")
        
        # Test 2: Skip metadata folders (new behavior)
        print(f"\n🔄 Test 2: Flattening SKIPPING metadata folders...")
        dummy_sorter._flatten_with_exclusions_copy(demo_source, "demo_flattened_without_metadata", {'Gen Data', 'Other Files'}, cleanup=False)
        
        show_structure("demo_flattened_without_metadata", "📂 Result: SKIPPING metadata folders")
        
        print(f"\n✅ Demo complete!")
        print(f"📊 SUMMARY:")
        print(f"- WITH metadata: Processes all image files from all folders")
        print(f"- SKIP metadata: Only processes image files from checkpoint/LoRA folders")
        print(f"- Metadata folders (Gen Data, Other Files) are preserved when skipped")
        print(f"\nRun option 2 to clean up demo files when done.")
        
    elif choice == "2":
        print("\n🧹 Cleaning up demo files...")
        cleanup_demo()
        print("✅ Cleanup complete!")
        
    elif choice == "3":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
