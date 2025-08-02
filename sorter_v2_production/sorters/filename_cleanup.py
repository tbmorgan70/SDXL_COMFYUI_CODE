"""
Filename Cleanup Module for Sorter 2.0

Cleans up filenames from previous sorting operations and removes unwanted metadata files.
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Dict
import json

class FilenameCleanup:
    """Clean up filenames and remove metadata files from previous sorting operations"""
    
    def __init__(self, logger):
        self.logger = logger
        self.stats = {
            'files_renamed': 0,
            'metadata_files_removed': 0,
            'errors': 0,
            'total_files': 0
        }
    
    def cleanup_directory(self, source_dir: str, remove_metadata_files: bool = True, 
                         rename_files: bool = True, filename_prefix: str = "image", 
                         dry_run: bool = False) -> bool:
        """
        Clean up a directory by renaming files and removing metadata files
        
        Args:
            source_dir: Directory to clean up
            remove_metadata_files: Remove _metadata.json files
            rename_files: Clean up filenames (remove workflow prefixes, etc.)
            filename_prefix: Prefix to use for cleaned filenames (default: "image")
            dry_run: Preview changes without making them
            
        Returns:
            Success status
        """
        # Reset stats for each operation
        self.stats = {
            'files_renamed': 0,
            'metadata_files_removed': 0,
            'errors': 0,
            'total_files': 0
        }
        
        self.logger.start_operation("Filename Cleanup")
        self.logger._write_log(f"Source: {source_dir}")
        self.logger._write_log(f"Remove metadata files: {remove_metadata_files}")
        self.logger._write_log(f"Rename files: {rename_files}")
        self.logger._write_log(f"Filename prefix: {filename_prefix}")
        self.logger._write_log(f"Dry run: {dry_run}")
        
        try:
            # Find all files to process
            files_to_process = []
            
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    files_to_process.append(file_path)
            
            self.stats['total_files'] = len(files_to_process)
            self.logger._write_log(f"Found {len(files_to_process)} files to process")
            
            processed = 0
            
            for file_path in files_to_process:
                processed += 1
                
                # Update progress
                if hasattr(self.logger, 'progress_callback') and self.logger.progress_callback:
                    self.logger.progress_callback(processed, len(files_to_process), os.path.basename(file_path))
                
                filename = os.path.basename(file_path)
                
                # Remove metadata files
                if remove_metadata_files and filename.endswith('_metadata.json'):
                    if not dry_run:
                        try:
                            os.remove(file_path)
                            self.stats['metadata_files_removed'] += 1
                            self.logger._write_log(f"Removed metadata file: {filename}")
                        except Exception as e:
                            self.logger._write_log(f"Error removing {filename}: {e}")
                            self.stats['errors'] += 1
                    else:
                        self.logger._write_log(f"Would remove metadata file: {filename}")
                        self.stats['metadata_files_removed'] += 1
                    continue
                
                # Clean up image filenames
                if rename_files and self._should_rename_file(filename):
                    new_filename = self._clean_filename(filename, filename_prefix)
                    if new_filename != filename:
                        new_path = os.path.join(os.path.dirname(file_path), new_filename)
                        
                        if not dry_run:
                            try:
                                # Ensure no conflict
                                if os.path.exists(new_path):
                                    new_path = self._resolve_naming_conflict(new_path)
                                
                                shutil.move(file_path, new_path)
                                self.stats['files_renamed'] += 1
                                self.logger._write_log(f"Renamed: {filename} → {os.path.basename(new_path)}")
                            except Exception as e:
                                self.logger._write_log(f"Error renaming {filename}: {e}")
                                self.stats['errors'] += 1
                        else:
                            self.logger._write_log(f"Would rename: {filename} → {new_filename}")
                            self.stats['files_renamed'] += 1
            
            # Log summary
            self.logger._write_log(f"Cleanup completed:")
            self.logger._write_log(f"  Files renamed: {self.stats['files_renamed']}")
            self.logger._write_log(f"  Metadata files removed: {self.stats['metadata_files_removed']}")
            self.logger._write_log(f"  Errors: {self.stats['errors']}")
            
            self.logger.end_operation("Filename Cleanup")
            return self.stats['errors'] == 0
            
        except Exception as e:
            self.logger._write_log(f"Cleanup failed: {str(e)}")
            self.logger.end_operation("Filename Cleanup")
            return False
    
    def _should_rename_file(self, filename: str) -> bool:
        """Check if a file should be renamed"""
        # Skip already clean filenames
        if not any(pattern in filename for pattern in ['[workflow', '$', 'batch', 'Gen ']):
            return False
        
        # Only process image files
        extensions = ['.png', '.jpg', '.jpeg', '.webp']
        return any(filename.lower().endswith(ext) for ext in extensions)
    
    def _clean_filename(self, filename: str, prefix: str = "image") -> str:
        """Clean up a filename by removing workflow prefixes and unnecessary parts"""
        # Extract file extension
        name, ext = os.path.splitext(filename)
        
        # Remove common workflow patterns
        patterns = [
            r'\[workflow_test_batch\d+\]\s*',  # [workflow_test_batch1] 
            r'Gen\s+\d+\s+',                   # Gen 31 
            r'\$\d+',                          # $0152
            r'_+',                             # Multiple underscores
            r'^[\s\-_]+',                      # Leading spaces, dashes, underscores
            r'[\s\-_]+$',                      # Trailing spaces, dashes, underscores
        ]
        
        cleaned = name
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Clean up remaining artifacts
        cleaned = re.sub(r'\s+', '_', cleaned)  # Replace spaces with underscores
        cleaned = re.sub(r'_+', '_', cleaned)   # Collapse multiple underscores
        cleaned = cleaned.strip('_-')          # Remove leading/trailing separators
        
        # Ensure we have a valid filename
        if not cleaned:
            cleaned = prefix
        
        # Add timestamp if still generic or matches the prefix exactly
        if cleaned.lower() in [prefix.lower(), 'image', 'img', 'pic', 'photo']:
            import time
            timestamp = str(int(time.time()))
            cleaned = f"{prefix}_{timestamp}"
        
        return f"{cleaned}{ext}"
    
    def _resolve_naming_conflict(self, file_path: str) -> str:
        """Resolve filename conflicts by adding numbers"""
        base_path = file_path
        name, ext = os.path.splitext(base_path)
        counter = 1
        
        while os.path.exists(file_path):
            file_path = f"{name}_{counter:03d}{ext}"
            counter += 1
        
        return file_path
