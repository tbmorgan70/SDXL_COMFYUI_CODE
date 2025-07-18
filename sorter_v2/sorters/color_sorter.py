import os
import sys
import shutil
from collections import Counter
from pathlib import Path
from PIL import Image
import colorsys

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.diagnostics import SortLogger

# Color categories with RGB ranges
COLOR_CATEGORIES = {
    'Red': [(255, 0, 0), (220, 20, 60), (178, 34, 34), (139, 0, 0)],
    'Orange': [(255, 165, 0), (255, 140, 0), (255, 69, 0), (255, 99, 71)],
    'Yellow': [(255, 255, 0), (255, 215, 0), (218, 165, 32), (184, 134, 11)],
    'Green': [(0, 255, 0), (34, 139, 34), (0, 128, 0), (46, 125, 50)],
    'Blue': [(0, 0, 255), (30, 144, 255), (0, 191, 255), (70, 130, 180)],
    'Purple': [(128, 0, 128), (75, 0, 130), (148, 0, 211), (138, 43, 226)],
    'Pink': [(255, 192, 203), (255, 20, 147), (219, 112, 147), (199, 21, 133)],
    'Brown': [(165, 42, 42), (139, 69, 19), (160, 82, 45), (210, 180, 140)],
    'Black': [(0, 0, 0), (25, 25, 25), (50, 50, 50), (75, 75, 75)],
    'White': [(255, 255, 255), (248, 248, 255), (245, 245, 245), (220, 220, 220)],
    'Gray': [(128, 128, 128), (105, 105, 105), (169, 169, 169), (192, 192, 192)]
}

class ColorSorter:
    """Enhanced color sorting with progress tracking and logging"""
    
    def __init__(self, logger: SortLogger = None):
        self.logger = logger or SortLogger()
    
    def rgb_to_hsv(self, r, g, b):
        """Convert RGB to HSV values."""
        return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    
    def get_dominant_color(self, image_path, num_colors=5, ignore_dark_threshold=0.1):
        """Extract the dominant color from an image, with option to ignore very dark pixels."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize for faster processing
                img = img.resize((150, 150))
                
                # Get all pixels
                pixels = list(img.getdata())
                
                # Count color frequencies (with some grouping to reduce noise)
                color_counts = Counter()
                for r, g, b in pixels:
                    # Skip very dark pixels if requested
                    h, s, v = self.rgb_to_hsv(r, g, b)
                    if v < ignore_dark_threshold:
                        continue
                    
                    # Group similar colors (reduce precision)
                    grouped_color = (r//10*10, g//10*10, b//10*10)
                    color_counts[grouped_color] += 1
                
                if not color_counts:
                    return None
                
                # Get most common color
                dominant_rgb = color_counts.most_common(1)[0][0]
                return dominant_rgb
                
        except Exception as e:
            self.logger.log_error(f"Error analyzing color for {image_path}: {e}")
            return None
    
    def categorize_color(self, rgb_color):
        """Categorize an RGB color into one of the predefined color categories."""
        if not rgb_color:
            return "Unknown"
        
        r, g, b = rgb_color
        best_category = "Unknown"
        min_distance = float('inf')
        
        for category_name, category_colors in COLOR_CATEGORIES.items():
            for cat_r, cat_g, cat_b in category_colors:
                # Calculate Euclidean distance in RGB space
                distance = ((r - cat_r) ** 2 + (g - cat_g) ** 2 + (b - cat_b) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    best_category = category_name
        
        return best_category
    
    def sort_by_color(self, source_dir, output_dir, move_files=False, 
                     create_metadata=True, ignore_dark_threshold=0.1,
                     rename_files=False, user_prefix=''):
        """
        Sort images by dominant color into categorized folders
        
        Args:
            source_dir: Source directory containing images
            output_dir: Output directory for sorted images
            move_files: Whether to move (True) or copy (False) files
            create_metadata: Whether to create metadata files
            ignore_dark_threshold: Threshold for ignoring dark pixels (0.0-1.0)
            rename_files: Whether to rename files with sequential numbering
            user_prefix: Custom prefix for renamed files (e.g. 'myproject')
        """
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        
        # Start logging
        operation_name = "Color Sorting"
        self.logger.start_operation(operation_name)
        self.logger.log_config("Source", str(source_path))
        self.logger.log_config("Output", str(output_path))
        self.logger.log_config("Operation", "MOVE" if move_files else "COPY")
        self.logger.log_config("Dark threshold", str(ignore_dark_threshold))
        
        # Find all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_path.glob(f'*{ext}'))
            image_files.extend(source_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            self.logger.log_error("No image files found in source directory")
            return False
        
        total_files = len(image_files)
        self.logger.log_info(f"Found {total_files} image files to process")
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Track statistics
        color_stats = {}
        successful = 0
        failed = 0
        
        # Analyze colors
        self.logger.start_phase("Color Analysis")
        
        for i, image_file in enumerate(image_files):
            if i % 25 == 0:  # Progress every 25 files
                self.logger.update_progress(i, total_files, str(image_file.name))
            
            # Get dominant color
            dominant_color = self.get_dominant_color(str(image_file), ignore_dark_threshold=ignore_dark_threshold)
            color_category = self.categorize_color(dominant_color)
            
            # Track statistics
            if color_category not in color_stats:
                color_stats[color_category] = 0
            color_stats[color_category] += 1
            
            # Store result for sorting phase
            setattr(image_file, '_color_category', color_category)
            setattr(image_file, '_dominant_color', dominant_color)
        
        self.logger.end_phase("Color Analysis")
        
        # Create color category folders
        self.logger.start_phase("Folder Creation")
        
        for color_category in color_stats.keys():
            category_dir = output_path / color_category
            category_dir.mkdir(exist_ok=True)
            self.logger.log_folder_operation("Created", str(category_dir))
        
        self.logger.end_phase("Folder Creation")
        
        # Sort files into color folders
        self.logger.start_phase("File Sorting")
        
        # Initialize renaming counters for each color category
        rename_counters = {}
        if rename_files:
            for color_category in color_stats.keys():
                rename_counters[color_category] = 1
        
        for i, image_file in enumerate(image_files):
            try:
                color_category = getattr(image_file, '_color_category', 'Unknown')
                target_dir = output_path / color_category
                
                # Generate target filename
                if rename_files:
                    # Create sequential numbered filename
                    counter = rename_counters[color_category]
                    if user_prefix:
                        # Use custom prefix with color category
                        new_name = f"{user_prefix}_{color_category.lower()}_img{counter}{image_file.suffix}"
                    else:
                        # Use color category with sequential number
                        new_name = f"{color_category.lower()}_img{counter}{image_file.suffix}"
                    target_file = target_dir / new_name
                    rename_counters[color_category] += 1
                else:
                    # Use original filename
                    target_file = target_dir / image_file.name
                    
                    # Handle name conflicts for original filenames
                    counter = 1
                    while target_file.exists():
                        stem = image_file.stem
                        suffix = image_file.suffix
                        target_file = target_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                
                # Move or copy file
                if move_files:
                    shutil.move(str(image_file), str(target_file))
                    operation = "MOVED"
                else:
                    shutil.copy2(str(image_file), str(target_file))
                    operation = "COPIED"
                
                self.logger.log_file_operation(operation, str(image_file), str(target_file))
                successful += 1
                
                if i % 25 == 0:  # Progress every 25 files
                    self.logger.update_progress(i, total_files, str(image_file.name))
                
            except Exception as e:
                self.logger.log_error(f"Failed to process {image_file}: {e}")
                failed += 1
        
        self.logger.end_phase("File Sorting")
        
        # Create metadata files if requested
        if create_metadata:
            self.logger.start_phase("Metadata Creation")
            
            for color_category, count in color_stats.items():
                category_dir = output_path / color_category
                metadata_file = category_dir / "color_info.txt"
                
                with open(metadata_file, 'w') as f:
                    f.write(f"Color Category: {color_category}\n")
                    f.write(f"Image Count: {count}\n")
                    f.write(f"Sort Date: {self.logger.session_id}\n")
                    f.write(f"Dark Threshold: {ignore_dark_threshold}\n")
                
                self.logger.log_file_operation("CREATED", "metadata", str(metadata_file))
            
            self.logger.end_phase("Metadata Creation")
        
        # Log final statistics
        self.logger.end_operation(operation_name)
        
        print(f"\n=== COLOR SORTING SUMMARY ===")
        print(f"Total images found: {total_files}")
        print(f"Successfully sorted: {successful}")
        print(f"Failed: {failed}")
        print(f"Color categories found: {len(color_stats)}")
        print(f"Success rate: {(successful/total_files)*100:.1f}%")
        
        print(f"\n=== COLOR DISTRIBUTION ===")
        for color, count in sorted(color_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {color}: {count} images")
        
        return successful > 0
