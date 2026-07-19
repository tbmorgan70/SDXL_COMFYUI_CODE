# 🚀 Sorter 3.0 - Production Release

**Advanced ComfyUI Image Organizer - Clean, Fast, Reliable**

> ⭐ **Part of SDXL_COMFYUI_CODE v3.1**  
> This is the main production sorter tool. For other tools, see the [main repository README](../README.md).

## 🆕 What's New in 3.0

- **📦 Extract Images** — pull images out of PDF/EPUB/MOBI/CBR/CBZ files with auto-crop presets (SDXL training sizes, social ratios, and more) and optional face-centered cropping; chain straight into sorting
- **🖼️ Manual Sort (Triage)** — keyboard-driven visual gallery: view full-size, press 1-4 to bucket each image into custom-named folders (plus Trash), then execute the moves
- **🌈 Color engine rewrite** — HSV pixel voting with chromatic priority; dark images classify correctly and four intuitive sliders replace the old dark threshold

See [CHANGELOG.md](CHANGELOG.md) for full details.

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

### 🧬 Sort by LoRA Stack ✨ *NEW!*
- **Groups images by identical LoRA combinations**
- Ignores checkpoints, VAEs, and CLIP strength variations
- Perfect for finding images with the same style effects
- Windows path-length optimized with smart folder naming
- Handles complex multi-LoRA workflows seamlessly

### 📄 Generate Metadata Only ✨ *NEW!*
- **Extract metadata without moving or organizing images**
- Creates comprehensive .txt files alongside images
- Perfect for analysis and cataloging workflows
- No file disruption - pure metadata extraction
- Batch processing with progress tracking

### 📁 Auto-Open Output Folder ✨ *NEW!*
- **Automatically opens result folder after operations**
- Cross-platform support (Windows, macOS, Linux)
- Instant access to your organized images
- Smart detection of operation completion

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

## 🚀 New Feature Guide

### 🧬 LoRA Stack Sorting
Perfect for finding images that use identical LoRA combinations:

1. Select **"Sort by LoRA Stack"** from the dropdown
2. Choose your ComfyUI output folder
3. Images will be grouped by their exact LoRA combinations:
   ```
   output/lora_sorted/
   ├── DetailTweaker_and_FilmGrain/     # Images with these 2 LoRAs
   ├── CyberPunk_and_Neon_and_Glitch/ # Images with these 3 LoRAs  
   ├── Glitchcore_SDXL/                # Images with this 1 LoRA
   └── no_loras/                       # Images without LoRAs
   ```

### 📄 Metadata-Only Mode
Extract comprehensive metadata without disrupting your file organization:

1. Select **"Generate Metadata"** from the dropdown
2. Choose source folder with your images
3. Creates detailed .txt files alongside each image:
   ```
   my_image.png
   my_image.txt  ← Contains: checkpoint, LoRAs, prompts, settings
   ```

### 📁 Auto-Open Results
Every operation now ends with the **"📁 Open Output Folder"** button:
- Automatically appears after successful operations
- Cross-platform folder opening (Windows Explorer, macOS Finder, Linux file manager)
- Instant access to your organized results

## 📚 Documentation

### Sorter-Specific Documentation
- **✨ [FEATURE_SHOWCASE.md](FEATURE_SHOWCASE.md)** - Comprehensive guide to all features with examples
- **📋 [CHANGELOG.md](CHANGELOG.md)** - Complete version history and new features
- **🔧 [UPDATE_NOTES.md](UPDATE_NOTES.md)** - Update and migration information
- **🧪 [FEATURE_METADATA_PRESERVATION.md](FEATURE_METADATA_PRESERVATION.md)** - Metadata handling details

### Repository Documentation
- **[Main README](../README.md)** - Repository overview with documentation navigator
- **[ARCHITECTURE.md](../docs/ARCHITECTURE.md)** - System design and sorter architecture
- **[DEVELOPMENT_GUIDE.md](../docs/DEVELOPMENT_GUIDE.md)** - Setup, coding standards, testing patterns
- **[KNOWLEDGE_INDEX.md](../KNOWLEDGE_INDEX.md)** - Complete documentation index

### Other Tools in This Repository
- **[Builder Suite](../builder/README.md)** - Prompt generation tools (13 HTML builders)
- **[Modular Builder](../modular_builder/README.md)** - CSV-based category management
- **[CivitAI Converter](../civitai_converter/COMFYUI_TO_CIVITAI_README.md)** - Workflow format converter

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

**Last Updated:** July 12, 2026 (v3.0.0)  
**Part of:** SDXL_COMFYUI_CODE v3.1 - Sorter 3.0

*Clean codebase extracted from development version - ready for deployment*
