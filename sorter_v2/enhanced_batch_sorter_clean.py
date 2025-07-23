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
            # Step 1: Rename files using the new per-checkpoint algorithm
            renamed_records = self._rename_files_with_grouping(source_dir, user_string)
            
            # Step 2: Sort into checkpoint folders with generation subfolders
            self._sort_files_by_checkpoint_and_generation(renamed_records, output_dir, move_files)
            
            # Step 3: Create metadata files organized by checkpoint
            if create_metadata_files:
                self._create_checkpoint_metadata_files(renamed_records, output_dir)
            
            # Step 4: Handle other files
            self._handle_other_files(source_dir, output_dir)
            
            return self._get_results()
            
        except Exception as e:
            self.logger.log_error(f"Batch sort failed: {str(e)}", source_dir, "Batch Sort")
            raise
    
    def _rename_files_with_grouping(self, directory: str, user_string: str) -> List[Dict]:
        """Rename PNG files with generation numbers per checkpoint + LoRA combination"""
        
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
                'metadata': metadata
            })
        
        # Group by checkpoint first
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
            # Get unique LoRA combinations for this checkpoint
            unique_lora_combos = sorted(set(record['lora_signature'] for record in checkpoint_records))
            
            # Create generation mapping per checkpoint
            gen_map = {}
            counter = 1
            for lora_combo in unique_lora_combos:
                gen_map[lora_combo] = counter
                counter += 1
            
            # Sort records within this checkpoint by LoRA combo, then by original name
            sorted_checkpoint_records = sorted(checkpoint_records, 
                                             key=lambda x: (x['lora_signature'], x['orig_name']))
            
            # Rename files within this checkpoint
            for record in sorted_checkpoint_records:
                gen = gen_map[record['lora_signature']]
                new_name = f"[{user_string}] Gen {gen:02d} ${global_idx:04d}.png"
                
                # Handle filename conflicts
                base, ext = os.path.splitext(new_name)
                unique_name = new_name
                suffix = 1
                while os.path.exists(os.path.join(directory, unique_name)):
                    unique_name = f"{base}_{suffix}{ext}"
                    suffix += 1
                
                # Rename the file
                new_path = os.path.join(directory, unique_name)
                os.rename(record['file_path'], new_path)
                
                self.logger._write_log(f"[RENAME] {record['orig_name']} -> {unique_name} (Checkpoint: {checkpoint}, Gen: {gen})")
                
                renamed_records.append({
                    'orig_name': record['orig_name'],
                    'new_name': unique_name,
                    'file_path': new_path,
                    'gen': gen,
                    'checkpoint': checkpoint,
                    'lora_signature': record['lora_signature'],
                    'group': record['group'],
                    'metadata': record['metadata']
                })
                
                global_idx += 1
        
        self.stats['renamed_images'] = len(renamed_records)
        return renamed_records
    
    def _sort_files_by_checkpoint_and_generation(self, renamed_records: List[Dict], output_dir: str, move_files: bool):
        """Sort files into checkpoint folders with generation subfolders"""
        
        # Group by checkpoint
        checkpoint_groups = {}
        for record in renamed_records:
            checkpoint = record['checkpoint']
            if checkpoint not in checkpoint_groups:
                checkpoint_groups[checkpoint] = {}
            
            gen = record['gen']
            if gen not in checkpoint_groups[checkpoint]:
                checkpoint_groups[checkpoint][gen] = []
            
            checkpoint_groups[checkpoint][gen].append(record)
        
        # Create folder structure and move files
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
                
                # Move files to generation folder
                for record in records:
                    dest_path = os.path.join(gen_path, record['new_name'])
                    
                    if move_files:
                        shutil.move(record['file_path'], dest_path)
                        action = "MOVE"
                    else:
                        shutil.copy2(record['file_path'], dest_path)
                        action = "COPY"
                    
                    self.logger._write_log(f"[{action}] {record['new_name']} -> {checkpoint_folder}/Gen {gen:02d}/")
                    self.stats['sorted_images'] += 1
    
    def _create_checkpoint_metadata_files(self, renamed_records: List[Dict], output_dir: str):
        """Create metadata files organized by checkpoint and generation"""
        
        # Group by checkpoint
        checkpoint_groups = {}
        for record in renamed_records:
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
            
            # Create individual and bundled metadata files per generation
            all_gen_texts = {}
            
            for gen, records in generations.items():
                gen_texts = []
                
                for record in records:
                    if record['metadata']:
                        formatted_text = self.metadata_formatter.format_metadata_to_text(
                            record['metadata'], 
                            record['file_path']
                        )
                    else:
                        formatted_text = "No metadata found."
                    
                    # Create individual text file
                    base_name = os.path.splitext(record['new_name'])[0]
                    txt_path = os.path.join(gen_data_dir, f"{base_name}.txt")
                    
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_text)
                    
                    gen_texts.append(formatted_text)
                    self.stats['metadata_files'] += 1
                
                # Create generation bundle file
                all_gen_texts[gen] = gen_texts
                gen_file = os.path.join(gen_data_dir, f"GEN {gen:02d} META.txt")
                with open(gen_file, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(gen_texts))
            
            # Create complete bundle for this checkpoint
            bundle_path = os.path.join(gen_data_dir, f'{checkpoint}_ALL_GEN_METADATA_BUNDLE.txt')
            with open(bundle_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {checkpoint} METADATA BUNDLE ===\n\n")
                for gen in sorted(all_gen_texts.keys()):
                    f.write(f"GEN {gen:02d}\n" + '-' * 30 + "\n")
                    f.write("\n\n".join(all_gen_texts[gen]) + "\n\n")
    
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
