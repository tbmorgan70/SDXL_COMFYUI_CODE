#!/usr/bin/env python3
"""
Demo script for the Image Flattener functionality.
This shows how to use the flatten_images function directly from command line.
"""

import os
import sys
from pathlib import Path
import flatten_images

def create_demo_structure():
    """Create a demo nested folder structure with some sample files"""
    demo_dir = Path("demo_nested")
    
    # Create nested structure
    folders = [
        "demo_nested/checkpoint_a/lora1",
        "demo_nested/checkpoint_a/lora2", 
        "demo_nested/checkpoint_b/lora3",
        "demo_nested/checkpoint_c"
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    # Create some dummy image files
    sample_files = [
        "demo_nested/checkpoint_a/lora1/sample1.png",
        "demo_nested/checkpoint_a/lora1/sample2.jpg",
        "demo_nested/checkpoint_a/lora2/sample3.png",
        "demo_nested/checkpoint_b/lora3/sample4.jpeg",
        "demo_nested/checkpoint_c/sample5.png",
        "demo_nested/readme.txt"  # Non-image file should be ignored
    ]
    
    for file_path in sample_files:
        with open(file_path, 'w') as f:
            f.write(f"Sample content for {Path(file_path).name}")
    
    print(f"✓ Created demo structure in {demo_dir}")
    return str(demo_dir)

def cleanup_demo():
    """Remove demo directories"""
    import shutil
    demo_dirs = ["demo_nested", "demo_flattened"]
    for dir_name in demo_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned up {dir_name}")

def main():
    print("🧪 Image Flattener Demo")
    print("=" * 50)
    
    # Ask user what they want to do
    print("\nChoose an option:")
    print("1. Run demo with sample files")
    print("2. Flatten your own folder")
    print("3. Clean up demo files")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n📁 Creating demo nested structure...")
        demo_source = create_demo_structure()
        
        print(f"\n📋 Demo structure created at: {demo_source}")
        print("Contents:")
        for root, dirs, files in os.walk(demo_source):
            level = root.replace(demo_source, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        print(f"\n🔄 Flattening images from {demo_source} to demo_flattened...")
        flatten_images.flatten_images(demo_source, "demo_flattened")
        
        print("\n✅ Demo complete! Check the 'demo_flattened' folder.")
        print("Run option 3 to clean up demo files when done.")
    
    elif choice == "2":
        source_folder = input("\nEnter source folder path: ").strip().strip('"')
        if not os.path.exists(source_folder):
            print("❌ Source folder does not exist!")
            return
        
        output_folder = input("Enter output folder name (or press Enter for 'flattened_images'): ").strip()
        if not output_folder:
            output_folder = "flattened_images"
        
        print(f"\n🔄 Flattening images from {source_folder} to {output_folder}...")
        flatten_images.flatten_images(source_folder, output_folder)
        print("✅ Flattening complete!")
    
    elif choice == "3":
        print("\n🧹 Cleaning up demo files...")
        cleanup_demo()
        print("✅ Cleanup complete!")
    
    elif choice == "4":
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
