# Image Extractor

Extract images from PDF, EPUB, MOBI, and comic archive (CBR/CBZ) files with automatic size filtering.

## Features

- ✅ **Multiple format support**: PDF, EPUB, MOBI/AZW/AZW3, CBR, CBZ
- ✅ **Size filtering**: Only extract images above specified dimensions (default: 512x512)
- ✅ **Auto-installs dependencies**: No manual pip installs needed for GUI version
- ✅ **Organized output**: Creates subfolders for each source file
- ✅ **Two interfaces**: GUI for easy use, CLI for batch processing
- ✅ **Concise filenames**: Simple numbered format (0000.jpg, 0001.png, etc.)

## Quick Start

### GUI Version (Recommended for beginners)

**Windows:**
```bash
python extract_images_interactive.py
```

**Linux/Mac:**
```bash
python3 extract_images_interactive.py
```

The GUI will:
1. Auto-install any missing dependencies
2. Provide a file picker to select your file
3. Let you customize minimum dimensions
4. Show live progress as images extract
5. Notify you when complete

### Command-Line Version

**Single file:**
```bash
python extract_images.py "path/to/your/file.pdf"
```

**Entire directory (recursive):**
```bash
python extract_images.py "path/to/directory"
```

**Custom options:**
```bash
python extract_images.py "file.epub" -o my_output_folder -w 1024 -H 1024
```

## Installation

### Option 1: Auto-install (GUI version)
Just run the interactive version - it installs dependencies automatically:
```bash
python extract_images_interactive.py
```

### Option 2: Manual install
```bash
pip install -r requirements.txt
```

## Command-Line Options

```
usage: extract_images.py [-h] [-o OUTPUT] [-w MIN_WIDTH] [-H MIN_HEIGHT] input_path

Arguments:
  input_path            File or directory to process

Options:
  -h, --help            Show this help message
  -o, --output OUTPUT   Output directory (default: extracted_images)
  -w, --min-width       Minimum image width in pixels (default: 512)
  -H, --min-height      Minimum image height in pixels (default: 512)
```

## Examples

### Extract from a single PDF with high-quality filter
```bash
python extract_images.py "book.pdf" -w 2048 -H 2048 -o high_quality_images
```

### Process all ebooks in a folder
```bash
python extract_images.py "D:\BOOKS\art_photography" -o art_images
```

### Extract with custom prefix (GUI)
1. Run `python extract_images_interactive.py`
2. Browse to your file
3. Set "Folder prefix" to "art" or "comic" etc.
4. Click Extract Images

## Output Structure

```
extracted_images/
├── Book_Title_1/
│   ├── 0000.jpg
│   ├── 0001.png
│   ├── 0002.jpg
│   └── ...
├── Book_Title_2/
│   ├── 0000.jpg
│   └── ...
└── Comic_Archive/
    ├── 0000.jpg
    └── ...
```

## Requirements

- Python 3.7+
- PyMuPDF (for PDF support)
- Pillow (for image processing)
- rarfile (for CBR support)

For CBR files, you also need WinRAR or UnRAR installed on your system.

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | .pdf | Full support |
| EPUB | .epub | Full support |
| MOBI | .mobi, .azw, .azw3 | Full support |
| Comic Book Archive (RAR) | .cbr | Requires WinRAR/UnRAR |
| Comic Book Archive (ZIP) | .cbz | Full support |

## Troubleshooting

**"ModuleNotFoundError: No module named..."**
- Run: `pip install -r requirements.txt`
- Or use the GUI version which auto-installs

**"No module named pip" or wrong Python version**
- Your system PATH may point to a different Python (e.g., Inkscape's Python)
- **Solution 1:** Double-click `run_gui_python311.bat` instead
- **Solution 2:** Use Python launcher: `py -3 extract_images_interactive.py`
- **Solution 3:** Run with full path:
  ```
  C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe extract_images_interactive.py
  ```

**CBR files not working**
- Install WinRAR (Windows) or unrar (Linux/Mac)
- Windows: https://www.win-rar.com/
- Linux: `sudo apt install unrar` or `sudo yum install unrar`

**No images extracted**
- Check if images in the file meet minimum dimensions
- Try lowering the threshold: `-w 256 -H 256`
- Some files may have images embedded in non-standard ways

**GUI doesn't open**
- Make sure tkinter is installed (usually comes with Python)
- Test: `python -m tkinter` (should open a test window)
- If missing, reinstall Python with tkinter enabled

## License

Free to use and modify.
