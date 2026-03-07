#!/usr/bin/env python3
"""
Text File Sorter Module

Simple text file sorting functionality with placeholder replacement.
"""

import os
import shutil


def sort_text_files(directory, placeholders, move=False):
    """
    Sort text files based on placeholders.
    
    Args:
        directory: Source directory containing text files
        placeholders: Dict with placeholder values (A, B, C, D)
        move: Whether to move files instead of copying
    """
    print(f"Sorting text files in: {directory}")
    print(f"Placeholders: {placeholders}")
    print(f"Move files: {move}")
    
    # This is a basic placeholder implementation
    # You can expand this based on your actual text sorting needs
    
    text_files = [f for f in os.listdir(directory) 
                  if f.lower().endswith(('.txt', '.md', '.log'))]
    
    if not text_files:
        print("No text files found to sort.")
        return
    
    # Create sorted folder
    sorted_dir = os.path.join(directory, "text_sorted")
    os.makedirs(sorted_dir, exist_ok=True)
    
    print(f"Found {len(text_files)} text files to process...")
    
    for filename in text_files:
        src_path = os.path.join(directory, filename)
        dest_path = os.path.join(sorted_dir, filename)
        
        # Ensure unique filename
        counter = 1
        while os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            dest_path = os.path.join(sorted_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            if move:
                shutil.move(src_path, dest_path)
                action = "Moved"
            else:
                shutil.copy2(src_path, dest_path)
                action = "Copied"
            
            print(f"[{action}] {filename}")
            
        except Exception as e:
            print(f"[Error] Failed to process {filename}: {e}")
    
    print(f"Text file sorting complete. Files processed to: {sorted_dir}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sort text files')
    parser.add_argument('directory', help='Directory containing text files')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying')
    
    args = parser.parse_args()
    
    # Default placeholders for standalone use
    placeholders = {'A': None, 'B': None, 'C': None, 'D': None}
    
    sort_text_files(args.directory, placeholders, move=args.move)
