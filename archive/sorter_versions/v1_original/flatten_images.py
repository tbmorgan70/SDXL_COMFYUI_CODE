import os
import shutil
from pathlib import Path

def flatten_images(source_dir, target_dir="flattened_images"):
    """
    Flatten all images from nested folders into a single target directory
    and remove empty folders afterwards.
    """
    # Create target directory if it doesn't exist
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    
    moved_count = 0
    source_path = Path(source_dir)
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(source_path):
        for file in files:
            file_path = Path(root) / file
            file_ext = file_path.suffix.lower()
            
            # Check if it's an image file
            if file_ext in image_extensions:
                # Create unique filename if there's a collision
                target_file = target_path / file
                counter = 1
                while target_file.exists():
                    name_part = file_path.stem
                    target_file = target_path / f"{name_part}_{counter}{file_ext}"
                    counter += 1
                
                # Move the file
                try:
                    shutil.move(str(file_path), str(target_file))
                    print(f"Moved: {file_path} -> {target_file}")
                    moved_count += 1
                except Exception as e:
                    print(f"Error moving {file_path}: {e}")
    
    print(f"\nMoved {moved_count} images to {target_dir}")
    
    # Remove empty directories
    remove_empty_dirs(source_path)

def remove_empty_dirs(path):
    """
    Remove empty directories recursively, starting from the deepest level.
    """
    removed_count = 0
    
    # Walk the directory tree bottom-up
    for root, dirs, files in os.walk(path, topdown=False):
        root_path = Path(root)
        
        # Skip the root directory itself
        if root_path == path:
            continue
            
        try:
            # Try to remove if directory is empty
            if not any(root_path.iterdir()):
                root_path.rmdir()
                print(f"Removed empty directory: {root_path}")
                removed_count += 1
        except OSError:
            # Directory not empty or other error
            pass
    
    print(f"\nRemoved {removed_count} empty directories")

if __name__ == "__main__":
    # Use current directory as source
    current_dir = "."
    target_directory = "all_images"
    
    print(f"Flattening images from '{current_dir}' to '{target_directory}'...")
    print("This will move all images from nested folders into a single folder.")
    
    confirm = input("Do you want to continue? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        flatten_images(current_dir, target_directory)
        print("Operation completed!")
    else:
        print("Operation cancelled.")