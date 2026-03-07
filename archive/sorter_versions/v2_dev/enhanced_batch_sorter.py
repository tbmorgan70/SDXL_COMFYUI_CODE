"""
Enhanced Batch Rename and Sort - Sorter 2.0 Edition

Combines the working algorithm from the original final_batch_rename_sort.py
with the enhanced metadata formatting from Sorter 2.0.

Features:
1. Rename images by Base+LoRA-sorted generation
2. Generate comprehensive metadata files 
3. Sort renamed PNGs into checkpoint folders
4. Maintain compatibility with the working older algorithm
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
        """
        Complete batch rename and sort workflow
        
        Args:
            source_dir: Directory containing PNG images
            user_string: Prefix for renaming (e.g., "nova_skyrift")
            output_dir: Output directory (default: source_dir/sorted)
            move_files: True to move files, False to copy
            create_metadata_files: Create enhanced metadata text files
        """
        
        self.logger.start_operation("Enhanced Batch Sort")
        self.logger._write_log(f"Source: {source_dir}")
        self.logger._write_log(f"User string: {user_string}")
        
        # Set output directory
        if not output_dir:
            output_dir = os.path.join(source_dir, "sorted")
        
        # Clean or prepare output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Step 1: Rename files using the working algorithm
            self.logger.start_operation("File Renaming")
            renamed_records = self._rename_files_with_grouping(source_dir, user_string)
            self.stats['renamed_images'] = len(renamed_records)
            self.logger.complete_operation()
            
            # Step 2: Create metadata files
            if create_metadata_files:
                self.logger.start_operation("Metadata Generation")
                gen_data_dir = os.path.join(output_dir, 'Gen Data')
                self._create_gen_metadata_files(source_dir, renamed_records, gen_data_dir)
                self.logger.complete_operation()
            
            # Step 3: Sort PNGs into checkpoint folders
            self.logger.start_operation("File Sorting")
            self._sort_by_checkpoint_folders(source_dir, output_dir, move_files)
            self.logger.complete_operation()
            
            # Step 4: Handle other files
            self.logger.start_operation("Other Files")
            self._move_other_files(source_dir, output_dir)
            self.logger.complete_operation()
            
            results = self._get_results()
            self._log_summary(results)
            
            return results
            
        except Exception as e:
            self.logger.log_error(f"Batch sort failed: {str(e)}", source_dir, "Batch Sort")
            raise
    
    def _rename_files_with_grouping(self, directory: str, user_string: str) -> List[Dict]:
        """Rename PNG files using the working grouping algorithm"""
        
        # Find all PNG files
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
                group_signature = self.metadata_formatter.get_grouping_signature(metadata)
            else:
                group_signature = 'None'
            
            records.append({
                'orig_name': filename,
                'file_path': file_path,
                'group': group_signature,
                'metadata': metadata
            })
        
        # Version key function from working version
        def version_key(group_name):
            match = re.search(r"(\d+\.\d+)", group_name)
            return float(match.group(1)) if match else float('inf')
        
        # Get unique groups and sort them properly
        unique_groups = sorted(set(record['group'] for record in records), 
                             key=lambda g: (version_key(g), g))
        
        # Create generation mapping
        gen_map = {}
        counter = 1
        for group in unique_groups:
            if group == 'None':
                gen_map[group] = 0
            else:
                gen_map[group] = counter
                counter += 1
        
        # Rename files with proper generation numbers
        renamed_records = []
        idx = 1
        
        # Sort records by group version, then by original name
        sorted_records = sorted(records, key=lambda x: (version_key(x['group']), x['orig_name']))
        
        for record in sorted_records:
            gen = gen_map[record['group']]
            new_name = f"[{user_string}] Gen {gen:02d} ${idx:04d}.png"
            
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
            
            self.logger._write_log(f"[RENAME] {record['orig_name']} -> {unique_name}")
            
            renamed_records.append({
                'orig_name': record['orig_name'],
                'new_name': unique_name,
                'file_path': new_path,
                'gen': gen,
                'group': record['group'],
                'metadata': record['metadata']
            })
            
            idx += 1
        
        return renamed_records
    
    def _create_gen_metadata_files(self, source_dir: str, renamed_records: List[Dict], gen_data_dir: str):
        """Create enhanced metadata files using the new formatter"""
        
        os.makedirs(gen_data_dir, exist_ok=True)
        
        # Group by generation for bundling
        by_gen = {}
        
        for record in renamed_records:
            if record['metadata']:
                # Format using enhanced formatter
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
            
            self.logger._write_log(f"[TXT] {base_name}.txt")
            self.stats['metadata_files'] += 1
            
            # Add to generation bundle
            gen = record['gen']
            by_gen.setdefault(gen, []).append(formatted_text)
        
        # Create generation bundle files
        for gen, texts in by_gen.items():
            gen_file = os.path.join(gen_data_dir, f"GEN {gen:02d} META.txt")
            with open(gen_file, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(texts))
            
            self.logger._write_log(f"[GEN] GEN {gen:02d} META.txt")
        
        # Create complete bundle
        bundle_path = os.path.join(gen_data_dir, 'ALL_GEN_METADATA_BUNDLE.txt')
        with open(bundle_path, 'w', encoding='utf-8') as f:
            for gen in sorted(by_gen.keys()):
                f.write(f"GEN {gen:02d}\n" + '-' * 30 + "\n")
                f.write("\n\n".join(by_gen[gen]) + "\n\n")
        
        self.logger._write_log(f"[BUNDLE] ALL_GEN_METADATA_BUNDLE.txt")
    
    def _sort_by_checkpoint_folders(self, source_dir: str, output_dir: str, move_files: bool):
        \"\"\"Sort PNG files into checkpoint-based folders\"\"\"
        
        for filename in os.listdir(source_dir):
            if not filename.lower().endswith('.png'):
                continue
            
            file_path = os.path.join(source_dir, filename)
            
            # Extract base checkpoint
            base_checkpoint = self._get_base_checkpoint_name(file_path)
            folder_name = self._sanitize_folder_name(base_checkpoint)
            
            # Create destination folder
            dest_folder = os.path.join(output_dir, folder_name)
            os.makedirs(dest_folder, exist_ok=True)
            
            # Move or copy file
            dest_path = os.path.join(dest_folder, filename)
            if move_files:
                shutil.move(file_path, dest_path)
                action = \"MOVE\"
            else:
                shutil.copy2(file_path, dest_path)
                action = \"COPY\"
            
            self.logger._write_log(f\"[{action}] {filename} -> {folder_name}\")
            self.stats['sorted_images'] += 1
    
    def _get_base_checkpoint_name(self, image_path: str) -> str:
        \"\"\"Extract base checkpoint name from image metadata\"\"\"
        metadata = self.metadata_extractor.extract_single(image_path)
        if not metadata:
            return \"NO_BASE_MODEL\"
        
        base_model = self.metadata_formatter.get_base_model(metadata)
        if base_model:
            # Extract just the filename without path and extension
            return os.path.splitext(os.path.basename(base_model))[0]
        
        return \"NO_BASE_MODEL\"
    
    def _sanitize_folder_name(self, name: str) -> str:
        \"\"\"Clean up name for use as folder name\"\"\"
        if not name:
            return \"NO_BASE_MODEL\"
        
        # Remove problematic characters
        sanitized = ''.join(c for c in name if c.isalnum() or c in '-_.')
        return sanitized or \"NO_BASE_MODEL\"
    
    def _move_other_files(self, source_dir: str, output_dir: str):
        \"\"\"Move non-PNG files to Other Files folder\"\"\"
        
        other_files_dir = os.path.join(output_dir, 'Other Files')
        os.makedirs(other_files_dir, exist_ok=True)
        
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            
            # Skip PNG files and directories
            if os.path.isfile(file_path) and not filename.lower().endswith('.png'):
                dest_path = os.path.join(other_files_dir, filename)
                shutil.move(file_path, dest_path)
                self.logger._write_log(f\"[OTHER] {filename} -> Other Files\")
    
    def _get_results(self) -> Dict[str, any]:
        \"\"\"Get comprehensive results\"\"\"
        return {
            'stats': self.stats,
            'summary': self.logger.get_summary()
        }
    
    def _log_summary(self, results: Dict[str, any]):
        \"\"\"Log comprehensive summary\"\"\"
        stats = results['stats']
        
        self.logger._write_log(\"\\n=== ENHANCED BATCH SORT SUMMARY ===\")
        self.logger._write_log(f\"Total images: {stats['total_images']}\")
        self.logger._write_log(f\"Renamed: {stats['renamed_images']}\")
        self.logger._write_log(f\"Sorted: {stats['sorted_images']}\")
        self.logger._write_log(f\"Metadata files: {stats['metadata_files']}\")
        
        success_rate = (stats['sorted_images'] / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
        self.logger._write_log(f\"Success rate: {success_rate:.1f}%\")


# Example usage
if __name__ == \"__main__\":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Batch Rename and Sort - Sorter 2.0')
    parser.add_argument('directory', help='Directory containing PNG images')
    parser.add_argument('user_string', help='Prefix for renaming (e.g., \"nova_skyrift\")')
    parser.add_argument('--output', help='Output directory (default: directory/sorted)')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying')
    parser.add_argument('--no-metadata', action='store_true', help='Skip metadata file creation')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f\"❌ Directory not found: {args.directory}\")
        sys.exit(1)
    
    # Count PNG files
    png_count = len([f for f in os.listdir(args.directory) if f.lower().endswith('.png')])
    if png_count == 0:
        print(\"❌ No PNG files found in directory\")
        sys.exit(1)
    
    print(f\"🚀 Enhanced Batch Sort - Sorter 2.0\")
    print(f\"Directory: {args.directory}\")
    print(f\"User string: {args.user_string}\")
    print(f\"PNG files: {png_count}\")
    print(f\"Operation: {'MOVE' if args.move else 'COPY'}\")
    print(f\"Metadata: {'No' if args.no_metadata else 'Yes'}\")
    
    confirm = input(\"\\nProceed? (y/n): \").lower()
    if confirm != 'y':
        print(\"❌ Operation cancelled\")
        sys.exit(0)
    
    try:
        sorter = EnhancedBatchSorter()
        
        results = sorter.enhanced_batch_sort(
            source_dir=args.directory,
            user_string=args.user_string,
            output_dir=args.output,
            move_files=args.move,
            create_metadata_files=not args.no_metadata
        )
        
        print(f\"\\n✅ Enhanced batch sort complete!\")
        if args.output:
            print(f\"Check results in: {args.output}\")
        else:
            print(f\"Check results in: {os.path.join(args.directory, 'sorted')}\")
        
    except Exception as e:
        print(f\"❌ Error: {e}\")
        sys.exit(1)
