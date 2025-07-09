#!/usr/bin/env python3
"""
Test the enhanced color sorting methods
"""

import color_sorter
import os
from PIL import Image

def create_test_image(color, name, size=(100, 100)):
    """Create a test image with a specific color."""
    img = Image.new('RGB', size, color)
    img.save(f"test_{name}.png")
    return f"test_{name}.png"

def test_color_methods():
    """Test different color analysis methods."""
    print("Creating test images...")
    
    # Create test images
    test_images = []
    test_images.append(create_test_image((50, 50, 50), "dark_gray"))      # Should be Gray now, not Black
    test_images.append(create_test_image((30, 30, 30), "very_dark"))      # Should be Black
    test_images.append(create_test_image((80, 40, 40), "dark_red"))       # Should be Red
    test_images.append(create_test_image((200, 100, 100), "light_red"))   # Should be Red
    test_images.append(create_test_image((100, 150, 200), "light_blue"))  # Should be Blue
    
    methods = ["original", "enhanced", "brightness", "temperature", "center_focus"]
    
    for method in methods:
        print(f"\n=== Testing {method.upper()} method ===")
        for img_file in test_images:
            try:
                category, rgb = color_sorter.analyze_image_color(img_file, method)
                print(f"{img_file:<20} -> {category:<12} (RGB: {rgb})")
            except Exception as e:
                print(f"{img_file:<20} -> ERROR: {e}")
    
    # Clean up test images
    for img_file in test_images:
        if os.path.exists(img_file):
            os.remove(img_file)
    
    print(f"\n=== Key Differences ===")
    print("Enhanced: Better handling of dark colors, more restrictive black threshold")
    print("Original: More images classified as black")
    print("Brightness: Groups by Dark/Medium/Bright/Very Bright")
    print("Temperature: Groups by Warm/Cool/Neutral")
    print("Center Focus: Weighs center pixels more heavily")

if __name__ == "__main__":
    test_color_methods()
