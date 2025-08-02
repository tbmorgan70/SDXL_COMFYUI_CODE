"""
Enhanced Batch Rename and Sort - Sorter 2.0 Edition

Combines the working algorithm from the original final_batch_rename_sort.py
with the enhanced metadata formatting from Sorter 2.0.
"""

import os
import shutil
import json
import re
import sys
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.metadata_engine import MetadataExtractor
from core.enhanced_metadata_formatter import EnhancedMetadataFormatter
from core.diagnostics import SortLogger
from PIL import Image
from PIL.PngImagePlugin import PngInfo

class EnhancedBatchSorter:
    """Enhanced sorter using the working algorithm from the original version"""
    
    def __init__(self, logger: Optional[SortLogger] = None):
        self.metadata_extractor = MetadataExtractor()
        self.metadata_formatter = EnhancedMetadataFormatter()
        self.logger = logger or SortLogger()
        
        self.stats = {
            'total_images': 0,
            'renamed_images': 0,
            'sorted_images': 0,
            'metadata_files': 0,
            'folders_created': 0
        }
    
    def enhanced_batch_sort(
        self,
        source_dir: str,
        user_string: str,
        output_dir: Optional[str] = None,
        move_files: bool = False,
        create_metadata_files: bool = True
    ) -> Dict[str, Any]:
        """Complete batch rename and sort workflow following the working algorithm"""
        
        self.logger.start_operation("Enhanced Batch Sort")
        
        # Set output directory
        if not output_dir:
            output_dir = os.path.join(source_dir, "sorted")
        
        # Clean or prepare output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Step 1: Analyze files and create records (without renaming originals)
            file_records = self._analyze_files_for_grouping(source_dir, user_string)
            
            # Step 2: Copy/move and rename files to checkpoint folders with generation subfolders
            self._copy_and_rename_files_by_checkpoint(file_records, output_dir, move_files)
            
            # Step 3: Create metadata files organized by checkpoint
            if create_metadata_files:
                self._create_checkpoint_metadata_files(file_records, output_dir)
            
            # Step 4: Handle other files
            self._handle_other_files(source_dir, output_dir)
            
            return self._get_results()
            
        except Exception as e:
            self.logger.log_error(f"Batch sort failed: {str(e)}", source_dir, "Batch Sort")
            raise
    
    def _analyze_files_for_grouping(self, directory: str, user_string: str) -> List[Dict]:
        """Analyze PNG files and create records with new names WITHOUT renaming originals"""
        
        png_files = [f for f in os.listdir(directory) if f.lower().endswith('.png')]
        self.stats['total_images'] = len(png_files)
        
        if not png_files:
            return []
        
        # Create records with metadata and grouping signatures
        records = []
        for filename in png_files:
            file_path = os.path.join(directory, filename)
            metadata = self.metadata_extractor.extract_single(file_path)
            
            if metadata:
                base_model = self.metadata_formatter.get_base_model(metadata)
                lora_signature = self.metadata_formatter.get_lora_stack_signature(metadata)
                group_signature = self.metadata_formatter.get_grouping_signature(metadata)
            else:
                base_model = 'NO_BASE_MODEL'
                lora_signature = ''
                group_signature = 'None'
            
            # Extract just the base checkpoint name
            if base_model and base_model != 'NO_BASE_MODEL':
                checkpoint_name = os.path.splitext(os.path.basename(base_model))[0]
            else:
                checkpoint_name = 'NO_BASE_MODEL'
            
            records.append({
                'orig_name': filename,
                'file_path': file_path,
                'checkpoint': checkpoint_name,
                'lora_signature': lora_signature,
                'group': group_signature,
                'metadata': metadata,
                'base_model': base_model
            })
        
        # Create GLOBAL generation mapping for unique base model + LoRA combinations
        unique_combinations = sorted(set(record['group'] for record in records))
        global_gen_map = {}
        for i, combo in enumerate(unique_combinations, 1):
            global_gen_map[combo] = i
        
        # Group by checkpoint for folder organization
        checkpoint_groups = {}
        for record in records:
            checkpoint = record['checkpoint']
            if checkpoint not in checkpoint_groups:
                checkpoint_groups[checkpoint] = []
            checkpoint_groups[checkpoint].append(record)
        
        renamed_records = []
        global_idx = 1
        
        # Process each checkpoint group
        for checkpoint, checkpoint_records in checkpoint_groups.items():
            # Sort records within this checkpoint by generation number, then by original name
            sorted_checkpoint_records = sorted(checkpoint_records, 
                                             key=lambda x: (global_gen_map[x['group']], x['orig_name']))
            
            # Create new names for files (but DON'T rename originals)
            for record in sorted_checkpoint_records:
                global_gen = global_gen_map[record['group']]
                new_name = f"[{user_string}] Gen {global_gen:02d} ${global_idx:04d}.png"
                
                # Record the new name without changing the original file
                renamed_records.append({
                    'orig_name': record['orig_name'],
                    'new_name': new_name,
                    'file_path': record['file_path'],  # Still points to original location
                    'gen': global_gen,
                    'checkpoint': checkpoint,
                    'lora_signature': record['lora_signature'],
                    'group': record['group'],
                    'metadata': record['metadata'],
                    'base_model': record['base_model']
                })
                
                global_idx += 1
        
        self.stats['renamed_images'] = len(renamed_records)
        return renamed_records
    
    def _copy_and_rename_files_by_checkpoint(self, file_records: List[Dict], output_dir: str, move_files: bool):
        """Copy/move files to checkpoint folders and rename them there (preserving originals)"""
        
        # Group by checkpoint
        checkpoint_groups = {}
        for record in file_records:
            checkpoint = record['checkpoint']
            if checkpoint not in checkpoint_groups:
                checkpoint_groups[checkpoint] = {}
            
            gen = record['gen']
            if gen not in checkpoint_groups[checkpoint]:
                checkpoint_groups[checkpoint][gen] = []
            
            checkpoint_groups[checkpoint][gen].append(record)
        
        # Create folder structure and copy/move files with new names
        for checkpoint, generations in checkpoint_groups.items():
            # Sanitize checkpoint name for folder
            checkpoint_folder = self._sanitize_name(checkpoint)
            checkpoint_path = os.path.join(output_dir, checkpoint_folder)
            os.makedirs(checkpoint_path, exist_ok=True)
            
            # Create generation subfolders
            for gen, records in generations.items():
                gen_folder = f"Gen {gen:02d}"
                gen_path = os.path.join(checkpoint_path, gen_folder)
                os.makedirs(gen_path, exist_ok=True)
                
                # Copy/move files to generation folder with new names
                for record in records:
                    # Use the new name as the destination filename
                    dest_path = os.path.join(gen_path, record['new_name'])
                    
                    # Handle potential filename conflicts in destination
                    base, ext = os.path.splitext(dest_path)
                    unique_dest_path = dest_path
                    suffix = 1
                    while os.path.exists(unique_dest_path):
                        unique_dest_path = f"{base}_{suffix}{ext}"
                        suffix += 1
                    
                    if move_files:
                        shutil.move(record['file_path'], unique_dest_path)
                        action = "MOVE"
                    else:
                        shutil.copy2(record['file_path'], unique_dest_path)
                        action = "COPY"
                    
                    # Write formatted metadata back to the copied PNG for CivitAI compatibility
                    if record['metadata']:
                        success = self._write_metadata_to_png(unique_dest_path, record['metadata'])
                        if success:
                            self.logger._write_log(f"[METADATA] Updated PNG metadata for {os.path.basename(unique_dest_path)}")
                        else:
                            self.logger._write_log(f"[WARNING] Failed to update PNG metadata for {os.path.basename(unique_dest_path)}")
                    
                    self.logger._write_log(f"[{action}] {record['orig_name']} -> {checkpoint_folder}/Gen {gen:02d}/{os.path.basename(unique_dest_path)}")
                    self.stats['sorted_images'] += 1
    
    def _create_checkpoint_metadata_files(self, file_records: List[Dict], output_dir: str):
        """Create simplified metadata files - one text file per image only"""
        
        # Group by checkpoint
        checkpoint_groups = {}
        for record in file_records:
            checkpoint = record['checkpoint']
            if checkpoint not in checkpoint_groups:
                checkpoint_groups[checkpoint] = {}
            
            gen = record['gen']
            if gen not in checkpoint_groups[checkpoint]:
                checkpoint_groups[checkpoint][gen] = []
            
            checkpoint_groups[checkpoint][gen].append(record)
        
        # Create metadata files for each checkpoint
        for checkpoint, generations in checkpoint_groups.items():
            checkpoint_folder = self._sanitize_name(checkpoint)
            checkpoint_path = os.path.join(output_dir, checkpoint_folder)
            gen_data_dir = os.path.join(checkpoint_path, 'Gen Data')
            os.makedirs(gen_data_dir, exist_ok=True)
            
            # Create only individual metadata files (one per image)
            for gen, records in generations.items():
                for record in records:
                    if record['metadata']:
                        formatted_text = self.metadata_formatter.format_metadata_to_text(
                            record['metadata'], 
                            record['file_path']
                        )
                    else:
                        formatted_text = "No metadata found."
                    
                    # Create individual text file (simplified naming)
                    base_name = os.path.splitext(record['new_name'])[0]
                    txt_path = os.path.join(gen_data_dir, f"{base_name}.txt")
                    
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_text)
                    
                    self.stats['metadata_files'] += 1
    
    def _write_metadata_to_png(self, png_path: str, metadata: Dict[str, Any]) -> bool:
        """Write formatted metadata back to PNG file for CivitAI compatibility"""
        try:
            # Create formatted metadata text
            formatted_metadata = self.metadata_formatter.format_metadata_to_text(metadata, png_path)
            
            # Extract key parameters from metadata for standard PNG fields
            base_model = self.metadata_formatter.get_base_model(metadata) or "Unknown"
            
            # Extract sampling parameters (prioritizing base over refiner)
            steps = None
            cfg = None
            sampler_name = None
            scheduler = None
            seed = None
            
            # Get base model prompt (not refiner prompt)
            positive_prompt_lines = self.metadata_formatter._format_positive_prompt_section(metadata)
            negative_prompt_lines = self.metadata_formatter._format_negative_prompt_section(metadata)
            
            # Extract just the prompt text (skip the header line)
            positive_prompt = None
            if len(positive_prompt_lines) > 1:
                positive_prompt = positive_prompt_lines[1]  # Skip "=== POSITIVE PROMPT ===" header
            
            negative_prompt = None
            if len(negative_prompt_lines) > 1:
                negative_prompt = negative_prompt_lines[1]  # Skip "=== NEGATIVE PROMPT ===" header
            
            # Extract sampling parameters from base model (not refiner)
            for node_id, node_data in metadata.items():
                if not isinstance(node_data, dict):
                    continue
                    
                class_type = node_data.get('class_type', '')
                inputs = node_data.get('inputs', {})
                title = node_data.get('_meta', {}).get('title', '').lower()
                
                # Look for base KSampler (not refiner)
                if 'sampler' in class_type.lower():
                    is_refiner = False
                    
                    if 'refiner' in title:
                        is_refiner = True
                    elif 'start_at_step' in inputs and inputs.get('start_at_step', 0) > 0:
                        is_refiner = True
                    
                    # Only use base sampler parameters
                    if not is_refiner:
                        if 'steps' in inputs and steps is None:
                            steps = inputs['steps']
                        if 'cfg' in inputs and cfg is None:
                            cfg = inputs['cfg']
                        if 'sampler_name' in inputs and sampler_name is None:
                            sampler_name = inputs['sampler_name']
                        if 'scheduler' in inputs and scheduler is None:
                            scheduler = inputs['scheduler']
                        if 'seed' in inputs and seed is None:
                            seed = inputs['seed']
            
            # Open the PNG and prepare new metadata
            with Image.open(png_path) as img:
                # Create new PNG info
                png_info = PngInfo()
                
                # Add CivitAI-compatible parameters
                if positive_prompt:
                    png_info.add_text("parameters", f"{positive_prompt}")
                
                # Add individual fields for better compatibility
                if positive_prompt:
                    png_info.add_text("positive", positive_prompt)
                if negative_prompt:
                    png_info.add_text("negative", negative_prompt)
                if steps is not None:
                    png_info.add_text("Steps", str(steps))
                if cfg is not None:
                    png_info.add_text("CFG scale", str(cfg))
                if sampler_name:
                    png_info.add_text("Sampler", sampler_name)
                if scheduler:
                    png_info.add_text("Scheduler", scheduler)
                if seed is not None:
                    png_info.add_text("Seed", str(seed))
                
                # Add model info
                base_model_name = os.path.splitext(os.path.basename(base_model))[0] if base_model != "Unknown" else "Unknown"
                png_info.add_text("Model", base_model_name)
                
                # Add full formatted metadata as backup
                png_info.add_text("ComfyUI_metadata", formatted_metadata)
                
                # Save with new metadata
                img.save(png_path, pnginfo=png_info)
                
            return True
            
        except Exception as e:
            self.logger.log_error(f"Failed to write metadata to {png_path}: {str(e)}", png_path, "Metadata Write")
            return False
    
    def _extract_checkpoint_name(self, image_path: str) -> str:
        """Extract base checkpoint name from image metadata"""
        metadata = self.metadata_extractor.extract_single(image_path)
        if not metadata:
            return "NO_BASE_MODEL"
        
        base_model = self.metadata_formatter.get_base_model(metadata)
        if base_model:
            return os.path.splitext(os.path.basename(base_model))[0]
        
        return "NO_BASE_MODEL"
    
    def _sanitize_name(self, name: str) -> str:
        """Clean up name for use as folder name"""
        if not name:
            return "NO_BASE_MODEL"
        
        sanitized = ''.join(c for c in name if c.isalnum() or c in '-_.')
        return sanitized or "NO_BASE_MODEL"
    
    def _handle_other_files(self, source_dir: str, output_dir: str):
        """Move non-PNG files to Other Files folder"""
        
        other_files_dir = os.path.join(output_dir, 'Other Files')
        os.makedirs(other_files_dir, exist_ok=True)
        
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            
            if os.path.isfile(file_path) and not filename.lower().endswith('.png'):
                dest_path = os.path.join(other_files_dir, filename)
                shutil.move(file_path, dest_path)
    
    def _get_results(self) -> Dict[str, Any]:
        """Get comprehensive results"""
        return {
            'stats': self.stats,
            'summary': self.logger.get_summary()
        }


# Simple test
if __name__ == "__main__":
    test_dir = input("Enter test directory: ").strip().strip('"\'')
    user_str = input("Enter user string: ").strip()
    
    if os.path.exists(test_dir):
        sorter = EnhancedBatchSorter()
        results = sorter.enhanced_batch_sort(test_dir, user_str)
        print("✅ Test complete!")
        print(f"Stats: {results['stats']}")
    else:
        print("❌ Directory not found")
