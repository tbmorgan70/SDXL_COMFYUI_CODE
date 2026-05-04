#!/usr/bin/env python3
"""
Extract images from PDF, EPUB, MOBI, CBR/CBZ files.
Filters by minimum dimensions and saves with concise names.
"""

import os
import zipfile
import io
from pathlib import Path
from PIL import Image
import argparse

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("Warning: PyMuPDF not installed. PDF support disabled.")

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False
    print("Warning: rarfile not installed. CBR support disabled.")

try:
    from mobi import Mobi
    HAS_MOBI = False  # mobi library is less reliable, using alternative
except ImportError:
    HAS_MOBI = False


class ImageExtractor:
    def __init__(self, min_width=512, min_height=512, output_dir="extracted_images"):
        self.min_width = min_width
        self.min_height = min_height
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.counter = 0
        self.current_source_dir = None
        self.current_file_counter = 0
        
    def get_safe_filename(self, index, ext):
        """Generate concise filename."""
        return f"{index:04d}.{ext}"
    
    def setup_source_folder(self, source_file):
        """Create a subdirectory for the current source file."""
        # Clean source name: remove extension, special chars, limit length
        base = Path(source_file).stem
        base = "".join(c for c in base if c.isalnum() or c in (' ', '-', '_'))
        base = base.replace(' ', '_')[:50]  # Limit to 50 chars
        
        self.current_source_dir = self.output_dir / base
        self.current_source_dir.mkdir(exist_ok=True)
        self.current_file_counter = 0
    
    def is_image_large_enough(self, img):
        """Check if image meets minimum dimension requirements."""
        return img.width >= self.min_width and img.height >= self.min_height
    
    def save_image(self, img_data):
        """Save image if it meets size requirements."""
        try:
            img = Image.open(io.BytesIO(img_data))
            
            if self.is_image_large_enough(img):
                # Determine format
                fmt = img.format.lower() if img.format else 'png'
                if fmt == 'jpeg':
                    fmt = 'jpg'
                
                filename = self.get_safe_filename(self.current_file_counter, fmt)
                filepath = self.current_source_dir / filename
                
                img.save(filepath)
                print(f"  ✓ Saved: {filename} ({img.width}x{img.height})")
                self.counter += 1
                self.current_file_counter += 1
                return True
            return False
        except Exception as e:
            print(f"  ✗ Error processing image: {e}")
            return False
    
    def extract_from_pdf(self, filepath):
        """Extract images from PDF using PyMuPDF."""
        if not HAS_PYMUPDF:
            print(f"Skipping PDF (PyMuPDF not installed): {filepath.name}")
            return 0
        
        print(f"\nProcessing PDF: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            doc = fitz.open(filepath)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    img_data = base_image["image"]
                    
                    self.save_image(img_data)
            
            doc.close()
        except Exception as e:
            print(f"  Error reading PDF: {e}")
        
        return self.current_file_counter
    
    def extract_from_epub(self, filepath):
        """Extract images from EPUB (ZIP-based)."""
        print(f"\nProcessing EPUB: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for filename in zf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        img_data = zf.read(filename)
                        self.save_image(img_data)
        except Exception as e:
            print(f"  Error reading EPUB: {e}")
        
        return self.current_file_counter
    
    def extract_from_mobi(self, filepath):
        """Extract images from MOBI (try as AZW3/MOBI8 ZIP or parse)."""
        print(f"\nProcessing MOBI: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        # Try treating as ZIP (for MOBI8/AZW3)
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for filename in zf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        img_data = zf.read(filename)
                        self.save_image(img_data)
                return self.current_file_counter
        except:
            pass
        
        # If ZIP approach fails, try parsing MOBI structure
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
                # Look for common image signatures in raw data
                formats = [
                    (b'\xFF\xD8\xFF', '.jpg', b'\xFF\xD9'),  # JPEG
                    (b'\x89PNG\r\n\x1a\n', '.png', b'IEND\xaeB`\x82'),  # PNG
                    (b'GIF89a', '.gif', b'\x00\x3b'),  # GIF
                    (b'GIF87a', '.gif', b'\x00\x3b'),  # GIF
                ]
                
                for sig, ext, end_sig in formats:
                    pos = 0
                    while True:
                        pos = data.find(sig, pos)
                        if pos == -1:
                            break
                        
                        end_pos = data.find(end_sig, pos + len(sig))
                        if end_pos != -1:
                            end_pos += len(end_sig)
                            img_data = data[pos:end_pos]
                            self.save_image(img_data)
                        pos += 1
        except Exception as e:
            print(f"  Error reading MOBI: {e}")
        
        return self.current_file_counter
    
    def extract_from_cbr(self, filepath):
        """Extract images from CBR (RAR archive)."""
        if not HAS_RARFILE:
            print(f"Skipping CBR (rarfile not installed): {filepath.name}")
            return 0
            
        print(f"\nProcessing CBR: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            with rarfile.RarFile(filepath, 'r') as rf:
                for filename in rf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                        img_data = rf.read(filename)
                        self.save_image(img_data)
        except Exception as e:
            print(f"  Error reading CBR: {e}")
        
        return self.current_file_counter
    
    def extract_from_cbz(self, filepath):
        """Extract images from CBZ (ZIP archive)."""
        print(f"\nProcessing CBZ: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for filename in zf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                        img_data = zf.read(filename)
                        self.save_image(img_data)
        except Exception as e:
            print(f"  Error reading CBZ: {e}")
        
        return self.current_file_counter
    
    def process_file(self, filepath):
        """Process a single file based on its extension."""
        ext = filepath.suffix.lower()
        
        if ext == '.pdf':
            return self.extract_from_pdf(filepath)
        elif ext == '.epub':
            return self.extract_from_epub(filepath)
        elif ext in ['.mobi', '.azw', '.azw3']:
            return self.extract_from_mobi(filepath)
        elif ext == '.cbr':
            return self.extract_from_cbr(filepath)
        elif ext == '.cbz':
            return self.extract_from_cbz(filepath)
        else:
            return 0
    
    def process_directory(self, directory):
        """Process all supported files in a directory."""
        dir_path = Path(directory)
        supported_exts = {'.pdf', '.epub', '.mobi', '.azw', '.azw3', '.cbr', '.cbz'}
        
        files = [f for f in dir_path.rglob('*') if f.suffix.lower() in supported_exts]
        
        print(f"Found {len(files)} files to process\n")
        print("=" * 70)
        
        total_images = 0
        for file in files:
            count = self.process_file(file)
            total_images += count
        
        print("\n" + "=" * 70)
        print(f"Extraction complete!")
        print(f"Total images extracted: {self.counter}")
        print(f"Output directory: {self.output_dir.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract images from PDF, EPUB, MOBI, CBR/CBZ files"
    )
    parser.add_argument(
        'input_path',
        help='File or directory to process'
    )
    parser.add_argument(
        '-o', '--output',
        default='extracted_images',
        help='Output directory for extracted images (default: extracted_images)'
    )
    parser.add_argument(
        '-w', '--min-width',
        type=int,
        default=512,
        help='Minimum image width in pixels (default: 512)'
    )
    parser.add_argument(
        '-H', '--min-height',
        type=int,
        default=512,
        help='Minimum image height in pixels (default: 512)'
    )
    
    args = parser.parse_args()
    
    extractor = ImageExtractor(
        min_width=args.min_width,
        min_height=args.min_height,
        output_dir=args.output
    )
    
    input_path = Path(args.input_path)
    
    if input_path.is_file():
        # Process single file
        print(f"Processing single file: {input_path.name}")
        print("=" * 70)
        count = extractor.process_file(input_path)
        print("\n" + "=" * 70)
        print(f"Extraction complete!")
        print(f"Total images extracted: {extractor.counter}")
        print(f"Output directory: {extractor.output_dir.absolute()}")
    elif input_path.is_dir():
        # Process directory
        extractor.process_directory(input_path)
    else:
        print(f"Error: {input_path} is not a valid file or directory")


if __name__ == "__main__":
    main()
