"""
File Operations Handler for Sorter 2.3

Enhanced file operations that handle moving PNG images along with their 
associated metadata files (.txt files with same basename).

Features:
- Move/copy PNG files with associated metadata
- Detect and handle metadata files automatically
- Comprehensive logging of all operations
- Error handling and recovery
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import logging

class FileOperationsHandler:
    """Handle file operations with associated metadata support"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.metadata_extensions = ['.txt']  # Could expand to include .json, .yml, etc.
    
    def get_associated_metadata_files(self, image_path: str) -> List[str]:
        """
        Find metadata files associated with an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of paths to associated metadata files
        """
        associated_files = []
        base_path = os.path.splitext(image_path)[0]
        
        for ext in self.metadata_extensions:
            metadata_path = f"{base_path}{ext}"
            if os.path.exists(metadata_path):
                associated_files.append(metadata_path)
        
        return associated_files
    
    def move_image_with_metadata(
        self, 
        source_image_path: str, 
        dest_image_path: str,
        move_files: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Move or copy an image file along with its associated metadata files.
        
        Args:
            source_image_path: Source path of the image
            dest_image_path: Destination path for the image  
            move_files: True to move files, False to copy
            
        Returns:
            Tuple of (success: bool, moved_files: List[str])
        """
        moved_files = []
        
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(dest_image_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Move/copy the main image file
            if move_files:
                shutil.move(source_image_path, dest_image_path)
                operation = "MOVED"
            else:
                shutil.copy2(source_image_path, dest_image_path)
                operation = "COPIED"
            
            moved_files.append(f"{operation}: {source_image_path} -> {dest_image_path}")
            
            # Find and move/copy associated metadata files
            metadata_files = self.get_associated_metadata_files(source_image_path)
            
            for metadata_file in metadata_files:
                # Calculate destination path for metadata file
                metadata_filename = os.path.basename(metadata_file)
                dest_base = os.path.splitext(dest_image_path)[0]
                metadata_ext = os.path.splitext(metadata_file)[1]
                dest_metadata_path = f"{dest_base}{metadata_ext}"
                
                try:
                    if move_files:
                        shutil.move(metadata_file, dest_metadata_path)
                        meta_operation = "MOVED"
                    else:
                        shutil.copy2(metadata_file, dest_metadata_path)
                        meta_operation = "COPIED"
                    
                    moved_files.append(f"{meta_operation}: {metadata_file} -> {dest_metadata_path}")
                    
                    if self.logger:
                        self.logger.log_info(f"Associated metadata {meta_operation.lower()}: {metadata_filename}")
                
                except Exception as e:
                    if self.logger:
                        self.logger.log_error(f"Failed to {operation.lower()} metadata file {metadata_file}: {e}")
                    # Continue with other files even if one metadata file fails
            
            return True, moved_files
            
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to {operation.lower()} image {source_image_path}: {e}")
            return False, []
    
    def batch_move_with_metadata(
        self,
        file_operations: List[Tuple[str, str]],
        move_files: bool = True,
        progress_callback=None
    ) -> Tuple[int, int, List[str]]:
        """
        Batch move/copy multiple image files with their metadata.
        
        Args:
            file_operations: List of (source_path, dest_path) tuples
            move_files: True to move files, False to copy
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_count, failed_count, all_moved_files)
        """
        successful_count = 0
        failed_count = 0
        all_moved_files = []
        
        total_files = len(file_operations)
        
        for i, (source_path, dest_path) in enumerate(file_operations):
            if progress_callback:
                progress_callback(i + 1, total_files, os.path.basename(source_path))
            
            success, moved_files = self.move_image_with_metadata(source_path, dest_path, move_files)
            
            if success:
                successful_count += 1
                all_moved_files.extend(moved_files)
            else:
                failed_count += 1
        
        return successful_count, failed_count, all_moved_files


# Helper function for backward compatibility
def move_image_with_metadata(source_image_path: str, dest_image_path: str, move_files: bool = True, logger=None) -> bool:
    """
    Convenience function to move/copy a single image with its metadata.
    
    Args:
        source_image_path: Source path of the image
        dest_image_path: Destination path for the image
        move_files: True to move files, False to copy
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    handler = FileOperationsHandler(logger)
    success, _ = handler.move_image_with_metadata(source_image_path, dest_image_path, move_files)
    return success