# 🚀 Sorter 2.0 - Production Release

**Advanced ComfyUI Image Organizer - Clean, Fast, Reliable**

## Quick Start

### GUI Version (Recommended)
```bash
python gui.py
```

### Command Line Version
```bash
python main.py
```

## Features

### 🎯 Sort by Base Checkpoint
- Organizes images by their base model (SDXL, Pony, etc.)
- Smart model detection from metadata
- Optional LoRA stack grouping
- **Your #1 priority feature!**

### 🔍 Search & Sort by Metadata
- Find images by LoRAs, prompts, settings, etc.
- Flexible search modes (ANY, ALL, EXACT)
- Case-sensitive options

### 🌈 Sort by Color
- Organizes by dominant colors (red, blue, green, etc.)
- Supports all image formats (PNG, JPG, GIF, BMP, TIFF, WebP)
- Configurable dark threshold

### 📂 Flatten Image Folders
- Consolidates nested folders into one directory
- Smart duplicate handling with automatic renaming
- Optional empty folder cleanup

### 📊 Session Logs
- View detailed logs of previous operations
- Error tracking and performance statistics
- Comprehensive audit trail

## Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   - GUI: `python gui.py`
   - CLI: `python main.py`

## GUI Features

- **Compact Design:** 750x700 window fits perfectly on any screen
- **Real-time Progress:** Live progress tracking with auto-close on completion
- **Dark Theme:** Modern CustomTkinter interface
- **Smart Confirmations:** Detailed operation previews before execution
- **Error Handling:** Clear error messages and logging

## Requirements

- Python 3.7+
- CustomTkinter (for GUI)
- Pillow (for image processing)
- Standard libraries: json, pathlib, threading, queue

## File Operations

- **Copy Mode (Default):** Preserves original files
- **Move Mode:** Transfers files to new locations
- **Metadata Files:** Optional .txt files with image details
- **Smart Renaming:** Handles filename conflicts automatically

## Supported Formats

- **Images:** PNG, JPG, JPEG, GIF, BMP, TIFF, WebP
- **Metadata:** ComfyUI PNG metadata extraction
- **Output:** Organized folder structure with optional metadata files

## Logging

All operations are logged to `sort_logs/` directory:
- Detailed operation logs
- Error tracking
- Performance statistics
- File processing history

---

**Built for Production Use - Reliable, Fast, User-Friendly**

*Clean codebase extracted from development version - ready for deployment*
