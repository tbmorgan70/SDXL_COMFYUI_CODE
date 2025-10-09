"""
Sorter 2.0 - Metadata Generator

Generate metadata text files for all PNG images without moving or organizing them.
Perfect for users who just want to extract and save ComfyUI metadata information.

Features:
- Extract metadata from all PNG files in a directory
- Generate clean, formatted text files alongside images
- Preserve original file locations
- Detailed progress tracking
- Comprehensive error handling
- Statistics reporting
"""

import os
import sys
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.enhanced_metadata_formatter import EnhancedMetadataFormatter
from core.diagnostics import SortLogger

class MetadataGenerator:
    """Generate metadata text files for images without moving them"""
    
    def __init__(self, logger: Optional[SortLogger] = None):
        self.metadata_extractor = MetadataExtractor()
        self.metadata_analyzer = MetadataAnalyzer()
        self.metadata_formatter = EnhancedMetadataFormatter()
        self.logger = logger or SortLogger()
        
        # Statistics
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'metadata_files_created': 0,
            'failed_extractions': 0,
            'no_metadata_count': 0,
            'already_exists_count': 0,
            'skipped_count': 0
        }
    
    def generate_metadata_files(
        self,
        source_dir: str,
        output_dir: Optional[str] = None,
        overwrite_existing: bool = False,
        include_subdirectories: bool = False,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate metadata text files for all PNG images in the specified directory
        
        Args:
            source_dir: Directory containing PNG images
            output_dir: Directory where metadata files will be saved (if None, saves alongside images)
            overwrite_existing: Whether to overwrite existing .txt files
            include_subdirectories: Whether to process subdirectories recursively
            progress_callback: Optional callback function for progress updates (completed, total, current_file)
            
        Returns:
            Dictionary containing operation results and statistics
        """
        
        # Store parameters
        self.progress_callback = progress_callback
        self.output_dir = output_dir
        
        self.logger.start_operation("Metadata Generation", 0)
        self.logger.log_info(f"Starting metadata generation in: {source_dir}")
        self.logger.log_info(f"Overwrite existing: {overwrite_existing}")
        self.logger.log_info(f"Include subdirectories: {include_subdirectories}")
        
        try:
            # Find all PNG files
            png_files = self._find_png_files(source_dir, include_subdirectories)
            
            if not png_files:
                self.logger.log_info("No PNG files found")
                return self._get_results()
            
            self.stats['total_images'] = len(png_files)
            self.logger.log_info(f"Found {len(png_files)} PNG files to process")
            
            # Send initial progress update
            if self.progress_callback:
                self.progress_callback(0, len(png_files), "Starting processing...")
            
            # Extract metadata from all files
            self.logger.start_operation("Metadata Extraction", len(png_files))
            metadata_results = self._extract_all_metadata(png_files)
            
            # Generate metadata files
            self.logger.start_operation("Creating Metadata Files", len(png_files))
            
            # Ensure main output directory exists if specified
            if self.output_dir:
                os.makedirs(self.output_dir, exist_ok=True)
            
            self._create_all_metadata_files(png_files, metadata_results, overwrite_existing, source_dir)
            
            # Log final summary
            results = self._get_results()
            self._log_summary(results)
            
            return results
            
        except Exception as e:
            self.logger.log_error(f"Critical error during metadata generation: {str(e)}")
            raise
        finally:
            self.logger.end_operation("Metadata Generation")
    
    def _find_png_files(self, source_dir: str, include_subdirectories: bool) -> List[Tuple[str, str]]:
        """Find all PNG files in the directory"""
        png_files = []
        source_path = Path(source_dir)
        
        if include_subdirectories:
            # Recursive search
            for png_file in source_path.rglob("*.png"):
                if png_file.is_file():
                    rel_path = png_file.relative_to(source_path)
                    png_files.append((str(png_file), str(rel_path)))
            
            for png_file in source_path.rglob("*.PNG"):
                if png_file.is_file():
                    rel_path = png_file.relative_to(source_path)
                    png_files.append((str(png_file), str(rel_path)))
        else:
            # Only current directory
            for png_file in source_path.glob("*.png"):
                if png_file.is_file():
                    png_files.append((str(png_file), png_file.name))
            
            for png_file in source_path.glob("*.PNG"):
                if png_file.is_file():
                    png_files.append((str(png_file), png_file.name))
        
        return png_files
    
    def _extract_all_metadata(self, png_files: List[Tuple[str, str]]) -> Dict[str, Optional[Dict]]:
        """Extract metadata from all PNG files with progress tracking"""
        file_paths = [file_path for file_path, _ in png_files]
        
        def progress_callback(completed, total, current_file):
            self.logger.update_progress(completed, total, current_file)
            # Also update GUI progress if callback provided
            if self.progress_callback:
                self.progress_callback(completed, total, current_file)
        
        return self.metadata_extractor.extract_batch(file_paths, progress_callback)
    
    def _create_all_metadata_files(
        self, 
        png_files: List[Tuple[str, str]], 
        metadata_results: Dict[str, Optional[Dict]], 
        overwrite_existing: bool,
        source_dir: str
    ):
        """Create metadata text files for all processed images"""
        
        for i, (file_path, rel_path) in enumerate(png_files, 1):
            try:
                # Calculate output path for metadata file
                if self.output_dir:
                    # Create metadata file in output directory with same relative structure
                    rel_base = os.path.splitext(rel_path)[0]
                    metadata_filename = f"{rel_base}.txt"
                    metadata_path = os.path.join(self.output_dir, metadata_filename)
                    
                    # Ensure output directory exists
                    metadata_dir = os.path.dirname(metadata_path)
                    if metadata_dir:
                        os.makedirs(metadata_dir, exist_ok=True)
                else:
                    # Create alongside original image
                    base_path = os.path.splitext(file_path)[0]
                    metadata_path = f"{base_path}.txt"
                
                if os.path.exists(metadata_path) and not overwrite_existing:
                    self.logger.log_info(f"Skipping existing file: {rel_path}")
                    self.stats['already_exists_count'] += 1
                    self.stats['skipped_count'] += 1
                else:
                    # Get metadata for this file
                    metadata = metadata_results.get(file_path)
                    
                    if metadata:
                        # Create metadata file
                        self._create_metadata_file_at_path(file_path, metadata, metadata_path)
                        self.stats['metadata_files_created'] += 1
                        self.logger.log_info(f"Created metadata: {rel_path}")
                    else:
                        self.logger.log_info(f"No metadata found: {rel_path}")
                        self.stats['no_metadata_count'] += 1
                
                self.stats['processed_images'] += 1
                
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i, len(png_files), f"Creating metadata: {rel_path}")
                
            except Exception as e:
                self.logger.log_error(f"Failed to process {rel_path}: {str(e)}")
                self.stats['failed_extractions'] += 1
            
            # Update progress
            self.logger.update_progress(i, len(png_files), rel_path)
    
    def _create_metadata_file_at_path(self, image_path: str, metadata: Dict, metadata_path: str):
        """Create a clean text metadata file at the specified path"""
        try:
            # Use the enhanced formatter to create clean text
            formatted_text = self.metadata_formatter.format_metadata_to_text(metadata, image_path)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
                
        except Exception as e:
            self.logger.log_error(f"Failed to create metadata file: {str(e)}", metadata_path, "Metadata Write")
            raise
    
    def _get_results(self) -> Dict[str, Any]:
        """Get comprehensive operation results"""
        extractor_stats = self.metadata_extractor.get_statistics()
        
        return {
            'generator_stats': self.stats,
            'metadata_stats': extractor_stats,
            'session_summary': self.logger.get_summary()
        }
    
    def _log_summary(self, results: Dict[str, Any]):
        """Log comprehensive summary"""
        stats = results['generator_stats']
        
        self.logger.log_info("=" * 50)
        self.logger.log_info("METADATA GENERATION COMPLETE")
        self.logger.log_info("=" * 50)
        self.logger.log_info(f"Total Images: {stats['total_images']}")
        self.logger.log_info(f"Processed: {stats['processed_images']}")
        self.logger.log_info(f"Metadata Files Created: {stats['metadata_files_created']}")
        self.logger.log_info(f"Already Existed (Skipped): {stats['already_exists_count']}")
        self.logger.log_info(f"No Metadata Found: {stats['no_metadata_count']}")
        self.logger.log_info(f"Failed Extractions: {stats['failed_extractions']}")
        self.logger.log_info("=" * 50)