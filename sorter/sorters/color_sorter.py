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
from core.file_operations import FileOperationsHandler

# Bucket names -- neutrals are only chosen when they dominate the image
# (see neutral_dominance in classify_image).
NEUTRAL_CATEGORIES = ('Black', 'White', 'Gray')
CHROMATIC_CATEGORIES = ('Red', 'Orange', 'Yellow', 'Green', 'Cyan',
                        'Blue', 'Purple', 'Pink', 'Brown')

class ColorSorter:
    """Color sorting via HSV pixel voting with chromatic priority.

    Every pixel is bucketed by HSV rules (hue ranges for colors; value/
    saturation thresholds for black/white/gray), then the image takes the
    plurality color. Neutrals only win when they exceed neutral_dominance,
    so a subject on a dark background sorts by the subject's color.
    """

    ANALYSIS_SIZE = 128  # thumbnail edge used for pixel voting

    def __init__(self, logger: SortLogger = None):
        self.logger = logger or SortLogger()
        self.file_handler = FileOperationsHandler(self.logger)

    @staticmethod
    def classify_pixel(h, s, v, black_level, white_level, gray_sat):
        """Bucket one HSV pixel (h,s,v all 0..1) into a category name."""
        if v <= black_level:
            return 'Black'
        if s <= gray_sat:
            return 'White' if v >= white_level else 'Gray'

        hue = h * 360.0

        # Light, washed-out reds/magentas read as pink
        if (hue < 15 or hue >= 345) and s < 0.45 and v > 0.75:
            return 'Pink'
        # Dark or muddy orange reads as brown
        if 15 <= hue < 50 and (v < 0.60 or s < 0.35):
            return 'Brown'

        if hue < 15 or hue >= 345:
            return 'Red'
        if hue < 45:
            return 'Orange'
        if hue < 70:
            return 'Yellow'
        if hue < 165:
            return 'Green'
        if hue < 200:
            return 'Cyan'
        if hue < 260:
            return 'Blue'
        if hue < 290:
            return 'Purple'
        return 'Pink'  # 290..345 magenta range

    def classify_image(self, image_path, black_level=0.12, white_level=0.90,
                       gray_sat=0.15, neutral_dominance=0.75):
        """Classify an image into a color category by pixel voting.

        Returns (category, breakdown) where breakdown maps category -> share
        (0..1) of pixels, or ("Unknown", {}) on failure.
        """
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.thumbnail((self.ANALYSIS_SIZE, self.ANALYSIS_SIZE))
                pixels = img.getdata()

                votes = Counter()
                for r, g, b in pixels:
                    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                    votes[self.classify_pixel(h, s, v, black_level, white_level, gray_sat)] += 1

                total = sum(votes.values())
                if total == 0:
                    return "Unknown", {}

                breakdown = {cat: n / total for cat, n in votes.items()}
                neutral_share = sum(breakdown.get(c, 0.0) for c in NEUTRAL_CATEGORIES)

                chromatic = {c: breakdown[c] for c in breakdown if c in CHROMATIC_CATEGORIES}
                neutrals = {c: breakdown[c] for c in breakdown if c in NEUTRAL_CATEGORIES}

                # Chromatic priority: strongest color wins unless the image
                # is overwhelmingly neutral.
                if chromatic and neutral_share < neutral_dominance:
                    category = max(chromatic, key=chromatic.get)
                elif neutrals:
                    category = max(neutrals, key=neutrals.get)
                elif chromatic:
                    category = max(chromatic, key=chromatic.get)
                else:
                    return "Unknown", {}

                return category, breakdown

        except Exception as e:
            self.logger.log_error(f"Error analyzing color for {image_path}: {e}")
            return "Unknown", {}
    
    def sort_by_color(self, source_dir, output_dir, move_files=False,
                     create_metadata=True, rename_files=False, user_prefix='',
                     black_level=0.12, white_level=0.90, gray_sat=0.15,
                     neutral_dominance=0.75):
        """
        Sort images by dominant color into categorized folders

        Args:
            source_dir: Source directory containing images
            output_dir: Output directory for sorted images
            move_files: Whether to move (True) or copy (False) files
            create_metadata: Whether to create metadata files
            rename_files: Whether to rename files with sequential numbering
            user_prefix: Custom prefix for renamed files (e.g. 'myproject')
            black_level: Pixels darker than this count as black (0-1)
            white_level: Bright low-saturation pixels above this count as white (0-1)
            gray_sat: Pixels below this saturation are neutral, not a color (0-1)
            neutral_dominance: Neutral share needed for black/white/gray to
                               beat the strongest color (0-1)
        """
        source_path = Path(source_dir)
        output_path = Path(output_dir)

        # Start logging
        operation_name = "Color Sorting"
        self.logger.start_operation(operation_name)
        self.logger.log_config("Source", str(source_path))
        self.logger.log_config("Output", str(output_path))
        self.logger.log_config("Operation", "MOVE" if move_files else "COPY")
        self.logger.log_config("Black level", f"{black_level:.2f}")
        self.logger.log_config("White level", f"{white_level:.2f}")
        self.logger.log_config("Color purity (gray sat)", f"{gray_sat:.2f}")
        self.logger.log_config("Neutral dominance", f"{neutral_dominance:.2f}")
        
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
        file_color_mapping = {}  # Store color info separately from path objects
        successful = 0
        failed = 0
        
        # Analyze colors
        self.logger.start_phase("Color Analysis")
        
        for i, image_file in enumerate(image_files):
            if i % 25 == 0:  # Progress every 25 files
                self.logger.update_progress(i, total_files, str(image_file.name))

            color_category, breakdown = self.classify_image(
                str(image_file),
                black_level=black_level,
                white_level=white_level,
                gray_sat=gray_sat,
                neutral_dominance=neutral_dominance,
            )

            # Log top shares so surprising results are explainable
            if breakdown:
                top = sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)[:3]
                shares = ", ".join(f"{c} {p:.0%}" for c, p in top)
                self.logger.log_info(f"  {image_file.name}: {shares} -> {color_category}")

            # Track statistics
            if color_category not in color_stats:
                color_stats[color_category] = 0
            color_stats[color_category] += 1

            # Store result for sorting phase in separate dictionary
            file_color_mapping[str(image_file)] = {
                'color_category': color_category,
                'breakdown': breakdown
            }
        
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
                file_path_str = str(image_file)
                color_info = file_color_mapping.get(file_path_str, {})
                color_category = color_info.get('color_category', 'Unknown')
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
                
                # Move or copy file with its metadata
                success, moved_files = self.file_handler.move_image_with_metadata(
                    str(image_file), str(target_file), move_files
                )
                
                if success:
                    operation = "MOVED" if move_files else "COPIED"
                    self.logger.log_file_operation(operation, str(image_file), str(target_file))
                    successful += 1
                    
                    # Log all moved files (image + metadata)
                    for moved_file in moved_files:
                        self.logger.log_info(moved_file)
                else:
                    operation = "move" if move_files else "copy"
                    raise Exception(f"Failed to {operation} file")
                
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
                    f.write(f"Black Level: {black_level}\n")
                    f.write(f"White Level: {white_level}\n")
                    f.write(f"Color Purity (gray sat): {gray_sat}\n")
                    f.write(f"Neutral Dominance: {neutral_dominance}\n")
                
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
