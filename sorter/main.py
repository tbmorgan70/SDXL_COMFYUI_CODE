"""
Sorter 2.0 - Main Interface

Simple, rob            print("1. 🎯 Sort by Base Checkpoint (Most Used)")
            print("2. 🔍 Search & Sort by Metadata")
            print("3. 🌈 Sort by Color")
            print("4. 📂 Flatten Image Folders")
            print("5. 🧹 Cleanup Filenames & Remove Metadata")
            print("6. 📝 Generate Enhanced Metadata Reports")
            print("7. 🧪 Test Metadata Extraction")
            print("8. 📊 View Previous Session Logs")mand-line interface for all sorting operations.
Built for reliability with large batches and comprehensive error handling.

Features:
- Base checkpoint sorting (your #1 priority)
- Metadata search and filtering  
- Color sorting (from existing sorter)
- Flatten images (from existing sorter)
- Comprehensive logging and diagnostics
- Progress tracking for large batches
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.diagnostics import SortLogger
from sorters.checkpoint_sorter import CheckpointSorter
from sorters.metadata_search import MetadataSearchSorter
from sorters.color_sorter import ColorSorter
from sorters.image_flattener import ImageFlattener
from sorters.image_extractor import ImageExtractorSorter, CROP_PRESETS, SUPPORTED_EXTENSIONS

class SorterV2:
    """Main interface for Sorter 2.0"""
    
    def __init__(self):
        self.logger = SortLogger()
        print("🚀 Sorter 3.0.0 - Advanced ComfyUI Image Organizer")
        print("=" * 60)
    
    def main_menu(self):
        """Display main menu and handle user choices"""
        while True:
            print("\n📋 SORTING OPTIONS:")
            print("1. 🎯 Sort by Base Checkpoint (Most Used)")
            print("2. 🔍 Search & Sort by Metadata")
            print("3. 🌈 Sort by Color")
            print("4. 📂 Flatten Image Folders")
            print("5. 📦 Extract Images from Files (PDF/EPUB/CBZ…)")
            print("6. 📊 View Previous Session Logs")
            print("0. ❌ Exit")

            choice = input("\nChoose option (0-6): ").strip()

            if choice == "1":
                self.sort_by_checkpoint()
            elif choice == "2":
                self.search_and_sort()
            elif choice == "3":
                self.sort_by_color()
            elif choice == "4":
                self.flatten_images()
            elif choice == "5":
                self.extract_images()
            elif choice == "6":
                self.view_session_logs()
            elif choice == "0":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
    
    def sort_by_checkpoint(self):
        """Sort images by base checkpoint - your #1 priority feature"""
        print("\n🎯 SORT BY BASE CHECKPOINT")
        print("-" * 40)
        
        # Get user inputs
        source_dir = self._get_directory_input("Enter source directory")
        if not source_dir:
            return
        
        # Count PNG files
        png_count = len([f for f in os.listdir(source_dir) if f.lower().endswith('.png')])
        if png_count == 0:
            print("❌ No PNG files found in source directory")
            return
        
        print(f"📊 Found {png_count} PNG files to sort")
        
        # Get output directory
        output_dir = input("Enter output directory (or press Enter for 'sorted'): ").strip().strip('"\'')
        if not output_dir:
            output_dir = os.path.join(source_dir, "sorted")
        
        # Operation type
        move_files = input("Move files? (y/n, default=n): ").lower() == 'y'
        operation = "MOVE" if move_files else "COPY"
        
        # Create metadata files
        create_metadata = input("Create metadata files? (y/n, default=y): ").lower() != 'n'
        
        # Renaming options
        rename_files = input("Rename files with sequential numbering? (y/n, default=n): ").lower() == 'y'
        user_prefix = ""
        if rename_files:
            user_prefix = input("Enter prefix for renamed files (e.g. 'nova_skyrift'): ").strip()
            if not user_prefix:
                print("❌ Prefix is required for renaming")
                rename_files = False
        
        # Advanced grouping options
        print("\n🎯 GROUPING OPTIONS:")
        print("1. By checkpoint only (default)")
        print("2. By checkpoint + LoRA stack combination")
        
        grouping_choice = input("Choose grouping method (1-2, default=1): ").strip()
        group_by_lora_stack = grouping_choice == "2"
        
        if group_by_lora_stack:
            print("📝 Note: Images will be grouped by both checkpoint AND LoRA combinations")
        
        # Confirm before starting
        print(f"\n📋 CONFIRMATION:")
        print(f"   Source: {source_dir}")
        print(f"   Output: {output_dir}")
        print(f"   Files: {png_count} PNG files")
        print(f"   Operation: {operation}")
        print(f"   Metadata files: {'Yes' if create_metadata else 'No'}")
        print(f"   Grouping: {'Checkpoint + LoRA Stack' if group_by_lora_stack else 'Checkpoint Only'}")
        print(f"   Rename files: {'Yes' if rename_files else 'No'}")
        if rename_files and user_prefix:
            print(f"   Naming pattern: {user_prefix}_img1, {user_prefix}_img2, etc.")
        
        confirm = input("\nProceed? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Operation cancelled")
            return
        
        # Start sorting
        try:
            sorter = CheckpointSorter(self.logger)
            
            print(f"\n🚀 Starting checkpoint sorting...")
            results = sorter.sort_by_checkpoint(
                source_dir=source_dir,
                output_dir=output_dir,
                move_files=move_files,
                create_metadata_files=create_metadata,
                rename_files=rename_files,
                user_prefix=user_prefix,
                group_by_lora_stack=group_by_lora_stack
            )
            
            # Show results
            stats = results['sorter_stats']
            print(f"\n✅ SORTING COMPLETE!")
            print(f"   Sorted: {stats['sorted_images']}/{stats['total_images']} images")
            print(f"   Folders created: {stats['folders_created']}")
            print(f"   Unknown checkpoints: {stats['unknown_checkpoint']}")
            
            # Offer to open output folder
            if input("\nOpen output folder? (y/n): ").lower() == 'y':
                os.startfile(output_dir)
                
        except Exception as e:
            print(f"❌ Error during sorting: {e}")
            self.logger.log_error(f"Checkpoint sorting failed: {str(e)}", source_dir, "Sorting Error")
    
    def search_and_sort(self):
        """Search and sort by metadata content"""
        print("\n🔍 SEARCH & SORT BY METADATA")
        print("-" * 40)
        
        # Get user inputs
        source_dir = self._get_directory_input("Enter source directory")
        if not source_dir:
            return
        
        print("\n🎯 SEARCH OPTIONS:")
        print("1. Search for specific LoRA")
        print("2. Search for prompt keywords")
        print("3. Custom metadata search")
        
        search_type = input("Choose search type (1-3): ").strip()
        
        if search_type == "1":
            self._search_for_lora(source_dir)
        elif search_type == "2":
            self._search_for_keywords(source_dir)
        elif search_type == "3":
            self._custom_search(source_dir)
        else:
            print("❌ Invalid choice")
    
    def _search_for_lora(self, source_dir: str):
        """Search for specific LoRA"""
        lora_name = input("Enter LoRA name to search for (e.g., 'Nova_Skyrift'): ").strip()
        if not lora_name:
            print("❌ LoRA name required")
            return
        
        output_dir = input("Enter output directory (or press Enter for auto): ").strip().strip('"\'')
        if not output_dir:
            clean_lora = lora_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            output_dir = os.path.join(source_dir, f"lora_{clean_lora}")
        
        move_files = input("Move files? (y/n, default=n): ").lower() == 'y'
        
        # Confirm and execute
        png_count = len([f for f in os.listdir(source_dir) if f.lower().endswith('.png')])
        print(f"\n📋 Searching {png_count} PNG files for LoRA: {lora_name}")
        
        if input("Proceed? (y/n): ").lower() == 'y':
            try:
                sorter = MetadataSearchSorter(self.logger)
                results = sorter.search_specific_lora(source_dir, output_dir, lora_name, move_files)
                
                stats = results['search_stats']
                print(f"\n✅ Search complete!")
                print(f"   Found: {stats['images_matched']} matching images")
                print(f"   Sorted: {stats['images_sorted']} images")
                
                if input("Open output folder? (y/n): ").lower() == 'y':
                    os.startfile(output_dir)
                    
            except Exception as e:
                print(f"❌ Search failed: {e}")
    
    def _search_for_keywords(self, source_dir: str):
        """Search for prompt keywords"""
        keywords_input = input("Enter keywords to search for (separated by commas): ").strip()
        if not keywords_input:
            print("❌ Keywords required")
            return
        
        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        
        output_dir = input("Enter output directory (or press Enter for auto): ").strip().strip('"\'')
        if not output_dir:
            output_dir = os.path.join(source_dir, "keyword_search")
        
        move_files = input("Move files? (y/n, default=n): ").lower() == 'y'
        require_all = input("Require ALL keywords? (y/n, default=n): ").lower() == 'y'
        
        # Confirm and execute
        png_count = len([f for f in os.listdir(source_dir) if f.lower().endswith('.png')])
        logic = "AND" if require_all else "OR"
        print(f"\n📋 Searching {png_count} PNG files for keywords: {keywords} ({logic} logic)")
        
        if input("Proceed? (y/n): ").lower() == 'y':
            try:
                sorter = MetadataSearchSorter(self.logger)
                results = sorter.search_by_prompt_keywords(source_dir, output_dir, keywords, move_files, require_all)
                
                stats = results['search_stats']
                print(f"\n✅ Search complete!")
                print(f"   Found: {stats['images_matched']} matching images")
                print(f"   Sorted: {stats['images_sorted']} images")
                
                if input("Open output folder? (y/n): ").lower() == 'y':
                    os.startfile(output_dir)
                    
            except Exception as e:
                print(f"❌ Search failed: {e}")
    
    def _custom_search(self, source_dir: str):
        """Custom metadata search"""
        search_terms_input = input("Enter search terms (separated by commas): ").strip()
        if not search_terms_input:
            print("❌ Search terms required")
            return
        
        search_terms = [t.strip() for t in search_terms_input.split(',') if t.strip()]
        
        print("\nSearch mode:")
        print("1. ANY term matches (OR logic)")
        print("2. ALL terms must match (AND logic)")
        print("3. Exact match")
        
        mode_choice = input("Choose mode (1-3, default=1): ").strip() or "1"
        search_modes = {"1": "any", "2": "all", "3": "exact"}
        search_mode = search_modes.get(mode_choice, "any")
        
        output_dir = input("Enter output directory (or press Enter for auto): ").strip().strip('"\'')
        if not output_dir:
            output_dir = os.path.join(source_dir, "custom_search")
        
        move_files = input("Move files? (y/n, default=n): ").lower() == 'y'
        case_sensitive = input("Case sensitive search? (y/n, default=n): ").lower() == 'y'
        
        # Confirm and execute
        png_count = len([f for f in os.listdir(source_dir) if f.lower().endswith('.png')])
        print(f"\n📋 Custom search configuration:")
        print(f"   Files: {png_count} PNG files")
        print(f"   Terms: {search_terms}")
        print(f"   Mode: {search_mode.upper()}")
        print(f"   Case sensitive: {case_sensitive}")
        
        if input("Proceed? (y/n): ").lower() == 'y':
            try:
                sorter = MetadataSearchSorter(self.logger)
                results = sorter.search_and_sort(
                    source_dir=source_dir,
                    output_dir=output_dir,
                    search_terms=search_terms,
                    search_mode=search_mode,
                    move_files=move_files,
                    case_sensitive=case_sensitive
                )
                
                stats = results['search_stats']
                print(f"\n✅ Search complete!")
                print(f"   Found: {stats['images_matched']} matching images")
                print(f"   Sorted: {stats['images_sorted']} images")
                
                if input("Open output folder? (y/n): ").lower() == 'y':
                    os.startfile(output_dir)
                    
            except Exception as e:
                print(f"❌ Search failed: {e}")
    
    def sort_by_color(self):
        """Sort images by dominant color"""
        print("\n🌈 SORT BY COLOR")
        print("-" * 40)
        
        source_dir = self._get_directory_input("Enter source directory")
        if not source_dir:
            return
        
        # Count images first
        from pathlib import Path
        source_path = Path(source_dir)
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_path.glob(f'*{ext}'))
            image_files.extend(source_path.glob(f'*{ext.upper()}'))
        
        print(f"📊 Found {len(image_files)} image files to sort")
        
        if len(image_files) == 0:
            print("❌ No image files found")
            return
        
        output_dir = input("Enter output directory (or press Enter for 'color_sorted'): ").strip().strip('"\'')
        if not output_dir:
            output_dir = os.path.join(source_dir, "color_sorted")
        
        move_files = input("Move files? (y/n, default=n): ").strip().lower() == 'y'
        create_metadata = input("Create metadata files? (y/n, default=y): ").strip().lower() != 'n'
        
        # Renaming options
        rename_files = input("Rename files with sequential numbering? (y/n, default=n): ").strip().lower() == 'y'
        user_prefix = ""
        if rename_files:
            user_prefix = input("Enter filename prefix (optional, e.g. 'myproject'): ").strip()
        
        # Color tuning (press Enter to accept defaults)
        print("\n🎛️  COLOR TUNING (press Enter for defaults):")

        def _pct_input(prompt, default):
            raw = input(f"{prompt} (0-100, default={default:.0f}): ").strip()
            try:
                return max(0.0, min(1.0, float(raw) / 100.0)) if raw else default / 100.0
            except ValueError:
                return default / 100.0

        black_level = _pct_input("Black level — darker than this = black", 12)
        white_level = _pct_input("White level — brighter (and colorless) = white", 90)
        gray_sat = _pct_input("Color purity — below this saturation = gray", 15)
        neutral_dominance = _pct_input("Neutral dominance — % neutral needed to beat top color", 75)
        
        # Confirmation
        print(f"\n📋 CONFIRMATION:")
        print(f"   Source: {source_dir}")
        print(f"   Output: {output_dir}")
        print(f"   Files: {len(image_files)} image files")
        print(f"   Operation: {'MOVE' if move_files else 'COPY'}")
        print(f"   Metadata files: {'Yes' if create_metadata else 'No'}")
        print(f"   Rename files: {'Yes' if rename_files else 'No'}")
        if rename_files:
            if user_prefix:
                print(f"   Prefix: '{user_prefix}' (e.g. {user_prefix}_red_img1.png)")
            else:
                print(f"   Naming: color_img# format (e.g. red_img1.png)")
        print(f"   Tuning: Black {black_level:.0%} / White {white_level:.0%} / Purity {gray_sat:.0%} / Neutral dom. {neutral_dominance:.0%}")
        
        if input("\nProceed? (y/n): ").strip().lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        # Execute color sorting
        print("🚀 Starting color sorting...")
        
        color_sorter = ColorSorter(self.logger)
        success = color_sorter.sort_by_color(
            source_dir=source_dir,
            output_dir=output_dir,
            move_files=move_files,
            create_metadata=create_metadata,
            black_level=black_level,
            white_level=white_level,
            gray_sat=gray_sat,
            neutral_dominance=neutral_dominance,
            rename_files=rename_files,
            user_prefix=user_prefix
        )
        
        if success:
            print("✅ COLOR SORTING COMPLETE!")
            if input("\nOpen output folder? (y/n): ").strip().lower() == 'y':
                import subprocess
                subprocess.run(['explorer', os.path.abspath(output_dir)], shell=True)
        else:
            print("❌ Color sorting failed")
    
    def flatten_images(self):
        """Flatten nested image folders into a single directory"""
        print("\n📂 FLATTEN IMAGE FOLDERS")
        print("-" * 40)
        
        source_dir = self._get_directory_input("Enter source directory with nested folders")
        if not source_dir:
            return
        
        # Preview first
        flattener = ImageFlattener(self.logger)
        preview_data = flattener.preview_flatten(source_dir)
        
        if preview_data['total_images'] == 0:
            print("❌ No image files found in directory or subdirectories")
            return
        
        print(f"\n🤔 Continue with flattening?")
        target_dir = input("Enter target directory (or press Enter for 'flattened'): ").strip().strip('"\'')
        if not target_dir:
            target_dir = os.path.join(source_dir, "flattened")
        
        move_files = input("Move files? (y/n, default=n): ").strip().lower() == 'y'
        remove_empty = input("Remove empty directories? (y/n, default=y): ").strip().lower() != 'n'
        
        # Confirmation
        print(f"\n📋 CONFIRMATION:")
        print(f"   Source: {source_dir}")
        print(f"   Target: {target_dir}")
        print(f"   Images: {preview_data['total_images']} files")
        print(f"   Folders: {preview_data['folders']} folders")
        print(f"   Operation: {'MOVE' if move_files else 'COPY'}")
        print(f"   Remove empty dirs: {'Yes' if remove_empty else 'No'}")
        print(f"   Duplicates to rename: {preview_data['duplicates']}")
        
        if input("\nProceed? (y/n): ").strip().lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        # Execute flattening
        print("🚀 Starting image flattening...")
        
        success = flattener.flatten_images(
            source_dir=source_dir,
            target_dir=target_dir,
            move_files=move_files,
            remove_empty_dirs=remove_empty
        )
        
        if success:
            print("✅ IMAGE FLATTENING COMPLETE!")
            if input("\nOpen target folder? (y/n): ").strip().lower() == 'y':
                import subprocess
                subprocess.run(['explorer', os.path.abspath(target_dir)], shell=True)
        else:
            print("❌ Image flattening failed")
    
    def extract_images(self):
        """Extract images from PDF/EPUB/MOBI/CBZ/CBR files with optional crop."""
        print("\n📦 EXTRACT IMAGES FROM FILES")
        print("-" * 40)
        print(f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

        # --- Input: file(s) or directory ---
        print("\nInput options:")
        print("  1. Single file")
        print("  2. Directory (all supported files inside)")
        input_choice = input("Choose (1-2, default=1): ").strip() or "1"

        input_paths = []
        if input_choice == "2":
            src = self._get_directory_input("Enter source directory")
            if not src:
                return
            input_paths = [src]
        else:
            filepath = input("Enter file path: ").strip().strip('"\'')
            if not filepath or not os.path.isfile(filepath):
                print("❌ File not found")
                return
            input_paths = [filepath]

        # --- Output directory ---
        output_dir = input("Enter output directory (or press Enter for 'extracted_images'): ").strip().strip('"\'')
        if not output_dir:
            output_dir = "extracted_images"

        folder_prefix = input("Folder prefix for subfolders (optional): ").strip()

        # --- Minimum dimensions ---
        try:
            min_w = int(input("Minimum width  (default 512): ").strip() or 512)
            min_h = int(input("Minimum height (default 512): ").strip() or 512)
        except ValueError:
            min_w = min_h = 512

        # --- Crop preset ---
        preset_keys = list(CROP_PRESETS.keys())
        print("\n📐 CROP SIZE PRESETS:")
        for i, key in enumerate(preset_keys):
            print(f"  {i:2d}. {key}")
        try:
            preset_idx = int(input(f"Choose preset (0-{len(preset_keys)-1}, default=0 None): ").strip() or 0)
            preset_idx = max(0, min(preset_idx, len(preset_keys) - 1))
        except ValueError:
            preset_idx = 0

        preset_label = preset_keys[preset_idx]
        crop_size = CROP_PRESETS[preset_label]

        if crop_size == "custom":
            try:
                cw = int(input("  Custom width  (px): ").strip())
                ch = int(input("  Custom height (px): ").strip())
                crop_size = (cw, ch)
            except ValueError:
                print("  Invalid dimensions — no crop applied")
                crop_size = None

        # --- Crop mode ---
        crop_mode = "none"
        if crop_size:
            print("\n✂️  CROP MODE:")
            print("  1. Center fill (default)")
            print("  2. Face-centered (requires mediapipe; falls back to center)")
            mode_choice = input("Choose (1-2, default=1): ").strip() or "1"
            crop_mode = "face" if mode_choice == "2" else "center"

        # --- Confirm ---
        print(f"\n📋 CONFIRMATION:")
        print(f"   Input:      {input_paths}")
        print(f"   Output:     {output_dir}")
        print(f"   Min size:   {min_w}×{min_h}")
        print(f"   Crop:       {preset_label}  mode={crop_mode}")

        if input("\nProceed? (y/n): ").strip().lower() != 'y':
            print("❌ Cancelled")
            return

        # --- Run extraction ---
        try:
            extractor = ImageExtractorSorter(
                logger=self.logger,
                min_width=min_w,
                min_height=min_h,
                output_dir=output_dir,
                folder_prefix=folder_prefix,
                crop_size=crop_size,
                crop_mode=crop_mode,
            )
            results = extractor.process_paths(input_paths)

            print(f"\n✅ EXTRACTION COMPLETE!")
            print(f"   Files processed:  {results['total_files']}")
            print(f"   Images extracted: {results['total_extracted']}")
            print(f"   Output:           {results['output_dir']}")

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            self.logger.log_error(f"Image extraction failed: {e}", str(input_paths), "Extraction Error")
            return

        # --- Optional chain to sort ---
        if results['total_extracted'] == 0:
            return

        print("\n🔗 CHAIN TO SORTING (optional)")
        print("   Sort the extracted images now?")
        print("   1. Sort by Checkpoint")
        print("   2. Sort by Color")
        print("   3. Flatten into single folder")
        print("   0. No — done")

        chain_choice = input("Choose (0-3, default=0): ").strip() or "0"

        extracted_dir = results['output_dir']

        if chain_choice == "1":
            self.source_dir = extracted_dir  # pre-fill for sort method
            # Temporarily override source so sort_by_checkpoint picks it up
            orig = input
            print(f"\n→ Running checkpoint sort on: {extracted_dir}")
            self.sort_by_checkpoint()
        elif chain_choice == "2":
            print(f"\n→ Running color sort on: {extracted_dir}")
            self.sort_by_color()
        elif chain_choice == "3":
            print(f"\n→ Running flatten on: {extracted_dir}")
            self.flatten_images()

    def view_session_logs(self):
        """View previous session logs"""
        print("\n📊 SESSION LOGS")
        print("-" * 40)
        
        logs_dir = os.path.join(os.getcwd(), "sort_logs")
        if not os.path.exists(logs_dir):
            print("❌ No logs directory found")
            return
        
        log_files = [f for f in os.listdir(logs_dir) if f.startswith('sort_') and f.endswith('.log')]
        
        if not log_files:
            print("❌ No log files found")
            return
        
        print(f"📋 Found {len(log_files)} log files:")
        for i, log_file in enumerate(sorted(log_files, reverse=True)[:5]):
            print(f"   {i+1}. {log_file}")
        
        choice = input("Enter number to view log (or press Enter to skip): ").strip()
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(log_files):
                log_path = os.path.join(logs_dir, sorted(log_files, reverse=True)[index])
                print(f"\n📄 Viewing: {log_files[index]}")
                print("-" * 60)
                
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Show last 50 lines
                    for line in lines[-50:]:
                        print(line.rstrip())
        except (ValueError, IndexError):
            print("❌ Invalid selection")
    
    def _get_directory_input(self, prompt: str) -> str:
        """Get and validate directory input from user"""
        directory = input(f"{prompt}: ").strip().strip('"\'')
        
        if not directory:
            print("❌ Directory path required")
            return ""
        
        if not os.path.exists(directory):
            print(f"❌ Directory not found: {directory}")
            return ""
        
        if not os.path.isdir(directory):
            print(f"❌ Path is not a directory: {directory}")
            return ""
        
        return directory


def main():
    """Main entry point"""
    try:
        sorter = SorterV2()
        sorter.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting Sorter 3.0.0...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this issue.")


if __name__ == "__main__":
    main()
