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
from core.enhanced_metadata_formatter import EnhancedMetadataFormatter
from sorters.checkpoint_sorter import CheckpointSorter
from sorters.metadata_search import MetadataSearchSorter
from sorters.color_sorter import ColorSorter
from sorters.image_flattener import ImageFlattener
from sorters.filename_cleanup import FilenameCleanup

class SorterV2:
    """Main interface for Sorter 2.0"""
    
    def __init__(self):
        self.logger = SortLogger()
        print("🚀 Sorter 2.0 - Advanced ComfyUI Image Organizer")
        print("=" * 60)
    
    def main_menu(self):
        """Display main menu and handle user choices"""
        while True:
            print("\n📋 SORTING OPTIONS:")
            print("1. 🎯 Sort by Base Checkpoint (Most Used)")
            print("2. 🔍 Search & Sort by Metadata")
            print("3. 🌈 Sort by Color")
            print("4. 📂 Flatten Image Folders")
            print("5. � Cleanup Filenames & Remove Metadata")
            print("6. �🧪 Test Metadata Extraction")
            print("7. 📊 View Previous Session Logs")
            print("0. ❌ Exit")
            
            choice = input("\nChoose option (0-8): ").strip()
            
            if choice == "1":
                self.sort_by_checkpoint()
            elif choice == "2":
                self.search_and_sort()
            elif choice == "3":
                self.sort_by_color()
            elif choice == "4":
                self.flatten_images()
            elif choice == "5":
                self.cleanup_filenames()
            elif choice == "6":
                self.generate_metadata_reports()
            elif choice == "7":
                self.test_metadata_extraction()
            elif choice == "8":
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
        """Placeholder for color sorting"""
        print("\n🌈 COLOR SORTING")
        print("Coming soon! This will integrate your existing color sorter.")
        input("Press Enter to continue...")
    
    def flatten_images(self):
        """Placeholder for image flattening"""
        print("\n📂 FLATTEN IMAGES")
        print("Coming soon! This will integrate your existing image flattener.")
        input("Press Enter to continue...")
    
    def test_metadata(self):
        """Test metadata extraction on sample files"""
        print("\n🧪 TEST METADATA EXTRACTION")
        print("-" * 40)
        
        source_dir = self._get_directory_input("Enter directory with PNG files to test")
        if not source_dir:
            return
        
        png_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.png')]
        if not png_files:
            print("❌ No PNG files found")
            return
        
        test_count = min(10, len(png_files))
        print(f"📊 Testing metadata extraction on {test_count} files...")
        
        extractor = MetadataExtractor()
        analyzer = MetadataAnalyzer()
        
        for i, filename in enumerate(png_files[:test_count]):
            file_path = os.path.join(source_dir, filename)
            print(f"\n🔍 Testing {i+1}/{test_count}: {filename}")
            
            metadata = extractor.extract_single(file_path)
            
            if metadata:
                primary_checkpoint = analyzer.extract_primary_checkpoint(metadata)
                loras = analyzer.extract_loras(metadata)
                sampling = analyzer.extract_sampling_params(metadata)
                
                print(f"  ✅ Metadata extracted successfully")
                print(f"  📋 Primary checkpoint: {primary_checkpoint}")
                print(f"  🎨 LoRAs: {loras[:3]}{'...' if len(loras) > 3 else ''}")
                print(f"  ⚙️  Sampling: CFG={sampling.get('cfg')}, Steps={sampling.get('steps')}")
            else:
                print(f"  ❌ No metadata found")
        
        # Show statistics
        stats = extractor.get_statistics()
        print(f"\n📊 Extraction Statistics:")
        print(f"   Success rate: {stats['success_rate_percent']}%")
        print(f"   Successful: {stats['successful_extractions']}")
        print(f"   Failed: {stats['failed_extractions']}")
    
    def view_logs(self):
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
        
        dark_threshold = input("Dark pixel threshold (0.0-1.0, default=0.1): ").strip()
        try:
            dark_threshold = float(dark_threshold) if dark_threshold else 0.1
            dark_threshold = max(0.0, min(1.0, dark_threshold))
        except ValueError:
            dark_threshold = 0.1
        
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
        print(f"   Dark threshold: {dark_threshold}")
        
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
            ignore_dark_threshold=dark_threshold,
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
    
    def cleanup_filenames(self):
        """Clean up filenames and remove metadata files"""
        print("\n🧹 FILENAME CLEANUP & METADATA REMOVAL")
        print("-" * 50)
        print("This tool will:")
        print("• Remove old naming patterns like '[workflow_test_batch1]'")
        print("• Clean up 'Gen 31 $0152' type patterns")
        print("• Remove _metadata.json files (optional)")
        print("• Preview changes before applying")
        
        # Get source directory
        source_dir = self._get_directory_input("Enter directory to clean up")
        if not source_dir:
            return
        
        # Cleanup options
        print("\n🔧 CLEANUP OPTIONS:")
        rename_files = input("Clean up filenames? (y/n, default=y): ").strip().lower() != 'n'
        remove_metadata = input("Remove _metadata.json files? (y/n, default=y): ").strip().lower() != 'n'
        
        filename_prefix = "image"
        if rename_files:
            custom_prefix = input("Enter filename prefix (default='image'): ").strip()
            if custom_prefix:
                # Clean the prefix to make it filesystem-safe
                filename_prefix = re.sub(r'[<>:"/\\|?*]', '_', custom_prefix)
                filename_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', filename_prefix)
                filename_prefix = filename_prefix.strip('_-')
                if not filename_prefix:
                    filename_prefix = "image"
        
        # Preview mode first
        print("\n👀 PREVIEW MODE - No files will be changed yet")
        cleanup = FilenameCleanup(self.logger)
        
        print("🔍 Running preview...")
        cleanup.cleanup_directory(
            source_dir=source_dir,
            remove_metadata_files=remove_metadata,
            rename_files=rename_files,
            filename_prefix=filename_prefix,
            dry_run=True
        )
        
        # Show preview results
        print(f"\n📊 PREVIEW RESULTS:")
        print(f"   Files to rename: {cleanup.stats['files_renamed']}")
        print(f"   Metadata files to remove: {cleanup.stats['metadata_files_removed']}")
        print(f"   Total files processed: {cleanup.stats['total_files']}")
        
        if cleanup.stats['files_renamed'] == 0 and cleanup.stats['metadata_files_removed'] == 0:
            print("✅ No cleanup needed - all files are already clean!")
            return
        
        # Confirm changes
        print(f"\n📋 CONFIRMATION:")
        print(f"   Directory: {source_dir}")
        print(f"   Files to rename: {cleanup.stats['files_renamed']}")
        print(f"   Metadata files to remove: {cleanup.stats['metadata_files_removed']}")
        if rename_files:
            print(f"   Filename prefix: '{filename_prefix}'")
        
        if input("\nApply these changes? (y/n): ").strip().lower() != 'y':
            print("❌ Cleanup cancelled")
            return
        
        # Apply changes
        print("🚀 Applying cleanup changes...")
        cleanup = FilenameCleanup(self.logger)  # Fresh instance for actual run
        success = cleanup.cleanup_directory(
            source_dir=source_dir,
            remove_metadata_files=remove_metadata,
            rename_files=rename_files,
            filename_prefix=filename_prefix,
            dry_run=False
        )
        
        if success:
            print("✅ FILENAME CLEANUP COMPLETE!")
            print(f"   Files renamed: {cleanup.stats['files_renamed']}")
            print(f"   Metadata files removed: {cleanup.stats['metadata_files_removed']}")
            if input("\nOpen folder? (y/n): ").strip().lower() == 'y':
                import subprocess
                subprocess.run(['explorer', os.path.abspath(source_dir)], shell=True)
        else:
            print("❌ Cleanup completed with errors - check logs for details")
    
    def generate_metadata_reports(self):
        """Generate enhanced metadata reports for PNG files"""
        print("\n📝 GENERATE ENHANCED METADATA REPORTS")
        print("-" * 60)
        print("Creates comprehensive, formatted text reports from ComfyUI metadata")
        print("Perfect for documentation, sharing, and analysis")
        
        # Get source directory
        source_dir = self._get_directory_input("Enter directory with PNG files")
        if not source_dir:
            return
        
        # Count PNG files
        png_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.png')]
        if not png_files:
            print("❌ No PNG files found in source directory")
            return
        
        print(f"📊 Found {len(png_files)} PNG files")
        
        # Options
        create_individual = input("Create individual report files? (y/n, default=y): ").strip().lower() != 'n'
        create_summary = input("Create summary report? (y/n, default=y): ").strip().lower() != 'n'
        
        if not create_individual and not create_summary:
            print("❌ No report types selected")
            return
        
        # Get output directory
        output_dir = input("Enter output directory (or press Enter for 'metadata_reports'): ").strip().strip('"\'')
        if not output_dir:
            output_dir = os.path.join(source_dir, "metadata_reports")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Confirmation
        print(f"\n📋 CONFIRMATION:")
        print(f"   Source: {source_dir}")
        print(f"   Output: {output_dir}")
        print(f"   PNG files: {len(png_files)}")
        print(f"   Individual reports: {'Yes' if create_individual else 'No'}")
        print(f"   Summary report: {'Yes' if create_summary else 'No'}")
        
        if input("\nProceed? (y/n): ").strip().lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        # Start processing
        print("🚀 Generating metadata reports...")
        
        extractor = MetadataExtractor()
        formatter = EnhancedMetadataFormatter()
        
        processed = 0
        successful = 0
        failed = 0
        summary_data = []
        
        for png_file in png_files:
            processed += 1
            png_path = os.path.join(source_dir, png_file)
            
            print(f"Processing {processed}/{len(png_files)}: {png_file}")
            
            try:
                # Extract metadata
                metadata = extractor.extract_single(png_path)
                if not metadata:
                    print(f"  ⚠️ No metadata found in {png_file}")
                    failed += 1
                    continue
                
                # Generate formatted report
                report_text = formatter.format_metadata_to_text(metadata, png_path)
                
                # Save individual report
                if create_individual:
                    report_filename = os.path.splitext(png_file)[0] + "_metadata_report.txt"
                    report_path = os.path.join(output_dir, report_filename)
                    
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(report_text)
                
                # Collect summary data
                if create_summary:
                    summary_data.append({
                        'filename': png_file,
                        'metadata': metadata,
                        'report': report_text
                    })
                
                successful += 1
                print(f"  ✅ Report generated")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1
        
        # Generate summary report
        if create_summary and summary_data:
            print("\n📊 Generating summary report...")
            summary_path = os.path.join(output_dir, "metadata_summary_report.txt")
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=== BATCH METADATA SUMMARY REPORT ===\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Source Directory: {source_dir}\n")
                f.write(f"Total Files: {len(png_files)}\n")
                f.write(f"Successfully Processed: {successful}\n")
                f.write(f"Failed: {failed}\n")
                f.write("=" * 50 + "\n\n")
                
                # Add each report
                for i, data in enumerate(summary_data, 1):
                    f.write(f"FILE {i}/{len(summary_data)}: {data['filename']}\n")
                    f.write("-" * 50 + "\n")
                    f.write(data['report'])
                    f.write("\n" + "=" * 50 + "\n\n")
        
        # Results
        print(f"\n✅ METADATA REPORTS COMPLETE!")
        print(f"   Processed: {processed}/{len(png_files)} files")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        if create_individual:
            print(f"   Individual reports: {successful} files")
        if create_summary:
            print(f"   Summary report: metadata_summary_report.txt")
        
        if input("\nOpen output folder? (y/n): ").strip().lower() == 'y':
            import subprocess
            subprocess.run(['explorer', os.path.abspath(output_dir)], shell=True)
    
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
        print("\n\n👋 Exiting Sorter 2.0...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this issue.")


if __name__ == "__main__":
    main()
