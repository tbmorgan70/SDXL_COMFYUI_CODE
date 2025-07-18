"""
Image Flattener for Sorter 2.0

Flattens nested image folders into a single directory structure.
Includes enhanced logging and duplicate handling.
"""

import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.diagnostics import SortLogger

class ImageFlattener:
    """Enhanced image flattening with progress tracking and logging"""
    
    def __init__(self, logger: SortLogger = None):
        self.logger = logger or SortLogger()
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    
    def flatten_images(self, source_dir, target_dir="flattened_images", 
                      move_files=False, remove_empty_dirs=True):
        """
        Flatten all images from nested folders into a single target directory
        
        Args:
            source_dir: Source directory containing nested image folders
            target_dir: Target directory for flattened images
            move_files: Whether to move (True) or copy (False) files
            remove_empty_dirs: Whether to remove empty directories after flattening
        """
        source_path = Path(source_dir)
        target_path = Path(target_dir)
        
        # Start logging
        operation_name = "Image Flattening"
        self.logger.start_operation(operation_name)
        self.logger.log_config("Source", str(source_path))
        self.logger.log_config("Target", str(target_path))
        self.logger.log_config("Operation", "MOVE" if move_files else "COPY")
        self.logger.log_config("Remove empty dirs", str(remove_empty_dirs))
        
        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        self.logger.log_folder_operation("Created", str(target_path))
        
        # Find all image files
        image_files = []
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.image_extensions:
                    image_files.append(file_path)
        
        if not image_files:
            self.logger.log_error("No image files found in source directory")
            return False
        
        total_files = len(image_files)
        self.logger.log_info(f"Found {total_files} image files to flatten")
        
        # Flatten images
        self.logger.start_phase("File Flattening")
        
        moved_count = 0
        failed_count = 0
        duplicates_count = 0
        
        for i, file_path in enumerate(image_files):
            try:
                # Create unique filename if there's a collision
                target_file = target_path / file_path.name
                original_target = target_file
                counter = 1
                
                while target_file.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    target_file = target_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                    duplicates_count += 1
                
                # Move or copy the file
                if move_files:
                    shutil.move(str(file_path), str(target_file))
                    operation = "MOVED"
                else:
                    shutil.copy2(str(file_path), str(target_file))
                    operation = "COPIED"
                
                self.logger.log_file_operation(operation, str(file_path), str(target_file))
                moved_count += 1
                
                # Progress update every 25 files
                if i % 25 == 0:
                    self.logger.update_progress(i, total_files, file_path.name)
                
            except Exception as e:
                self.logger.log_error(f"Error processing {file_path}: {e}")
                failed_count += 1
        
        self.logger.end_phase("File Flattening")
        
        # Remove empty directories if requested
        removed_dirs = 0
        if remove_empty_dirs and move_files:  # Only remove if we moved files
            self.logger.start_phase("Empty Directory Cleanup")
            removed_dirs = self._remove_empty_dirs(source_path)
            self.logger.end_phase("Empty Directory Cleanup")
        
        # Log final statistics
        self.logger.end_operation(operation_name)
        
        print(f"\n=== IMAGE FLATTENING SUMMARY ===")
        print(f"Total images found: {total_files}")
        print(f"Successfully processed: {moved_count}")
        print(f"Failed: {failed_count}")
        print(f"Duplicates renamed: {duplicates_count}")
        print(f"Empty directories removed: {removed_dirs}")
        print(f"Success rate: {(moved_count/total_files)*100:.1f}%")
        
        return moved_count > 0
    
    def _remove_empty_dirs(self, path):
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
                    self.logger.log_folder_operation("Removed empty", str(root_path))
                    removed_count += 1
            except OSError:
                # Directory not empty or other error
                pass
        
        return removed_count
    
    def preview_flatten(self, source_dir):
        """
        Preview what would happen during flattening without actually moving files
        """
        source_path = Path(source_dir)
        
        print(f"🔍 FLATTENING PREVIEW for: {source_path}")
        print("=" * 60)
        
        # Find all image files and their locations
        folder_stats = {}
        total_images = 0
        
        for root, dirs, files in os.walk(source_path):
            folder = Path(root)
            image_count = 0
            
            for file in files:
                file_path = folder / file
                if file_path.suffix.lower() in self.image_extensions:
                    image_count += 1
                    total_images += 1
            
            if image_count > 0:
                relative_path = folder.relative_to(source_path) if folder != source_path else "ROOT"
                folder_stats[str(relative_path)] = image_count
        
        # Display results
        print(f"📊 Total images found: {total_images}")
        print(f"📂 Folders containing images: {len(folder_stats)}")
        print()
        
        print("📁 FOLDER BREAKDOWN:")
        for folder, count in sorted(folder_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {folder}: {count} images")
        
        # Check for potential name conflicts
        all_filenames = []
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.image_extensions:
                    all_filenames.append(file)
        
        from collections import Counter
        filename_counts = Counter(all_filenames)
        duplicates = {name: count for name, count in filename_counts.items() if count > 1}
        
        if duplicates:
            print(f"\n⚠️  POTENTIAL NAME CONFLICTS:")
            for filename, count in duplicates.items():
                print(f"  {filename}: appears {count} times")
            print(f"\n🔧 These files will be renamed with numbers: file_1.png, file_2.png, etc.")
        else:
            print(f"\n✅ No filename conflicts detected")
        
        return {
            'total_images': total_images,
            'folders': len(folder_stats),
            'folder_stats': folder_stats,
            'duplicates': len(duplicates)
        }
