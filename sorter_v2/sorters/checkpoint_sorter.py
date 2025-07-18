"""
Sorter 2.0 - Base Checkpoint Sorter

Your #1 priority feature: Sort images by base checkpoint/model.
Handles large batches efficiently with proper error recovery.

Features:
- Robust base checkpoint detection
- Clean folder naming (removes paths, extensions)
- Move or copy operations
- Metadata preservation
- Conflict resolution
- Detailed logging
"""

import os
import shutil
import json
import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.diagnostics import SortLogger

class CheckpointSorter:
    """Sort images by their base checkpoint/model"""
    
    def __init__(self, logger: Optional[SortLogger] = None):
        self.metadata_extractor = MetadataExtractor()
        self.metadata_analyzer = MetadataAnalyzer()
        self.logger = logger or SortLogger()
        
        # Statistics
        self.stats = {
            'total_images': 0,
            'sorted_images': 0,
            'unknown_checkpoint': 0,
            'failed_extractions': 0,
            'folders_created': 0,
            'duplicates_handled': 0
        }
        
        # Folder mapping for organization
        self.checkpoint_folders = {}
    
    def sort_by_checkpoint(
        self, 
        source_dir: str, 
        output_dir: str, 
        move_files: bool = True,
        create_metadata_files: bool = True,
        preserve_structure: bool = False,
        rename_files: bool = False,
        user_prefix: str = ""
    ) -> Dict[str, any]:
        """
        Sort images by base checkpoint into organized folders
        
        Args:
            source_dir: Directory containing images to sort
            output_dir: Base output directory for sorted images  
            move_files: True to move files, False to copy
            create_metadata_files: Create JSON metadata files alongside images
            preserve_structure: Keep original subfolder structure
            rename_files: True to rename files with sequential numbering
            user_prefix: Custom prefix for renamed files (e.g. "nova_skyrift")
            
        Returns:
            Dictionary with sorting results and statistics
        """
        
        self.logger.start_operation("Checkpoint Sorting")
        self.logger._write_log(f"Source: {source_dir}")
        self.logger._write_log(f"Output: {output_dir}")
        self.logger._write_log(f"Operation: {'MOVE' if move_files else 'COPY'}")
        
        # Find all PNG files
        png_files = self._find_png_files(source_dir, preserve_structure)
        self.stats['total_images'] = len(png_files)
        
        if not png_files:
            self.logger.log_error("No PNG files found in source directory", source_dir, "No Input")
            return self._get_results()
        
        self.logger._write_log(f"Found {len(png_files)} PNG files to process")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Phase 1: Extract all metadata (with progress tracking)
        self.logger.start_operation("Metadata Extraction", len(png_files))
        metadata_results = self._extract_all_metadata(png_files)
        self.logger.complete_operation()
        
        # Phase 2: Analyze and group by checkpoint
        self.logger.start_operation("Checkpoint Analysis")
        checkpoint_groups = self._group_by_checkpoint(png_files, metadata_results)
        self.logger.complete_operation()
        
        # Phase 3: Create folder structure
        self.logger.start_operation("Folder Creation")
        self._create_checkpoint_folders(output_dir, checkpoint_groups.keys())
        self.logger.complete_operation()
        
        # Phase 4: Sort files into folders
        self.logger.start_operation("File Sorting", len(png_files))
        try:
            self._sort_files_to_folders(
                png_files, metadata_results, checkpoint_groups, 
                output_dir, move_files, create_metadata_files,
                preserve_structure, rename_files, user_prefix
            )
        except Exception as e:
            self.logger._write_log(f"ERROR in file sorting: {str(e)}")
            import traceback
            self.logger._write_log(f"Traceback: {traceback.format_exc()}")
        self.logger.complete_operation()
        
        # Generate summary
        results = self._get_results()
        self._log_summary(results)
        
        return results
    
    def _find_png_files(self, source_dir: str, preserve_structure: bool) -> List[Tuple[str, str]]:
        """Find all PNG files, optionally preserving subfolder structure"""
        png_files = []
        
        if preserve_structure:
            # Recursively find files, preserving relative paths
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.lower().endswith('.png'):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(root, source_dir)
                        png_files.append((full_path, rel_path if rel_path != '.' else ''))
        else:
            # Just the source directory
            for file in os.listdir(source_dir):
                if file.lower().endswith('.png'):
                    full_path = os.path.join(source_dir, file)
                    png_files.append((full_path, ''))
        
        return png_files
    
    def _extract_all_metadata(self, png_files: List[Tuple[str, str]]) -> Dict[str, Optional[Dict]]:
        """Extract metadata from all PNG files with progress tracking"""
        file_paths = [file_info[0] for file_info in png_files]
        
        def progress_callback(current, total, filename):
            self.logger.update_progress(current, filename)
        
        return self.metadata_extractor.extract_batch(file_paths, progress_callback)
    
    def _group_by_checkpoint(
        self, 
        png_files: List[Tuple[str, str]], 
        metadata_results: Dict[str, Optional[Dict]]
    ) -> Dict[str, List[Tuple[str, str]]]:
        """Group files by their primary checkpoint"""
        checkpoint_groups = {}
        
        for file_path, rel_path in png_files:
            metadata = metadata_results.get(file_path)
            
            if metadata:
                # Extract primary checkpoint
                primary_checkpoint = self.metadata_analyzer.extract_primary_checkpoint(metadata)
                
                if primary_checkpoint:
                    # Clean up checkpoint name for folder naming
                    folder_name = self._clean_checkpoint_name(primary_checkpoint)
                    
                    if folder_name not in checkpoint_groups:
                        checkpoint_groups[folder_name] = []
                    
                    checkpoint_groups[folder_name].append((file_path, rel_path))
                else:
                    # No checkpoint found
                    if 'Unknown_Checkpoint' not in checkpoint_groups:
                        checkpoint_groups['Unknown_Checkpoint'] = []
                    
                    checkpoint_groups['Unknown_Checkpoint'].append((file_path, rel_path))
                    self.stats['unknown_checkpoint'] += 1
            else:
                # Metadata extraction failed
                if 'No_Metadata' not in checkpoint_groups:
                    checkpoint_groups['No_Metadata'] = []
                
                checkpoint_groups['No_Metadata'].append((file_path, rel_path))
                self.stats['failed_extractions'] += 1
        
        self.logger._write_log(f"Grouped into {len(checkpoint_groups)} checkpoint categories:")
        for checkpoint, files in checkpoint_groups.items():
            self.logger._write_log(f"  {checkpoint}: {len(files)} files")
        
        return checkpoint_groups
    
    def _clean_checkpoint_name(self, checkpoint_path: str) -> str:
        """Clean checkpoint name for use as folder name"""
        # Remove file extension
        name = Path(checkpoint_path).stem
        
        # Remove path separators and replace with underscores
        name = name.replace('\\', '_').replace('/', '_')
        
        # Remove or replace problematic characters
        name = re.sub(r'[<>:"|?*]', '_', name)
        
        # Remove version numbers in some cases (optional - you may want to keep them)
        # name = re.sub(r'_v\d+(\.\d+)?$', '', name)
        
        # Limit length
        if len(name) > 50:
            name = name[:50]
        
        return name
    
    def _create_checkpoint_folders(self, output_dir: str, checkpoint_names: List[str]):
        """Create folders for each checkpoint"""
        for checkpoint_name in checkpoint_names:
            folder_path = os.path.join(output_dir, checkpoint_name)
            os.makedirs(folder_path, exist_ok=True)
            self.checkpoint_folders[checkpoint_name] = folder_path
            self.logger.log_folder_created(folder_path)
            self.stats['folders_created'] += 1
    
    def _sort_files_to_folders(
        self,
        png_files: List[Tuple[str, str]],
        metadata_results: Dict[str, Optional[Dict]],
        checkpoint_groups: Dict[str, List[Tuple[str, str]]],
        output_dir: str,
        move_files: bool,
        create_metadata_files: bool,
        preserve_structure: bool = False,
        rename_files: bool = False,
        user_prefix: str = ""
    ):
        """Sort files into their checkpoint folders"""
        # Debug logging
        self.logger._write_log(f"DEBUG: Starting file sorting with {len(checkpoint_groups)} checkpoint groups")
        for checkpoint, files in checkpoint_groups.items():
            self.logger._write_log(f"DEBUG: {checkpoint}: {len(files)} files")
        
        # Calculate total files for progress tracking
        total_files = sum(len(file_list) for file_list in checkpoint_groups.values())
        self.logger._write_log(f"DEBUG: Total files to process: {total_files}")
        file_count = 0
        
        for checkpoint_name, file_list in checkpoint_groups.items():
            self.logger._write_log(f"DEBUG: Processing checkpoint {checkpoint_name} with {len(file_list)} files")
            
            # Check if checkpoint folder exists
            if checkpoint_name not in self.checkpoint_folders:
                self.logger._write_log(f"ERROR: No folder mapping for checkpoint {checkpoint_name}")
                continue
                
            checkpoint_folder = self.checkpoint_folders[checkpoint_name]
            self.logger._write_log(f"DEBUG: Target folder: {checkpoint_folder}")
            
            for file_path, rel_path in file_list:
                file_count += 1
                self.logger._write_log(f"DEBUG: Processing file {file_count}/{total_files}: {file_path}")
                
                # Update progress using the logger's callback system
                if hasattr(self.logger, 'progress_callback') and self.logger.progress_callback:
                    self.logger.progress_callback(file_count, total_files, os.path.basename(file_path))
                
                try:
                    # Determine destination path
                    filename = os.path.basename(file_path)
                    
                    # Apply renaming if requested
                    if rename_files and user_prefix:
                        # Get file extension
                        _, ext = os.path.splitext(filename)
                        # Create sequential filename: userprefix_img###.png
                        new_filename = f"{user_prefix}_img{file_count}{ext}"
                        filename = new_filename
                    
                    if rel_path:  # Preserve subfolder structure
                        dest_folder = os.path.join(checkpoint_folder, rel_path)
                        os.makedirs(dest_folder, exist_ok=True)
                        dest_path = os.path.join(dest_folder, filename)
                    else:
                        dest_path = os.path.join(checkpoint_folder, filename)
                    
                    # Handle filename conflicts
                    dest_path = self._resolve_filename_conflict(dest_path)
                    
                    # Move or copy the file
                    if move_files:
                        shutil.move(file_path, dest_path)
                        operation = "MOVE"
                    else:
                        shutil.copy2(file_path, dest_path)
                        operation = "COPY"
                    
                    self.logger.log_file_operation(operation, file_path, dest_path)
                    self.stats['sorted_images'] += 1
                    
                    # Create metadata file if requested
                    if create_metadata_files:
                        metadata = metadata_results.get(file_path)
                        if metadata:
                            self._create_metadata_file(dest_path, metadata)
                
                except Exception as e:
                    self.logger.log_error(f"Failed to sort file: {str(e)}", file_path, "File Operation")
    
    def _resolve_filename_conflict(self, dest_path: str) -> str:
        """Resolve filename conflicts by adding numbers"""
        if not os.path.exists(dest_path):
            return dest_path
        
        base, ext = os.path.splitext(dest_path)
        counter = 1
        
        while os.path.exists(dest_path):
            dest_path = f"{base}_{counter}{ext}"
            counter += 1
            
        self.stats['duplicates_handled'] += 1
        return dest_path
    
    def _create_metadata_file(self, image_path: str, metadata: Dict):
        """Create a JSON metadata file alongside the image"""
        base_path = os.path.splitext(image_path)[0]
        metadata_path = f"{base_path}_metadata.json"
        
        # Create simplified metadata for readability
        simplified_metadata = {
            'image_file': os.path.basename(image_path),
            'checkpoints': self.metadata_analyzer.extract_checkpoints(metadata),
            'primary_checkpoint': self.metadata_analyzer.extract_primary_checkpoint(metadata),
            'loras': self.metadata_analyzer.extract_loras(metadata),
            'sampling_params': self.metadata_analyzer.extract_sampling_params(metadata),
            'prompts': self.metadata_analyzer.extract_prompts(metadata),
            'full_metadata': metadata
        }
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(simplified_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.log_error(f"Failed to create metadata file: {str(e)}", metadata_path, "Metadata Write")
    
    def _get_results(self) -> Dict[str, any]:
        """Get comprehensive sorting results"""
        extractor_stats = self.metadata_extractor.get_statistics()
        
        return {
            'sorter_stats': self.stats,
            'metadata_stats': extractor_stats,
            'checkpoint_folders': self.checkpoint_folders,
            'session_summary': self.logger.get_summary()
        }
    
    def _log_summary(self, results: Dict[str, any]):
        """Log comprehensive summary"""
        stats = results['sorter_stats']
        
        self.logger._write_log("\n=== CHECKPOINT SORTING SUMMARY ===")
        self.logger._write_log(f"Total images found: {stats['total_images']}")
        self.logger._write_log(f"Successfully sorted: {stats['sorted_images']}")
        self.logger._write_log(f"Unknown checkpoint: {stats['unknown_checkpoint']}")
        self.logger._write_log(f"Failed extractions: {stats['failed_extractions']}")
        self.logger._write_log(f"Folders created: {stats['folders_created']}")
        self.logger._write_log(f"Duplicates handled: {stats['duplicates_handled']}")
        
        success_rate = (stats['sorted_images'] / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
        self.logger._write_log(f"Success rate: {success_rate:.1f}%")


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    
    # Test the checkpoint sorter
    sorter = CheckpointSorter()
    
    source = input("Enter source directory: ").strip().strip('"\'')
    output = input("Enter output directory (or press Enter for 'sorted'): ").strip().strip('"\'')
    
    if not output:
        output = os.path.join(source, "sorted")
    
    move_files = input("Move files? (y/n, default=n): ").lower() == 'y'
    
    if os.path.exists(source):
        print(f"\n🚀 Starting checkpoint sorting...")
        
        results = sorter.sort_by_checkpoint(
            source_dir=source,
            output_dir=output,
            move_files=move_files,
            create_metadata_files=True
        )
        
        print(f"\n✅ Sorting complete!")
        print(f"Check results in: {output}")
        
        # Offer to open output folder
        open_folder = input("Open output folder? (y/n): ").lower() == 'y'
        if open_folder:
            os.startfile(output)
    else:
        print("❌ Source directory not found")
