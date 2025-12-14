"""
Sorter 2.0 - LoRA Stack Sorter

Sort images purely by their LoRA combinations, ignoring checkpoints, VAE, CLIP strength, 
and other parameters. Groups images that use the same set of LoRAs together.

Features:
- Pure LoRA-based grouping
- Ignores all other parameters (checkpoint, VAE, etc.)
- Supports file moving or copying
- Metadata file generation
- File renaming with custom prefixes
- Comprehensive progress tracking
"""

import os
import sys
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.enhanced_metadata_formatter import EnhancedMetadataFormatter
from core.diagnostics import SortLogger
from core.file_operations import FileOperationsHandler


class LoRAStackSorter:
    """Sort images by LoRA stack combinations only"""
    
    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
        self.metadata_formatter = EnhancedMetadataFormatter()
        self.logger = SortLogger()
        self.file_handler = FileOperationsHandler(self.logger)
        
        # Statistics
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'moved_images': 0,
            'copied_images': 0,
            'metadata_files_created': 0,
            'renamed_files': 0,
            'failed_operations': 0,
            'lora_groups_created': 0,
            'no_lora_count': 0
        }
    
    def sort_by_lora_stack(
        self,
        source_dir: str,
        output_dir: Optional[str] = None,
        move_files: bool = False,
        create_metadata: bool = True,
        rename_files: bool = False,
        rename_prefix: str = "lora",
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Sort images by their LoRA stack combinations
        
        Args:
            source_dir: Directory containing PNG images
            output_dir: Output directory (creates 'lora_sorted' if None)
            move_files: Whether to move files (vs copy)
            create_metadata: Whether to create metadata text files
            rename_files: Whether to rename files
            rename_prefix: Prefix for renamed files
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing operation results and statistics
        """
        
        # Store parameters
        self.progress_callback = progress_callback
        
        self.logger.start_operation("LoRA Stack Sorting", 0)
        self.logger.log_info(f"Starting LoRA stack sorting in: {source_dir}")
        self.logger.log_info(f"Output directory: {output_dir or 'auto-generated'}")
        self.logger.log_info(f"Move files: {move_files}")
        self.logger.log_info(f"Create metadata: {create_metadata}")
        self.logger.log_info(f"Rename files: {rename_files}")
        
        # Debug: Show absolute paths
        print(f"DEBUG: Source directory absolute path: {os.path.abspath(source_dir)}")
        print(f"DEBUG: Output directory: {output_dir}")
        print(f"DEBUG: Source directory exists: {os.path.exists(source_dir)}")
        print(f"DEBUG: Source directory contents:")
        try:
            items = list(os.listdir(source_dir))
            print(f"DEBUG: Total items in directory: {len(items)}")
            png_count = len([f for f in items if f.lower().endswith('.png')])
            print(f"DEBUG: PNG files by simple count: {png_count}")
            subdirs = [f for f in items if os.path.isdir(os.path.join(source_dir, f))]
            print(f"DEBUG: Subdirectories: {subdirs}")
        except Exception as e:
            print(f"DEBUG: Error listing directory: {e}")
        
        try:
            # Set up output directory
            if not output_dir:
                output_dir = os.path.join(source_dir, "lora_sorted")
            os.makedirs(output_dir, exist_ok=True)
            
            # Find all PNG files
            png_files = self._find_png_files(source_dir)
            
            if not png_files:
                self.logger.log_info("No PNG files found")
                return self._get_results()
            
            self.stats['total_images'] = len(png_files)
            self.logger.log_info(f"Found {len(png_files)} PNG files to process")
            
            # Send initial progress update
            if self.progress_callback:
                self.progress_callback(0, len(png_files), "Analyzing LoRA stacks...")
            
            # Extract metadata and group by LoRA stack
            self.logger.start_operation("Metadata Extraction", len(png_files))
            lora_groups, metadata_cache = self._group_by_lora_stack(png_files)
            
            # Process each LoRA group
            self.logger.start_operation("Processing LoRA Groups", len(png_files))
            self._process_lora_groups(lora_groups, metadata_cache, output_dir, move_files, create_metadata, rename_files, rename_prefix)
            
            # Log final summary
            results = self._get_results()
            self._log_summary(results)
            
            return results
            
        except Exception as e:
            self.logger.log_error(f"Fatal error during LoRA stack sorting: {str(e)}")
            raise
        finally:
            self.logger.end_operation("LoRA Stack Sorting")
    
    def _find_png_files(self, source_dir: str) -> List[str]:
        """Find all PNG files in the source directory (not subdirectories)"""
        png_files = []
        source_path = Path(source_dir)
        
        print(f"DEBUG: _find_png_files called with: {source_dir}")
        print(f"DEBUG: source_path resolved to: {source_path.resolve()}")
        
        # Use iterdir() to only get files directly in the source directory
        try:
            all_items = list(source_path.iterdir())
            print(f"DEBUG: Found {len(all_items)} total items in directory")
            
            for item in all_items:
                print(f"DEBUG: Checking item: {item} (is_file: {item.is_file()}, suffix: {item.suffix})")
                if item.is_file() and item.suffix.lower() in ['.png']:
                    png_files.append(str(item))
                    print(f"DEBUG: Added PNG file: {item}")
                elif item.is_dir():
                    print(f"DEBUG: Skipping directory: {item}")
                    
        except Exception as e:
            print(f"DEBUG: Exception in _find_png_files: {e}")
            self.logger.log_error(f"Error scanning directory {source_dir}: {str(e)}")
        
        print(f"DEBUG: Total PNG files found by _find_png_files: {len(png_files)}")
        return png_files
    
    def _group_by_lora_stack(self, png_files: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, Dict]]:
        """Group PNG files by their LoRA stack signatures and cache metadata"""
        lora_groups = {}
        metadata_cache = {}  # Cache metadata to avoid re-extraction
        
        for i, file_path in enumerate(png_files, 1):
            try:
                # Check if file still exists (in case of partial previous runs)
                if not os.path.exists(file_path):
                    self.logger.log_info(f"Skipping missing file: {os.path.basename(file_path)}")
                    continue
                
                # Extract metadata
                metadata = self.metadata_extractor.extract_single(file_path)
                
                if metadata:
                    # Cache the metadata for later use
                    metadata_cache[file_path] = metadata
                    
                    # Get LoRA stack signature
                    lora_signature = self.metadata_formatter.get_lora_stack_signature(metadata)
                    
                    if lora_signature:
                        if lora_signature not in lora_groups:
                            lora_groups[lora_signature] = []
                        lora_groups[lora_signature].append(file_path)
                        self.logger.log_info(f"File {os.path.basename(file_path)} -> LoRA stack: {lora_signature}")
                    else:
                        # No LoRAs found
                        no_lora_key = "NO_LORAS"
                        if no_lora_key not in lora_groups:
                            lora_groups[no_lora_key] = []
                        lora_groups[no_lora_key].append(file_path)
                        self.stats['no_lora_count'] += 1
                        self.logger.log_info(f"File {os.path.basename(file_path)} -> No LoRAs found")
                else:
                    self.logger.log_info(f"No metadata found for: {os.path.basename(file_path)}")
                    self.stats['failed_operations'] += 1
                
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i, len(png_files), f"Analyzing: {os.path.basename(file_path)}")
                
            except Exception as e:
                self.logger.log_error(f"Failed to process {os.path.basename(file_path)}: {str(e)}")
                self.stats['failed_operations'] += 1
        
        self.stats['lora_groups_created'] = len(lora_groups)
        self.logger.log_info(f"Created {len(lora_groups)} LoRA groups")
        
        return lora_groups, metadata_cache
    
    def _process_lora_groups(
        self, 
        lora_groups: Dict[str, List[str]], 
        metadata_cache: Dict[str, Dict],
        output_dir: str, 
        move_files: bool, 
        create_metadata: bool, 
        rename_files: bool, 
        rename_prefix: str
    ):
        """Process each LoRA group by organizing files"""
        processed_count = 0
        total_files = sum(len(files) for files in lora_groups.values())
        
        for lora_signature, file_list in lora_groups.items():
            # Determine group directory and safe name
            if lora_signature == "NO_LORAS":
                group_dir = os.path.join(output_dir, "no_loras")
                safe_name = "no_loras"
            else:
                # Clean up signature for folder name
                safe_name = self._sanitize_folder_name(lora_signature)
                group_dir = os.path.join(output_dir, safe_name)
            
            try:
                os.makedirs(group_dir, exist_ok=True)
                
                # Process each file in this group
                for i, file_path in enumerate(file_list, 1):
                    filename = os.path.basename(file_path)
                    try:
                        processed_count += 1
                        
                        # Determine new filename
                        if rename_files:
                            base_name = os.path.splitext(filename)[0]
                            new_filename = f"{rename_prefix}_{i:03d}_{base_name}.png"
                            self.stats['renamed_files'] += 1
                        else:
                            new_filename = filename
                        
                        # Move or copy file with its metadata
                        dest_path = os.path.join(group_dir, new_filename)
                        
                        success, moved_files = self.file_handler.move_image_with_metadata(
                            file_path, dest_path, move_files
                        )
                        
                        if success:
                            if move_files:
                                self.stats['moved_images'] += 1
                                self.logger.log_info(f"Moved: {filename} -> {safe_name}/{new_filename}")
                            else:
                                self.stats['copied_images'] += 1
                                self.logger.log_info(f"Copied: {filename} -> {safe_name}/{new_filename}")
                            
                            # Log all moved files (image + metadata)
                            for moved_file in moved_files:
                                self.logger.log_info(moved_file)
                        else:
                            operation = "move" if move_files else "copy"
                            raise Exception(f"Failed to {operation} file")
                        
                        # Create metadata file if requested
                        if create_metadata:
                            try:
                                # Use cached metadata if available, otherwise extract from destination
                                metadata = metadata_cache.get(file_path)
                                if not metadata:
                                    metadata = self.metadata_extractor.extract_single(dest_path)
                                
                                if metadata:
                                    metadata_path = os.path.splitext(dest_path)[0] + ".txt"
                                    formatted_text = self.metadata_formatter.format_metadata_to_text(metadata, dest_path)
                                    
                                    with open(metadata_path, 'w', encoding='utf-8') as f:
                                        f.write(formatted_text)
                                    
                                    self.stats['metadata_files_created'] += 1
                            except Exception as e:
                                self.logger.log_error(f"Failed to create metadata for {new_filename}: {str(e)}")
                        
                        self.stats['processed_images'] += 1
                        
                        # Update progress
                        if self.progress_callback:
                            self.progress_callback(processed_count, total_files, f"Processing: {new_filename}")
                        
                    except Exception as e:
                        self.logger.log_error(f"Failed to process file {filename}: {str(e)}")
                        self.stats['failed_operations'] += 1
                
            except Exception as e:
                self.logger.log_error(f"Failed to process LoRA group {lora_signature}: {str(e)}")
                self.stats['failed_operations'] += 1
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitize a string for use as a folder name with Windows path length limits"""
        import hashlib
        
        # Replace problematic characters
        name = name.replace(',', '_and_')
        name = name.replace('/', '_')
        name = name.replace('\\', '_')
        name = name.replace(':', '_')
        name = name.replace('*', '_')
        name = name.replace('?', '_')
        name = name.replace('"', '_')
        name = name.replace('<', '_')
        name = name.replace('>', '_')
        name = name.replace('|', '_')
        
        # For Windows compatibility, keep folder names reasonably short
        # Windows has a 260 character path limit total
        max_folder_length = 80  # Conservative limit for folder names
        
        if len(name) > max_folder_length:
            # Create a shorter name with hash for uniqueness
            # Take first part + hash of full name
            hash_obj = hashlib.md5(name.encode('utf-8'))
            hash_suffix = hash_obj.hexdigest()[:8]
            
            # Keep meaningful part at the beginning
            truncated = name[:max_folder_length - 10]  # Leave room for hash
            name = f"{truncated}_{hash_suffix}"
        
        return name
    
    def _get_results(self) -> Dict[str, Any]:
        """Get comprehensive operation results"""
        extractor_stats = self.metadata_extractor.get_statistics()
        
        return {
            'sorter_stats': self.stats,
            'metadata_stats': extractor_stats,
            'session_summary': self.logger.get_summary()
        }
    
    def _log_summary(self, results: Dict[str, Any]):
        """Log comprehensive summary"""
        stats = results['sorter_stats']
        
        self.logger.log_info("=" * 50)
        self.logger.log_info("LORA STACK SORTING COMPLETE")
        self.logger.log_info("=" * 50)
        self.logger.log_info(f"Total Images: {stats['total_images']}")
        self.logger.log_info(f"Processed: {stats['processed_images']}")
        self.logger.log_info(f"Moved: {stats['moved_images']}")
        self.logger.log_info(f"Copied: {stats['copied_images']}")
        self.logger.log_info(f"Metadata Files Created: {stats['metadata_files_created']}")
        self.logger.log_info(f"Renamed Files: {stats['renamed_files']}")
        self.logger.log_info(f"LoRA Groups Created: {stats['lora_groups_created']}")
        self.logger.log_info(f"Images with No LoRAs: {stats['no_lora_count']}")
        self.logger.log_info(f"Failed Operations: {stats['failed_operations']}")
        self.logger.log_info("=" * 50)