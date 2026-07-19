# 📋 Sorter - Changelog

All notable changes to the Sorter project will be documented in this file.

## [3.0.0] - 2026-07-12 - "Extract, Triage & Color Engine" 🎨

### 🎉 Major New Features

#### 📦 Extract Images (new mode)
- Extract images from **PDF, EPUB, MOBI/AZW3, CBR, CBZ** files — single file, multi-select, or whole directory
- Minimum-dimension filtering with per-source subfolders and optional folder prefix
- **13 auto-crop presets** covering SDXL training sizes (512/768/1024), social (1:1, 4:5, 9:16), landscape (16:9), classic (4:3, 3:2), ultrawide (21:9), plus custom dimensions
- **Face-centered cropping** via MediaPipe (largest face, padded framing) with automatic center-crop fallback
- Optional **chain to sort**: run Checkpoint / Color / Flatten on the extracted output in one step
- Supersedes the standalone `ImageExtractor/` tool (now deprecated)

#### 🖼️ Manual Sort — Visual Triage (new mode)
- Paginated thumbnail gallery with background loading (handles 1000+ images)
- Full-size viewer: **←/→** navigate, **1-4** assign bucket + auto-advance, **0** clear, **Del** = Trash, **Esc** back to gallery
- Up to 3 custom-named buckets plus an always-present **Trash** bucket
- Colored borders + live per-bucket counts; Execute moves images into labeled subfolders
- Unassigned images stay in place — triage across multiple sittings safely

#### 🌈 Sort by Color — engine rewrite
- Replaced RGB-swatch-distance matching with **HSV pixel voting**: every pixel is bucketed by hue/saturation/value rules, the image takes the plurality color
- **Chromatic priority**: black/white/gray only win when they exceed a *Neutral dominance* share — a subject on a dark background now sorts by the subject's color
- Dark saturated colors (navy, deep red) now classify correctly instead of falling into Black
- New **Cyan** category; smarter Brown/Pink rules
- Four intuitive tuning sliders: **Black level**, **White level**, **Color purity**, **Neutral dominance** (replaces the old "dark threshold")
- Per-image vote breakdown logged (e.g. `Black 54%, Red 31% → Red`) so results are explainable

### 🛠️ Other Changes
- New dependencies: `PyMuPDF`, `rarfile` (extraction); `mediapipe`, `numpy` (optional, face crop)
- New modules: `sorters/image_extractor.py`, `sorters/manual_sorter.py`
- CLI menu expanded to include Extract Images

---

## [2.4.0] - 2024-12-13 - "Metadata Preservation Update" 🗂️

### 🔥 Major Enhancement

#### 📄 Automatic Metadata File Preservation
- **ENHANCED FILE OPERATIONS**: All sorters now automatically move `.txt` metadata files with PNG images
- **Smart Detection**: Automatically finds and handles associated metadata files
- **No More Orphaned Files**: Flatten mode no longer leaves metadata behind in empty folders
- **Comprehensive Logging**: All metadata file operations are tracked and logged
- **Backward Compatible**: All existing functionality preserved while adding metadata support

**Problem Solved**: Previously when running "Flatten" on a folder that had been sorted by base model, it would leave empty folders with just metadata files instead of moving both the images AND their metadata together.

**Technical Implementation**:
- New `FileOperationsHandler` class in `core/file_operations.py`
- Enhanced error handling and progress reporting
- Updated all sorters: Checkpoint, LoRA Stack, Search, Color, and Flatten
- Metadata files detected by `.txt` extension matching PNG basename

### 🛠️ What Changed
- **All file move/copy operations** now include associated metadata files
- **Empty folder cleanup** now works properly after flattening sorted folders  
- **Enhanced logging** shows both image and metadata file operations
- **No breaking changes** - all existing features work exactly the same

---

## [2.3.0] - 2025-10-08 - "Workflow Enhancement Update" ✨

### 🎉 Major New Features

#### 🧬 LoRA Stack Sorting
- **NEW SORTING MODE**: "Sort by LoRA Stack"
- Groups images by **identical LoRA combinations** only
- Ignores checkpoints, VAEs, and CLIP strength variations
- Perfect for finding images with the same style effects
- **Windows Path Optimization**: Smart folder naming with MD5 hashing for long names
- **Metadata Caching**: Optimized performance to avoid double-extraction
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

**Use Case**: Find all images that use the same combination of LoRAs regardless of which checkpoint was used.

#### 📄 Metadata-Only Generation
- **NEW MODE**: "Generate Metadata"
- Extract comprehensive metadata **without moving or organizing files**
- Creates detailed .txt files alongside original images
- **Non-Disruptive**: Perfect for analysis without changing file structure
- **Batch Processing**: Handles large collections with progress tracking
- **Comprehensive Data**: Includes checkpoints, LoRAs, prompts, settings, and technical details

**Use Case**: Catalog your existing collection or analyze workflow patterns without reorganizing files.

#### 📁 Auto-Open Output Folder
- **NEW UI FEATURE**: "📁 Open Output Folder" button
- Automatically appears after **every successful operation**
- **Cross-Platform**: Uses native file managers (Explorer, Finder, etc.)
- **Smart Detection**: Only shows when output directory exists
- **Instant Access**: One-click access to your organized results

**Use Case**: Immediately view and work with your sorted images without manual navigation.

### 🛠️ Technical Improvements

#### Performance Enhancements
- **Metadata Caching**: Eliminated redundant metadata extraction during LoRA sorting
- **Path Optimization**: Resolved Windows 260-character path limit issues
- **Memory Efficiency**: Improved handling of large image collections

#### Error Handling
- **Robust Path Handling**: Windows path length limitations automatically handled
- **File Existence Checks**: Prevents processing of missing files from partial runs
- **Detailed Error Logging**: Enhanced debugging information for troubleshooting

#### Code Architecture
- **New Sorter Module**: `lora_stack_sorter.py` - Dedicated LoRA stack processing
- **Enhanced Metadata Generator**: Extended for standalone metadata extraction
- **Cross-Platform File Operations**: Unified folder opening across all OS platforms

### 🎯 User Experience Improvements
- **Enhanced GUI**: New dropdown options with clear descriptions
- **Better Progress Tracking**: Real-time updates for all new operations
- **Comprehensive Logging**: Detailed operation summaries for all new features
- **Smart Validation**: Prevents common user errors with better input validation

---

## [2.2.0] - Previous Release
### Features
- Sort by Base Checkpoint
- Search & Sort by Metadata  
- Color-based sorting
- Image flattening
- Session logs

---

## 🚀 What's Next?

### Planned Features
- **Integration with Builder Suite**: Connect LoRA analysis with HTML dashboards
- **Advanced LoRA Analytics**: Statistics on LoRA usage patterns
- **Batch Metadata Export**: JSON/CSV export options for large-scale analysis
- **Custom LoRA Stack Filters**: Advanced filtering and search within LoRA groups

### Feedback Welcome!
Found the new features useful? Have suggestions for improvements? Let us know!

---

## 📊 Version Summary

| Version | Release Date | Key Features |
|---------|-------------|--------------|
| **2.3.0** | 2025-10-08 | 🧬 LoRA Stack Sorting, 📄 Metadata-Only Mode, 📁 Auto-Open Folder |
| 2.0.0 | Previous | Base functionality, Checkpoint sorting, Color sorting |

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.*