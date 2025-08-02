# Sorter 2.0 User Guide

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Sorting Operations](#sorting-operations)
4. [User Interface Options](#user-interface-options)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

## Installation

### Requirements
- Python 3.7 or higher
- Windows, macOS, or Linux

### Basic Installation
1. Clone or download the Sorter 2.0 files
2. Open a terminal/command prompt in the `sorter_v2` directory
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Optional Enhanced GUI
For the modern CustomTkinter interface, install:
```bash
pip install customtkinter
```

## Quick Start

### Using the Graphical Interface
1. **Standard GUI (No extra dependencies):**
   ```bash
   python gui_standard.py
   ```

2. **Modern GUI (Requires CustomTkinter):**
   ```bash
   python gui.py
   ```

### Using the Command Line
```bash
python main.py
```

## Sorting Operations

### 1. Sort by Base Checkpoint
**Most Popular Feature** - Organizes images by their AI model checkpoint.

**What it does:**
- Reads ComfyUI PNG metadata to identify the base checkpoint used
- Creates folders named after each checkpoint
- Copies images to their respective checkpoint folders
- Preserves original files in place

**Use case:** Perfect for organizing large collections of AI-generated images by the model that created them.

### 2. Metadata Search & Filter
Search and filter images based on their ComfyUI metadata.

**Features:**
- Search by prompt keywords
- Filter by checkpoint name
- Filter by sampling method
- Search by any metadata field
- Copy matching images to a results folder

**Use case:** Finding specific images with certain prompts or settings.

### 3. Color-Based Sorting
Analyze and sort images by dominant colors.

**Options:**
- **Basic colors:** Red, Green, Blue, etc.
- **Advanced colors:** Specific color ranges and saturation levels
- **Custom color analysis:** Define your own color categories

**Use case:** Organizing images by color themes or palettes.

### 4. Image Flattening
Organize images into a flat structure by renaming them with metadata prefixes.

**What it does:**
- Analyzes each image's metadata
- Renames files with descriptive prefixes
- Moves all images to a single directory
- Maintains searchable filenames

**Use case:** Converting complex folder structures into searchable flat hierarchies.

## User Interface Options

### Standard GUI Features
- **Folder Selection:** Browse and select source and destination folders
- **Operation Selection:** Choose from all sorting operations
- **Progress Tracking:** Real-time progress bars and status updates
- **Logging:** View detailed operation logs
- **Results Display:** See operation summaries and statistics

### Modern GUI Additional Features (CustomTkinter)
- **Dark/Light Themes:** Switch between modern appearance modes
- **Enhanced Styling:** Rounded buttons and modern visual design
- **Improved Responsiveness:** Smoother animations and interactions

### Command Line Interface
- **Interactive Menu:** Step-by-step operation selection
- **Batch Processing:** Process multiple operations in sequence
- **Detailed Logging:** Comprehensive console output
- **Statistics:** Operation timing and success rates

## Configuration

### Automatic Configuration
Sorter 2.0 automatically:
- Detects image file types (PNG, JPG, JPEG, etc.)
- Creates necessary output directories
- Handles duplicate filenames
- Manages logging and statistics

### Custom Settings
You can modify behavior by editing the source files:
- `SUPPORTED_EXTENSIONS` in metadata_engine.py for file types
- Color definitions in color_sorter.py
- Logging levels in diagnostics.py

## Troubleshooting

### Common Issues

**"No images found"**
- Verify the source folder contains supported image files (PNG, JPG, JPEG)
- Check that files aren't in use by other programs

**"Permission denied"**
- Ensure you have write permissions to the destination folder
- Close any image viewers that might have files open

**"Module not found"**
- Install required dependencies: `pip install -r requirements.txt`
- For CustomTkinter GUI: `pip install customtkinter`

**GUI won't start**
- Try the standard GUI: `python gui_standard.py`
- Check Python version: requires Python 3.7+

### Performance Tips

**For large image collections (1000+ images):**
- Use the command-line interface for better performance
- Process in smaller batches if memory is limited
- Close other applications to free up system resources

**For faster processing:**
- Use SSD storage when possible
- Ensure adequate free disk space (2x the size of your image collection)

## Advanced Usage

### Batch Operations
You can chain multiple operations by running the command-line interface multiple times:

1. First, sort by checkpoint to organize by model
2. Then, use metadata search to find specific themes
3. Finally, apply color sorting to the results

### Custom Workflows
Create custom sorting workflows by:
1. Using metadata search to create initial filters
2. Applying color sorting to the filtered results
3. Using image flattening for final organization

### Integration with Other Tools
Sorter 2.0 works well with:
- **ComfyUI:** Maintains all original metadata
- **Image viewers:** Organized folders work with any image browser
- **Backup tools:** Clean folder structures are easier to backup

## Tips for Best Results

1. **Start with small test batches** to verify settings
2. **Always backup your images** before large operations
3. **Use meaningful destination folder names**
4. **Review the logs** to understand what was processed
5. **Combine operations** for complex organization needs

## Getting Help

If you encounter issues:
1. Check the operation logs for detailed error messages
2. Try the command-line interface for more detailed output
3. Verify file permissions and disk space
4. Test with a small sample of images first

For technical support, include:
- Your operating system
- Python version
- The exact error message
- Steps to reproduce the issue
