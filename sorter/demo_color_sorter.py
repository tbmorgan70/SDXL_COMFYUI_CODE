#!/usr/bin/env python3
"""
Demo script to test the color sorter functionality with sample images.
"""

import os
from PIL import Image, ImageDraw
import color_sorter

def create_sample_images(output_dir):
    """Create sample images with different dominant colors for testing."""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define colors to create sample images
    colors_to_create = {
        'red_image.png': (255, 0, 0),
        'blue_image.png': (0, 0, 255),
        'green_image.png': (0, 255, 0),
        'yellow_image.png': (255, 255, 0),
        'purple_image.png': (128, 0, 128),
        'orange_image.png': (255, 165, 0),
        'pink_image.png': (255, 192, 203),
        'brown_image.png': (139, 69, 19),
        'black_image.png': (0, 0, 0),
        'white_image.png': (255, 255, 255),
        'gray_image.png': (128, 128, 128)
    }
    
    print(f"Creating sample images in: {output_dir}")
    
    for filename, color in colors_to_create.items():
        # Create a 200x200 image with the dominant color
        img = Image.new('RGB', (200, 200), color)
        draw = ImageDraw.Draw(img)
        
        # Add some texture/variation while keeping the dominant color
        for i in range(10):
            x1, y1 = i*20, i*20
            x2, y2 = x1+20, y1+20
            # Slightly vary the color for texture
            varied_color = tuple(max(0, min(255, c + (i*5 - 25))) for c in color)
            draw.rectangle([x1, y1, x2, y2], fill=varied_color)
        
        # Save the image
        img_path = os.path.join(output_dir, filename)
        img.save(img_path)
        print(f"Created: {filename}")
    
    print(f"Sample images created successfully!")
    return output_dir

def demo_color_sorting():
    """Run a demo of the color sorting functionality."""
    print("=== Color Sorter Demo ===\n")
    
    # Create sample images
    sample_dir = "sample_images_for_color_test"
    create_sample_images(sample_dir)
    
    # Run color sorting
    output_dir = "color_sorted_demo"
    print(f"\nSorting images from {sample_dir} to {output_dir}...")
    
    processed_files, color_stats = color_sorter.sort_images_by_color(
        sample_dir, 
        output_dir, 
        move_files=False,  # Copy so we keep originals
        user_prefix="DEMO"
    )
    
    # Create color preview
    color_sorter.create_color_preview(output_dir, color_stats)
    
    print(f"\n=== Demo Complete ===")
    print(f"Check the '{output_dir}' folder to see the results!")
    print(f"Original images are still in '{sample_dir}' folder.")
    
    return output_dir

if __name__ == '__main__':
    demo_color_sorting()
