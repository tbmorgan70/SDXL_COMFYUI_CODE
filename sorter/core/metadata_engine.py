"""
Sorter 2.3 - Bulletproof Metadata Engine

Handles ComfyUI metadata extraction with robust error handling,
memory optimization, and support for large batches (500+ files).

Key Features:
- Multiple fallback extraction methods
- Memory-efficient batch processing  
- Comprehensive error recovery
- Detailed extraction diagnostics
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import traceback
from PIL import Image

class MetadataExtractor:
    """Bulletproof metadata extraction for ComfyUI images"""
    
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'corrupted_files': 0,
            'no_metadata_files': 0,
            'memory_errors': 0
        }
        self.failed_files = []
        
    def extract_single(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a single image with multiple fallback methods
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary of metadata or None if extraction fails
        """
        try:
            # Method 1: Standard PIL extraction
            with Image.open(image_path) as img:
                # Try 'prompt' field first (ComfyUI standard)
                prompt_data = img.info.get('prompt')
                if prompt_data:
                    metadata = json.loads(prompt_data)
                    self.stats['successful_extractions'] += 1
                    return metadata
                
                # Method 2: Try 'parameters' field (fallback)
                params_data = img.info.get('parameters')
                if params_data:
                    metadata = json.loads(params_data)
                    self.stats['successful_extractions'] += 1
                    return metadata
                
                # Method 3: Try other common metadata fields
                for field in ['workflow', 'extra_pnginfo', 'exif']:
                    data = img.info.get(field)
                    if data:
                        try:
                            if isinstance(data, str):
                                metadata = json.loads(data)
                            else:
                                metadata = data
                            self.stats['successful_extractions'] += 1
                            return metadata
                        except (json.JSONDecodeError, TypeError):
                            continue
                
                # No metadata found
                self.stats['no_metadata_files'] += 1
                return None
                
        except (OSError, IOError) as e:
            # File corruption or access issues
            self.stats['corrupted_files'] += 1
            self.failed_files.append((image_path, f"File access error: {str(e)}"))
            return None
            
        except MemoryError as e:
            # Memory issues with large files
            self.stats['memory_errors'] += 1 
            self.failed_files.append((image_path, f"Memory error: {str(e)}"))
            return None
            
        except Exception as e:
            # Unexpected errors
            self.stats['failed_extractions'] += 1
            self.failed_files.append((image_path, f"Unexpected error: {str(e)}"))
            return None
    
    def extract_batch(self, image_paths: List[str], progress_callback=None) -> Dict[str, Optional[Dict]]:
        """
        Extract metadata from multiple images with progress tracking
        
        Args:
            image_paths: List of image file paths
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary mapping file paths to metadata (or None if failed)
        """
        results = {}
        total_files = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            self.stats['total_processed'] += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total_files, os.path.basename(image_path))
            
            # Extract metadata
            metadata = self.extract_single(image_path)
            results[image_path] = metadata
            
            # Memory management for large batches
            if i > 0 and i % 100 == 0:
                # Force garbage collection every 100 files
                import gc
                gc.collect()
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed extraction statistics"""
        success_rate = 0
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_extractions'] / self.stats['total_processed']) * 100
            
        return {
            **self.stats,
            'success_rate_percent': round(success_rate, 2),
            'failed_files': self.failed_files
        }
    
    def reset_statistics(self):
        """Reset all statistics and failed files list"""
        self.stats = {key: 0 for key in self.stats}
        self.failed_files = []


class MetadataAnalyzer:
    """Analyzes extracted metadata to find key fields for sorting"""
    
    @staticmethod
    def extract_checkpoints(metadata: Dict[str, Any]) -> List[str]:
        """Extract all checkpoint/model names from metadata"""
        checkpoints = []
        if not metadata:
            return checkpoints
            
        for entry in metadata.values():
            inputs = entry.get('inputs', {})
            
            # Primary checkpoint field
            if 'ckpt_name' in inputs:
                checkpoints.append(inputs['ckpt_name'])
            
            # Alternative model fields
            for field in ['model_name', 'checkpoint', 'base_model']:
                if field in inputs:
                    checkpoints.append(inputs[field])
        
        return list(set(checkpoints))  # Remove duplicates
    
    @staticmethod
    def extract_loras(metadata: Dict[str, Any]) -> List[str]:
        """Extract all LoRA names from metadata"""
        loras = []
        if not metadata:
            return loras
            
        for entry in metadata.values():
            inputs = entry.get('inputs', {})
            
            # Standard LoRA field
            if 'lora_name' in inputs:
                loras.append(inputs['lora_name'])
        
        return list(set(loras))  # Remove duplicates
    
    @staticmethod
    def extract_primary_checkpoint(metadata: Dict[str, Any], image_filename: Optional[str] = None) -> Optional[str]:
        """
        Extract the primary/base checkpoint (not refiner) for sorting
        
        This is your #1 priority feature - base checkpoint sorting
        Now with filename fallback support for model name extraction
        """
        if not metadata:
            return None
        
        # First try to extract model from filename if available (ComfyUI naming pattern)
        filename_model = None
        if image_filename:
            filename_model = MetadataAnalyzer._extract_model_from_filename(image_filename)
        
        # Track checkpoints with priority order
        base_checkpoints = []
        refiner_checkpoints = []
        all_checkpoints = []

        for node_id, entry in metadata.items():
            if not isinstance(entry, dict):
                continue
                
            class_type = entry.get('class_type', '')
            inputs = entry.get('inputs', {})
            node_title = str(node_id).lower()

            # Skip non-checkpoint loading nodes
            if class_type not in ['CheckpointLoaderSimple', 'CheckpointLoader', 'UNETLoader']:
                continue

            # Get checkpoint name
            ckpt_name = None
            if 'ckpt_name' in inputs:
                ckpt_name = inputs['ckpt_name']
            elif 'unet_name' in inputs:
                ckpt_name = inputs['unet_name']
            
            if not ckpt_name:
                continue
                
            # Track all checkpoints
            all_checkpoints.append(ckpt_name)
            
            # Determine if this is explicitly a refiner
            # Be more strict about refiner detection
            is_explicit_refiner = (
                'refiner' in class_type.lower() or
                'refiner' in node_title or
                # Check if this node has explicit refiner-specific parameters
                ('start_at_step' in inputs and 'end_at_step' in inputs) or
                any(key in inputs for key in ['refiner_ckpt', 'refiner_model', 'ascore'])
            )
            
            if is_explicit_refiner:
                refiner_checkpoints.append(ckpt_name)
            else:
                # This is likely the base checkpoint
                base_checkpoints.append(ckpt_name)

        # Priority order:
        # 1. Model name from filename (highest priority)
        # 2. First base checkpoint found from workflow
        # 3. First checkpoint overall from workflow
        
        if filename_model:
            return filename_model
        elif base_checkpoints:
            return base_checkpoints[0]
        elif all_checkpoints:
            return all_checkpoints[0]
        
        return None
    
    @staticmethod
    def _extract_model_from_filename(filename: str) -> Optional[str]:
        """
        Extract model name from ComfyUI filename pattern
        
        ComfyUI filenames often contain the model name in patterns like:
        2025-10-15-182703_pieModels_elderberryPie_710452282418503.png
        """
        if not filename:
            return None
            
        # Remove file extension
        base_name = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
        
        # Split by underscores and look for model patterns
        parts = base_name.split('_')
        
        # Look for model name patterns (typically after timestamp)
        # Pattern: YYYY-MM-DD-HHMMSS_modelName_seed or similar
        if len(parts) >= 3:
            # Skip timestamp part (first part), look at subsequent parts
            for i in range(1, len(parts) - 1):  # Exclude last part (usually seed)
                part = parts[i]
                # Look for likely model names (skip common prefixes)
                if part and len(part) > 3 and part not in ['ComfyUI', 'output', 'temp']:
                    # If we find what looks like a model name, combine it with next part if it exists
                    if i + 1 < len(parts) - 1:  # Not the last part
                        next_part = parts[i + 1]
                        # Check if this looks like a model name pattern
                        if any(keyword in (part + next_part).lower() for keyword in ['model', 'mix', 'xl', 'pie', 'diffusion']):
                            return f"{part}_{next_part}"
                    return part
        
        return None
    
    @staticmethod
    def extract_sampling_params(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sampling parameters (CFG, steps, sampler, scheduler)"""
        params = {}
        if not metadata:
            return params
            
        for entry in metadata.values():
            class_type = entry.get('class_type', '')
            inputs = entry.get('inputs', {})
            
            if class_type in ['KSampler', 'KSamplerAdvanced']:
                params.update({
                    'steps': inputs.get('steps'),
                    'cfg': inputs.get('cfg'),
                    'sampler_name': inputs.get('sampler_name'),
                    'scheduler': inputs.get('scheduler'),
                    'denoise': inputs.get('denoise')
                })
                break  # Take first sampler found
        
        return {k: v for k, v in params.items() if v is not None}
    
    @staticmethod
    def extract_prompts(metadata: Dict[str, Any]) -> Dict[str, str]:
        """Extract positive and negative prompts"""
        prompts = {'positive': '', 'negative': ''}
        if not metadata:
            return prompts
            
        for entry in metadata.values():
            class_type = entry.get('class_type', '')
            inputs = entry.get('inputs', {})
            
            if class_type == 'CLIPTextEncode':
                text = inputs.get('text', '')
                if text and not prompts['positive']:
                    prompts['positive'] = text
                elif text and not prompts['negative']:
                    prompts['negative'] = text
        
        return prompts
    
    @staticmethod
    def search_metadata(metadata: Dict[str, Any], search_term: str) -> bool:
        """
        Search for any string in metadata (for your metadata search feature)
        
        Args:
            metadata: The metadata dictionary
            search_term: String to search for (case-insensitive)
            
        Returns:
            True if search term found anywhere in metadata
        """
        if not metadata or not search_term:
            return False
            
        search_term = search_term.lower()
        metadata_str = json.dumps(metadata).lower()
        
        return search_term in metadata_str


# Example usage and testing
if __name__ == "__main__":
    extractor = MetadataExtractor()
    analyzer = MetadataAnalyzer()
    
    # Test with a single file
    test_file = input("Enter path to test PNG file: ").strip().strip('"\'')
    
    if os.path.exists(test_file):
        print(f"🔍 Testing metadata extraction on: {os.path.basename(test_file)}")
        
        metadata = extractor.extract_single(test_file)
        
        if metadata:
            print("✅ Metadata extracted successfully!")
            
            # Analyze the metadata
            checkpoints = analyzer.extract_checkpoints(metadata)
            primary = analyzer.extract_primary_checkpoint(metadata)
            loras = analyzer.extract_loras(metadata)
            sampling = analyzer.extract_sampling_params(metadata)
            prompts = analyzer.extract_prompts(metadata)
            
            print(f"\n📋 Analysis Results:")
            print(f"   Primary checkpoint: {primary}")
            print(f"   All checkpoints: {checkpoints}")
            print(f"   LoRAs: {loras}")
            print(f"   Sampling: {sampling}")
            print(f"   Prompts: {prompts}")
            
        else:
            print("❌ No metadata found")
        
        # Show statistics
        stats = extractor.get_statistics()
        print(f"\n📊 Statistics: {stats}")
    else:
        print("❌ File not found")
