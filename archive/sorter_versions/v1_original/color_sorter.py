#!/usr/bin/env python3
"""
Color-based Image Sorter

Analyzes images for dominant colors and sorts them into color-themed folders.
Perfect for final organization of AI-generated images.
"""

import os
import shutil
from collections import Counter
from PIL import Image, ImageDraw
import colorsys

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

def rgb_to_hsv(r, g, b):
    """Convert RGB to HSV values."""
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

def get_dominant_color(image_path, num_colors=5, ignore_dark_threshold=0.1):
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
                # Skip very dark pixels that might skew results
                brightness = (r + g + b) / (3 * 255)
                if brightness > ignore_dark_threshold:
                    # Group similar colors together (reduce precision)
                    grouped_color = (r//16*16, g//16*16, b//16*16)
                    color_counts[grouped_color] += 1
            
            # Get most common colors
            dominant_colors = color_counts.most_common(num_colors)
            return dominant_colors[0][0] if dominant_colors else (128, 128, 128)
            
    except Exception as e:
        print(f"[Color Error] {image_path}: {e}")
        return (128, 128, 128)  # Default to gray

def classify_color(rgb_color, method="enhanced"):
    """Classify an RGB color into a named category."""
    r, g, b = rgb_color
    
    # Convert to HSV for better classification
    h, s, v = rgb_to_hsv(r, g, b)
    
    if method == "enhanced":
        # Enhanced classification with better black/dark handling
        # Handle grayscale with more restrictive black threshold
        if s < 0.15:  # Low saturation = grayscale
            if v < 0.1:  # Very dark threshold lowered
                return 'Black'
            elif v > 0.85:  # High brightness threshold
                return 'White'
            else:
                return 'Gray'
        
        # For colored pixels, be more lenient with dark colors
        # Handle colors by hue with brightness consideration
        hue_deg = h * 360
        
        # If it's a very dark color but has some saturation, classify by hue
        if v < 0.3 and s > 0.3:  # Dark but saturated
            # Still classify by hue for dark saturated colors
            pass
        
        if hue_deg < 15 or hue_deg >= 345:
            return 'Red'
        elif 15 <= hue_deg < 45:
            return 'Orange'
        elif 45 <= hue_deg < 75:
            return 'Yellow'
        elif 75 <= hue_deg < 150:
            return 'Green'
        elif 150 <= hue_deg < 250:
            return 'Blue'
        elif 250 <= hue_deg < 290:
            return 'Purple'
        elif 290 <= hue_deg < 345:
            return 'Pink'
        else:
            # Fallback for browns (low saturation, mid brightness)
            if s < 0.5 and 0.2 < v < 0.7:
                return 'Brown'
            return 'Gray'
    
    else:  # Original method
        # Handle grayscale first
        if s < 0.2:  # Low saturation = grayscale
            if v < 0.2:
                return 'Black'
            elif v > 0.8:
                return 'White'
            else:
                return 'Gray'
        
        # Handle colors by hue
        hue_deg = h * 360
        
        if hue_deg < 15 or hue_deg >= 345:
            return 'Red'
        elif 15 <= hue_deg < 45:
            return 'Orange'
        elif 45 <= hue_deg < 75:
            return 'Yellow'
        elif 75 <= hue_deg < 150:
            return 'Green'
        elif 150 <= hue_deg < 250:
            return 'Blue'
        elif 250 <= hue_deg < 290:
            return 'Purple'
        elif 290 <= hue_deg < 345:
            return 'Pink'
        else:
            # Fallback for browns (low saturation, mid brightness)
            if s < 0.5 and 0.2 < v < 0.7:
                return 'Brown'
            return 'Gray'

def analyze_image_color(image_path, method="enhanced"):
    """Analyze an image and return its dominant color category."""
    return analyze_image_color_advanced(image_path, method)

def sort_images_by_color(src_dir, output_dir, move_files=False, user_prefix="", sort_method="enhanced"):
    """Sort images by dominant color into categorized folders."""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Supported image extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    
    # Statistics tracking
    color_stats = Counter()
    processed_files = []
    
    print(f"Analyzing images for color sorting using '{sort_method}' method...")
    
    for filename in os.listdir(src_dir):
        file_path = os.path.join(src_dir, filename)
        
        # Skip non-files and non-images
        if not os.path.isfile(file_path):
            continue
            
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in image_extensions:
            continue
        
        try:
            # Analyze color using selected method
            color_category, dominant_rgb = analyze_image_color(file_path, sort_method)
            color_stats[color_category] += 1
            
            # Create color folder
            color_folder = os.path.join(output_dir, color_category)
            os.makedirs(color_folder, exist_ok=True)
            
            # Generate new filename with color prefix if requested
            if user_prefix:
                base_name = os.path.splitext(filename)[0]
                new_filename = f"[{user_prefix}_{color_category.upper()}] {base_name}{file_ext}"
            else:
                new_filename = filename
            
            # Ensure unique filename
            dest_path = os.path.join(color_folder, new_filename)
            counter = 1
            while os.path.exists(dest_path):
                base, ext = os.path.splitext(new_filename)
                dest_path = os.path.join(color_folder, f"{base}_{counter}{ext}")
                counter += 1
            
            # Move or copy file
            if move_files:
                shutil.move(file_path, dest_path)
                action = "Moved"
            else:
                shutil.copy2(file_path, dest_path)
                action = "Copied"
            
            print(f"[{action}] {filename} -> {color_category} (RGB: {dominant_rgb})")
            processed_files.append({
                'original': filename,
                'new_path': dest_path,
                'color': color_category,
                'rgb': dominant_rgb
            })
            
        except Exception as e:
            print(f"[Error] Failed to process {filename}: {e}")
            continue
    
    # Print summary
    print(f"\n=== Color Sorting Complete ===")
    print(f"Total files processed: {len(processed_files)}")
    print("Color distribution:")
    for color, count in sorted(color_stats.items()):
        print(f"  {color}: {count} files")
    
    return processed_files, color_stats

def create_color_preview(output_dir, color_stats):
    """Create a visual preview showing the color distribution."""
    try:
        # Create a simple color bar preview
        preview_width = 400
        preview_height = 60
        
        if not color_stats:
            return
        
        total_files = sum(color_stats.values())
        preview = Image.new('RGB', (preview_width, preview_height), 'white')
        draw = ImageDraw.Draw(preview)
        
        x_pos = 0
        for color_name, count in sorted(color_stats.items()):
            # Get representative RGB for this color category
            if color_name in COLOR_CATEGORIES:
                color_rgb = COLOR_CATEGORIES[color_name][0]
            else:
                color_rgb = (128, 128, 128)  # Default gray
            
            # Calculate width proportional to file count
            width = int((count / total_files) * preview_width)
            
            # Draw color bar
            draw.rectangle([x_pos, 0, x_pos + width, preview_height], fill=color_rgb)
            x_pos += width
        
        # Save preview
        preview_path = os.path.join(output_dir, 'color_distribution_preview.png')
        preview.save(preview_path)
        print(f"[Preview] Created color distribution preview: {os.path.basename(preview_path)}")
        
    except Exception as e:
        print(f"[Preview Error] Could not create color preview: {e}")

def analyze_image_color_advanced(image_path, method="enhanced"):
    """Analyze an image with multiple color detection methods."""
    if method == "brightness":
        return analyze_by_brightness(image_path)
    elif method == "temperature":
        return analyze_by_temperature(image_path)
    elif method == "center_focus":
        return analyze_center_weighted(image_path)
    else:  # enhanced or dominant
        dominant_rgb = get_dominant_color(image_path)
        color_category = classify_color(dominant_rgb, method)
        return color_category, dominant_rgb

def analyze_by_brightness(image_path):
    """Sort by overall image brightness levels."""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img = img.resize((100, 100))
            pixels = list(img.getdata())
            
            # Calculate average brightness
            total_brightness = sum((r + g + b) / 3 for r, g, b in pixels)
            avg_brightness = total_brightness / len(pixels)
            
            if avg_brightness < 60:
                return 'Dark', (40, 40, 40)
            elif avg_brightness < 120:
                return 'Medium', (120, 120, 120)
            elif avg_brightness < 180:
                return 'Bright', (180, 180, 180)
            else:
                return 'Very Bright', (220, 220, 220)
                
    except Exception as e:
        print(f"[Brightness Error] {image_path}: {e}")
        return 'Medium', (128, 128, 128)

def analyze_by_temperature(image_path):
    """Sort by warm vs cool color temperature."""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img = img.resize((100, 100))
            pixels = list(img.getdata())
            
            warm_score = 0
            cool_score = 0
            
            for r, g, b in pixels:
                # Warm colors have more red/yellow
                warm_score += (r + (g * 0.5)) * 0.01
                # Cool colors have more blue/green
                cool_score += (b + (g * 0.5)) * 0.01
            
            if warm_score > cool_score * 1.2:
                return 'Warm', (200, 100, 50)
            elif cool_score > warm_score * 1.2:
                return 'Cool', (50, 100, 200)
            else:
                return 'Neutral', (128, 128, 128)
                
    except Exception as e:
        print(f"[Temperature Error] {image_path}: {e}")
        return 'Neutral', (128, 128, 128)

def analyze_center_weighted(image_path):
    """Analyze color with more weight given to center of image."""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            center_x, center_y = width // 2, height // 2
            
            # Sample more from center area
            color_counts = Counter()
            
            for y in range(height):
                for x in range(width):
                    r, g, b = img.getpixel((x, y))
                    
                    # Weight pixels closer to center more heavily
                    distance_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    max_distance = (width ** 2 + height ** 2) ** 0.5
                    weight = 1 - (distance_from_center / max_distance)
                    weight = max(0.1, weight)  # Minimum weight
                    
                    grouped_color = (r//16*16, g//16*16, b//16*16)
                    color_counts[grouped_color] += weight
            
            # Get most weighted color
            if color_counts:
                dominant_rgb = color_counts.most_common(1)[0][0]
                color_category = classify_color(dominant_rgb, "enhanced")
                return color_category, dominant_rgb
            else:
                return 'Gray', (128, 128, 128)
                
    except Exception as e:
        print(f"[Center Weight Error] {image_path}: {e}")
        return 'Gray', (128, 128, 128)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sort images by dominant color')
    parser.add_argument('input_dir', help='Directory containing images to sort')
    parser.add_argument('output_dir', help='Directory to create color-sorted folders')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying')
    parser.add_argument('--prefix', default='', help='Prefix for renamed files')
    parser.add_argument('--method', default='enhanced', 
                       choices=['enhanced', 'original', 'brightness', 'temperature', 'center_focus'],
                       help='Color analysis method to use')
    
    args = parser.parse_args()
    
    processed_files, color_stats = sort_images_by_color(
        args.input_dir, 
        args.output_dir, 
        move_files=args.move,
        user_prefix=args.prefix,
        sort_method=args.method
    )
    
    create_color_preview(args.output_dir, color_stats)
