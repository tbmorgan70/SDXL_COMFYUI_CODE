#!/usr/bin/env python3
"""
Interactive Image Extractor
Auto-installs dependencies and provides GUI for easy use.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_and_install_packages():
    """Check for required packages and install if missing."""
    required_packages = {
        'PIL': 'Pillow',
        'fitz': 'PyMuPDF',
        'rarfile': 'rarfile'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("Installing required packages...")
        print(f"Missing: {', '.join(missing_packages)}")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--quiet'
            ] + missing_packages)
            print("✓ All packages installed successfully!\n")
        except subprocess.CalledProcessError:
            print("Error installing packages. Please run manually:")
            print(f"  pip install {' '.join(missing_packages)}")
            sys.exit(1)

# Ensure dependencies are installed
check_and_install_packages()

# Now import the rest
import zipfile
import io
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False


class ImageExtractor:
    def __init__(self, min_width=512, min_height=512, output_dir="extracted_images", folder_prefix=""):
        self.min_width = min_width
        self.min_height = min_height
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.folder_prefix = folder_prefix
        self.counter = 0
        self.current_source_dir = None
        self.current_file_counter = 0
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def log(self, message):
        """Log message to console or callback."""
        print(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def get_safe_filename(self, index, ext):
        """Generate concise filename."""
        return f"{index:04d}.{ext}"
    
    def setup_source_folder(self, source_file):
        """Create a subdirectory for the current source file."""
        base = Path(source_file).stem
        base = "".join(c for c in base if c.isalnum() or c in (' ', '-', '_'))
        base = base.replace(' ', '_')[:50]
        
        if self.folder_prefix:
            base = f"{self.folder_prefix}_{base}"
        
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
                fmt = img.format.lower() if img.format else 'png'
                if fmt == 'jpeg':
                    fmt = 'jpg'
                
                filename = self.get_safe_filename(self.current_file_counter, fmt)
                filepath = self.current_source_dir / filename
                
                img.save(filepath)
                self.log(f"  ✓ Saved: {filename} ({img.width}x{img.height})")
                self.counter += 1
                self.current_file_counter += 1
                return True
            return False
        except Exception as e:
            self.log(f"  ✗ Error processing image: {e}")
            return False
    
    def extract_from_pdf(self, filepath):
        """Extract images from PDF using PyMuPDF."""
        if not HAS_PYMUPDF:
            self.log(f"Skipping PDF (PyMuPDF not installed): {filepath.name}")
            return 0
        
        self.log(f"\nProcessing PDF: {filepath.name}")
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
            self.log(f"  Error reading PDF: {e}")
        
        return self.current_file_counter
    
    def extract_from_epub(self, filepath):
        """Extract images from EPUB (ZIP-based)."""
        self.log(f"\nProcessing EPUB: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for filename in zf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        img_data = zf.read(filename)
                        self.save_image(img_data)
        except Exception as e:
            self.log(f"  Error reading EPUB: {e}")
        
        return self.current_file_counter
    
    def extract_from_mobi(self, filepath):
        """Extract images from MOBI (try as AZW3/MOBI8 ZIP or parse)."""
        self.log(f"\nProcessing MOBI: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
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
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
                formats = [
                    (b'\xFF\xD8\xFF', '.jpg', b'\xFF\xD9'),
                    (b'\x89PNG\r\n\x1a\n', '.png', b'IEND\xaeB`\x82'),
                    (b'GIF89a', '.gif', b'\x00\x3b'),
                    (b'GIF87a', '.gif', b'\x00\x3b'),
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
            self.log(f"  Error reading MOBI: {e}")
        
        return self.current_file_counter
    
    def extract_from_cbr(self, filepath):
        """Extract images from CBR (RAR archive)."""
        if not HAS_RARFILE:
            self.log(f"Skipping CBR (rarfile not installed): {filepath.name}")
            return 0
            
        self.log(f"\nProcessing CBR: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            with rarfile.RarFile(filepath, 'r') as rf:
                for filename in rf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                        img_data = rf.read(filename)
                        self.save_image(img_data)
        except Exception as e:
            self.log(f"  Error reading CBR: {e}")
        
        return self.current_file_counter
    
    def extract_from_cbz(self, filepath):
        """Extract images from CBZ (ZIP archive)."""
        self.log(f"\nProcessing CBZ: {filepath.name}")
        self.setup_source_folder(filepath.name)
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for filename in zf.namelist():
                    lower = filename.lower()
                    if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                        img_data = zf.read(filename)
                        self.save_image(img_data)
        except Exception as e:
            self.log(f"  Error reading CBZ: {e}")
        
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


class ImageExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Extractor")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        
        # Variables
        self.file_path = tk.StringVar()
        self.output_dir = tk.StringVar(value="extracted_images")
        self.folder_prefix = tk.StringVar()
        self.min_width = tk.IntVar(value=512)
        self.min_height = tk.IntVar(value=512)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="📷 Image Extractor", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # File Selection
        file_frame = tk.LabelFrame(self.root, text="File Selection", padx=10, pady=10)
        file_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Label(file_frame, text="Select file:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(file_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=5)
        tk.Button(file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=2)
        
        # Options
        options_frame = tk.LabelFrame(self.root, text="Options", padx=10, pady=10)
        options_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Label(options_frame, text="Output folder:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(options_frame, textvariable=self.output_dir, width=30).grid(row=0, column=1, padx=5)
        
        tk.Label(options_frame, text="Folder prefix (optional):").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(options_frame, textvariable=self.folder_prefix, width=30).grid(row=1, column=1, padx=5)
        
        tk.Label(options_frame, text="Minimum width (px):").grid(row=2, column=0, sticky="w", pady=5)
        tk.Spinbox(options_frame, from_=64, to=4096, textvariable=self.min_width, width=28).grid(row=2, column=1, padx=5)
        
        tk.Label(options_frame, text="Minimum height (px):").grid(row=3, column=0, sticky="w", pady=5)
        tk.Spinbox(options_frame, from_=64, to=4096, textvariable=self.min_height, width=28).grid(row=3, column=1, padx=5)
        
        # Extract Button
        self.extract_btn = tk.Button(self.root, text="Extract Images", command=self.extract_images,
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                     padx=20, pady=10)
        self.extract_btn.pack(pady=10)
        
        # Progress
        progress_frame = tk.LabelFrame(self.root, text="Progress", padx=10, pady=10)
        progress_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.progress_text = tk.Text(progress_frame, height=12, width=70, state="disabled")
        scrollbar = tk.Scrollbar(progress_frame, command=self.progress_text.yview)
        self.progress_text.config(yscrollcommand=scrollbar.set)
        
        self.progress_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select file to extract images from",
            filetypes=[
                ("All supported", "*.pdf *.epub *.mobi *.azw *.azw3 *.cbr *.cbz"),
                ("PDF files", "*.pdf"),
                ("EPUB files", "*.epub"),
                ("MOBI files", "*.mobi *.azw *.azw3"),
                ("Comic archives", "*.cbr *.cbz"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path.set(filename)
    
    def log(self, message):
        """Add message to progress text."""
        self.progress_text.config(state="normal")
        self.progress_text.insert("end", message + "\n")
        self.progress_text.see("end")
        self.progress_text.config(state="disabled")
        self.root.update()
    
    def extract_images(self):
        filepath = self.file_path.get()
        
        if not filepath:
            messagebox.showerror("Error", "Please select a file!")
            return
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", "File does not exist!")
            return
        
        # Clear progress
        self.progress_text.config(state="normal")
        self.progress_text.delete("1.0", "end")
        self.progress_text.config(state="disabled")
        
        # Disable button
        self.extract_btn.config(state="disabled")
        
        try:
            # Create extractor
            extractor = ImageExtractor(
                min_width=self.min_width.get(),
                min_height=self.min_height.get(),
                output_dir=self.output_dir.get(),
                folder_prefix=self.folder_prefix.get()
            )
            extractor.set_progress_callback(self.log)
            
            self.log("=" * 70)
            
            # Process file
            count = extractor.process_file(Path(filepath))
            
            self.log("\n" + "=" * 70)
            self.log(f"✓ Extraction complete!")
            self.log(f"Total images extracted: {extractor.counter}")
            self.log(f"Output directory: {extractor.output_dir.absolute()}")
            
            messagebox.showinfo("Success", 
                              f"Extracted {extractor.counter} images!\n\nSaved to: {extractor.output_dir.absolute()}")
        
        except Exception as e:
            self.log(f"\n✗ Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            # Re-enable button
            self.extract_btn.config(state="normal")


def main():
    root = tk.Tk()
    app = ImageExtractorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
