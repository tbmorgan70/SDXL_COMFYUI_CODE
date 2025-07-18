"""
Sorter 2.0 - Metadata Search Sorter

Search and sort images based on any metadata content.
Perfect for finding specific LoRAs, prompts, models, or any text in metadata.

Features:
- Search any field in metadata (LoRAs, prompts, models, etc.)
- Multiple search terms with AND/OR logic
- Case-insensitive searching
- Regex pattern support
- Flexible output organization
"""

import os
import shutil
import json
import re
import sys
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.metadata_engine import MetadataExtractor, MetadataAnalyzer
from core.diagnostics import SortLogger

class MetadataSearchSorter:
    """Sort images based on metadata content search"""
    
    def __init__(self, logger: Optional[SortLogger] = None):
        self.metadata_extractor = MetadataExtractor()
        self.metadata_analyzer = MetadataAnalyzer()
        self.logger = logger or SortLogger()
        
        # Statistics
        self.stats = {
            'total_images': 0,
            'images_matched': 0,
            'images_sorted': 0,
            'search_terms_used': 0,
            'folders_created': 0
        }
        
        # Search results tracking
        self.search_results = {}
    
    def search_and_sort(
        self,
        source_dir: str,
        output_dir: str,
        search_terms: List[str],
        search_mode: str = "any",  # "any", "all", "exact"
        search_fields: List[str] = None,  # Specific fields to search, None = all
        move_files: bool = False,
        create_subfolders: bool = True,
        case_sensitive: bool = False,
        use_regex: bool = False
    ) -> Dict[str, any]:
        """
        Search metadata and sort matching images
        
        Args:
            source_dir: Directory containing images to search
            output_dir: Base output directory for sorted images
            search_terms: List of terms to search for
            search_mode: "any" (OR logic), "all" (AND logic), "exact" (exact match)
            search_fields: Specific metadata fields to search (None = search all)
            move_files: True to move files, False to copy
            create_subfolders: Create subfolders for each search term
            case_sensitive: Whether search should be case sensitive
            use_regex: Whether to treat search terms as regex patterns
            
        Returns:
            Dictionary with search results and statistics
        """
        
        self.logger.start_operation("Metadata Search & Sort")
        self.logger._write_log(f"Source: {source_dir}")
        self.logger._write_log(f"Output: {output_dir}")
        self.logger._write_log(f"Search terms: {search_terms}")
        self.logger._write_log(f"Search mode: {search_mode}")
        self.logger._write_log(f"Operation: {'MOVE' if move_files else 'COPY'}")
        
        self.stats['search_terms_used'] = len(search_terms)
        
        # Find all PNG files
        png_files = self._find_png_files(source_dir)
        self.stats['total_images'] = len(png_files)
        
        if not png_files:
            self.logger.log_error("No PNG files found in source directory", source_dir, "No Input")
            return self._get_results()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Phase 1: Extract all metadata
        self.logger.start_operation("Metadata Extraction", len(png_files))
        metadata_results = self._extract_all_metadata(png_files)
        self.logger.complete_operation()
        
        # Phase 2: Search metadata
        self.logger.start_operation("Metadata Search")
        search_matches = self._search_metadata(
            png_files, metadata_results, search_terms, 
            search_mode, search_fields, case_sensitive, use_regex
        )
        self.logger.complete_operation()
        
        # Phase 3: Organize search results
        if create_subfolders:
            self.logger.start_operation("Organizing Results")
            organized_results = self._organize_by_search_terms(search_matches, search_terms)
            self.logger.complete_operation()
        else:
            organized_results = {"search_results": list(search_matches)}
        
        # Phase 4: Create folder structure
        self.logger.start_operation("Folder Creation")
        self._create_search_folders(output_dir, organized_results.keys())
        self.logger.complete_operation()
        
        # Phase 5: Sort files
        self.logger.start_operation("File Sorting", len(search_matches))
        self._sort_search_results(
            organized_results, metadata_results, output_dir, move_files
        )
        self.logger.complete_operation()
        
        # Generate summary
        results = self._get_results()
        results['search_matches'] = search_matches
        results['organized_results'] = organized_results
        self._log_summary(results)
        
        return results
    
    def search_specific_lora(
        self,
        source_dir: str,
        output_dir: str,
        lora_name: str,
        move_files: bool = False
    ) -> Dict[str, any]:
        """
        Convenience method to search for a specific LoRA
        Example: search_specific_lora(source, output, "Nova_Skyrift")
        """
        return self.search_and_sort(
            source_dir=source_dir,
            output_dir=output_dir,
            search_terms=[lora_name],
            search_mode="any",
            search_fields=["lora_name"],
            move_files=move_files,
            create_subfolders=False,
            case_sensitive=False
        )
    
    def search_by_prompt_keywords(
        self,
        source_dir: str,
        output_dir: str,
        keywords: List[str],
        move_files: bool = False,
        require_all_keywords: bool = False
    ) -> Dict[str, any]:
        """
        Convenience method to search by prompt keywords
        """
        return self.search_and_sort(
            source_dir=source_dir,
            output_dir=output_dir,
            search_terms=keywords,
            search_mode="all" if require_all_keywords else "any",
            search_fields=["positive_prompt", "negative_prompt"],
            move_files=move_files,
            create_subfolders=True,
            case_sensitive=False
        )
    
    def _find_png_files(self, source_dir: str) -> List[str]:
        """Find all PNG files in source directory"""
        png_files = []
        
        for file in os.listdir(source_dir):
            if file.lower().endswith('.png'):
                png_files.append(os.path.join(source_dir, file))
        
        return png_files
    
    def _extract_all_metadata(self, png_files: List[str]) -> Dict[str, Optional[Dict]]:
        """Extract metadata from all PNG files"""
        def progress_callback(current, total, filename):
            self.logger.update_progress(current, filename)
        
        return self.metadata_extractor.extract_batch(png_files, progress_callback)
    
    def _search_metadata(
        self,
        png_files: List[str],
        metadata_results: Dict[str, Optional[Dict]],
        search_terms: List[str],
        search_mode: str,
        search_fields: Optional[List[str]],
        case_sensitive: bool,
        use_regex: bool
    ) -> Set[str]:
        """Search metadata for matching terms"""
        matches = set()
        
        for file_path in png_files:
            metadata = metadata_results.get(file_path)
            
            if not metadata:
                continue
            
            # Extract searchable content
            searchable_content = self._extract_searchable_content(metadata, search_fields)
            
            # Perform search based on mode
            if search_mode == "any":
                # OR logic - any term matches
                if self._search_any_term(searchable_content, search_terms, case_sensitive, use_regex):
                    matches.add(file_path)
                    
            elif search_mode == "all":
                # AND logic - all terms must match
                if self._search_all_terms(searchable_content, search_terms, case_sensitive, use_regex):
                    matches.add(file_path)
                    
            elif search_mode == "exact":
                # Exact match
                if self._search_exact_match(searchable_content, search_terms, case_sensitive):
                    matches.add(file_path)
        
        self.stats['images_matched'] = len(matches)
        self.logger._write_log(f"Found {len(matches)} images matching search criteria")
        
        return matches
    
    def _extract_searchable_content(self, metadata: Dict, search_fields: Optional[List[str]]) -> Dict[str, str]:
        """Extract searchable content from metadata"""
        content = {}
        
        # Extract key fields using metadata analyzer
        checkpoints = self.metadata_analyzer.extract_checkpoints(metadata)
        loras = self.metadata_analyzer.extract_loras(metadata)
        prompts = self.metadata_analyzer.extract_prompts(metadata)
        sampling = self.metadata_analyzer.extract_sampling_params(metadata)
        
        # Organize searchable content
        content.update({
            'checkpoints': ' '.join(checkpoints),
            'loras': ' '.join(loras),
            'lora_name': ' '.join(loras),  # Alias for backward compatibility
            'positive_prompt': prompts.get('positive', ''),
            'negative_prompt': prompts.get('negative', ''),
            'prompts': f"{prompts.get('positive', '')} {prompts.get('negative', '')}",
            'sampling_params': ' '.join(f"{k}:{v}" for k, v in sampling.items()),
            'full_metadata': json.dumps(metadata).lower()
        })
        
        # If specific fields requested, filter content
        if search_fields:
            filtered_content = {}
            for field in search_fields:
                if field in content:
                    filtered_content[field] = content[field]
                # Also search in full metadata if field not found
                if field not in content:
                    filtered_content['full_metadata'] = content['full_metadata']
            content = filtered_content
        
        return content
    
    def _search_any_term(self, content: Dict[str, str], terms: List[str], case_sensitive: bool, use_regex: bool) -> bool:
        """Search for any of the terms (OR logic)"""
        for term in terms:
            if self._term_matches_content(content, term, case_sensitive, use_regex):
                return True
        return False
    
    def _search_all_terms(self, content: Dict[str, str], terms: List[str], case_sensitive: bool, use_regex: bool) -> bool:
        """Search for all terms (AND logic)"""
        for term in terms:
            if not self._term_matches_content(content, term, case_sensitive, use_regex):
                return False
        return True
    
    def _search_exact_match(self, content: Dict[str, str], terms: List[str], case_sensitive: bool) -> bool:
        """Search for exact matches"""
        combined_content = ' '.join(content.values())
        if not case_sensitive:
            combined_content = combined_content.lower()
            terms = [t.lower() for t in terms]
        
        return all(term in combined_content for term in terms)
    
    def _term_matches_content(self, content: Dict[str, str], term: str, case_sensitive: bool, use_regex: bool) -> bool:
        """Check if a term matches any content"""
        for field_content in content.values():
            if not field_content:
                continue
                
            search_text = field_content if case_sensitive else field_content.lower()
            search_term = term if case_sensitive else term.lower()
            
            if use_regex:
                try:
                    if re.search(search_term, search_text):
                        return True
                except re.error:
                    # Fallback to simple string search if regex is invalid
                    if search_term in search_text:
                        return True
            else:
                if search_term in search_text:
                    return True
        
        return False
    
    def _organize_by_search_terms(self, matches: Set[str], search_terms: List[str]) -> Dict[str, List[str]]:
        """Organize matches by which search terms they contain"""
        organized = {}
        
        # For each search term, find files that match it
        for term in search_terms:
            term_matches = []
            clean_term = re.sub(r'[<>:"|?*\\\/]', '_', term)  # Clean for folder name
            
            for file_path in matches:
                # Simple check - this could be more sophisticated
                if term.lower() in os.path.basename(file_path).lower():
                    term_matches.append(file_path)
            
            if term_matches:
                organized[clean_term] = term_matches
        
        # Add all matches to a general folder if no specific term folders
        if not organized:
            organized["search_results"] = list(matches)
        
        return organized
    
    def _create_search_folders(self, output_dir: str, folder_names: List[str]):
        """Create folders for search results"""
        for folder_name in folder_names:
            folder_path = os.path.join(output_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            self.logger.log_folder_created(folder_path)
            self.stats['folders_created'] += 1
    
    def _sort_search_results(
        self,
        organized_results: Dict[str, List[str]],
        metadata_results: Dict[str, Optional[Dict]],
        output_dir: str,
        move_files: bool
    ):
        """Sort search results into folders"""
        file_count = 0
        total_files = sum(len(files) for files in organized_results.values())
        
        for folder_name, file_list in organized_results.items():
            folder_path = os.path.join(output_dir, folder_name)
            
            for file_path in file_list:
                file_count += 1
                self.logger.update_progress(file_count, os.path.basename(file_path))
                
                try:
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(folder_path, filename)
                    
                    # Handle filename conflicts
                    dest_path = self._resolve_filename_conflict(dest_path)
                    
                    # Move or copy the file
                    if move_files:
                        shutil.move(file_path, dest_path)
                        operation = "move"
                    else:
                        shutil.copy2(file_path, dest_path)
                        operation = "copy"
                    
                    self.logger.log_file_operation(operation, file_path, dest_path, True)
                    self.stats['images_sorted'] += 1
                    
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
        
        return dest_path
    
    def _get_results(self) -> Dict[str, any]:
        """Get comprehensive search results"""
        extractor_stats = self.metadata_extractor.get_statistics()
        
        return {
            'search_stats': self.stats,
            'metadata_stats': extractor_stats,
            'session_summary': self.logger.get_summary()
        }
    
    def _log_summary(self, results: Dict[str, any]):
        """Log comprehensive summary"""
        stats = results['search_stats']
        
        self.logger._write_log("\n=== METADATA SEARCH SUMMARY ===")
        self.logger._write_log(f"Total images found: {stats['total_images']}")
        self.logger._write_log(f"Images matched: {stats['images_matched']}")
        self.logger._write_log(f"Images sorted: {stats['images_sorted']}")
        self.logger._write_log(f"Search terms used: {stats['search_terms_used']}")
        self.logger._write_log(f"Folders created: {stats['folders_created']}")
        
        match_rate = (stats['images_matched'] / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
        self.logger._write_log(f"Match rate: {match_rate:.1f}%")


# Example usage
if __name__ == "__main__":
    # Test the metadata search sorter
    sorter = MetadataSearchSorter()
    
    source = input("Enter source directory: ").strip().strip('"\'')
    
    if not os.path.exists(source):
        print("❌ Source directory not found")
        exit()
    
    print("\n🔍 Search Options:")
    print("1. Search for specific LoRA")
    print("2. Search for prompt keywords") 
    print("3. Custom search")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        lora_name = input("Enter LoRA name to search for: ").strip()
        output = input("Enter output directory: ").strip() or os.path.join(source, f"lora_{lora_name}")
        move_files = input("Move files? (y/n): ").lower() == 'y'
        
        results = sorter.search_specific_lora(source, output, lora_name, move_files)
        
    elif choice == "2":
        keywords = input("Enter keywords (separated by commas): ").strip().split(',')
        keywords = [k.strip() for k in keywords if k.strip()]
        output = input("Enter output directory: ").strip() or os.path.join(source, "keyword_search")
        move_files = input("Move files? (y/n): ").lower() == 'y'
        require_all = input("Require ALL keywords? (y/n): ").lower() == 'y'
        
        results = sorter.search_by_prompt_keywords(source, output, keywords, move_files, require_all)
        
    else:
        search_terms = input("Enter search terms (separated by commas): ").strip().split(',')
        search_terms = [t.strip() for t in search_terms if t.strip()]
        output = input("Enter output directory: ").strip() or os.path.join(source, "search_results")
        move_files = input("Move files? (y/n): ").lower() == 'y'
        
        results = sorter.search_and_sort(source, output, search_terms, move_files=move_files)
    
    print(f"\n✅ Search complete! Check results in: {output}")
    
    # Offer to open output folder
    open_folder = input("Open output folder? (y/n): ").lower() == 'y'
    if open_folder:
        os.startfile(output)
