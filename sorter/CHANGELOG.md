# 📋 Sorter - Changelog

All notable changes to the Sorter project will be documented in this file.

## [3.3.0] - 2026-08-07 - "YOLO Face Crop" 🎯

### 🎉 Face-Centered Crop Now Actually Works

#### 🎯 Multi-Backend Face Detection
- **Root cause of the long-standing "mediapipe doesn't work" issue**: mediapipe 0.10.x **removed** the legacy `mp.solutions` API this code targeted — `mp.solutions.face_detection` raises `AttributeError` no matter how many times you reinstall. The replacement Tasks API also requires a separate model download.
- New `FaceDetector` class picks the best available backend automatically:
  1. **YOLO** (`ultralytics` + a `face_yolov8*.pt` model) — best on angled, partial and stylized faces, GPU-accelerated. Auto-discovers `models/ultralytics/bbox/face_yolov8m.pt`, which most ComfyUI users already have for FaceDetailer
  2. **OpenCV Haar cascade** — bundled with opencv, no download, frontal faces only
  3. **Center crop** — final fallback
- The chosen backend is logged, so results are always explainable
- Multi-face images report the count and the confidence of the face used

#### 🖼️ Framing Quality Fix
- Face crops are **never upscaled past native resolution**. Previously a small face (group shots, full-body at distance) could demand ~7x enlargement to hit the 2.2x-face-height framing, producing soft, over-zoomed crops
- A small face now yields a wider *sharp* crop instead of a tight blurry one — measured across test generations, faces land at 31–45% of frame height with zero upscaling
- Crop is biased slightly above face centre so eyes sit nearer the upper third
- New **Face zoom** control (GUI entry + CLI prompt, default 2.2 = head and shoulders; lower is tighter)

### 🛠️ Other Changes
- `requirements.txt`: `mediapipe` replaced with `ultralytics` (optional; Haar fallback needs nothing)
- Verified end to end: a real `.cbr` extracted to 469 face-centered images, all exactly 1024×1024

---

## [3.2.0] - 2026-08-03 - "Universal Archives & Chained Prep" 📚

### 🎉 New Features

#### 📚 Universal Archive Support (Extract Images)
- **Magic-byte format detection** — the real container type is read from the file's bytes, not its extension. Mislabeled files (a ZIP named `.cbr`, a RAR named `.cbz`) now extract correctly instead of failing, which is extremely common for scanned books and comics
- **New formats**: `.cb7` / `.7z` (via `py7zr`), `.cbt` / `.tar`, plus bare `.zip` / `.rar` — many "books" are shared as plain archives
- **RAR backend auto-detection**: probes PATH, then 7-Zip, WinRAR, **PeaZip** (bundled `res\bin\7z` and `res\bin\unrar`), and NanaZip install locations. When no tool exists, the log says exactly what to install instead of failing silently
- Misnamed *documents* reroute too — a PDF or MOBI with an archive extension is detected and sent to the right handler
- Archive entries are extracted in sorted order so page sequence is preserved
- Fixed: two sources with the same stem in one batch (`comic.cbz` + `comic.cbr`) no longer overwrite each other's output folder

#### 🏷️ Civitai Prep Chained to Sorting
- **Sort by Checkpoint**, **Sort by LoRA Stack**, and **Sort by Color** each gained a "🏷️ Civitai Prep" checkbox — sort and embed resource hashes in one operation
- Runs **recursively and in place** across the sorted output tree, so folder structure is preserved and no duplicate copies are created
- CLI equivalents prompt "Run Civitai Prep on sorted output?" after checkpoint and color sorts
- `CivitaiPrep.process_folder()` gained a `recursive` parameter (implies in-place)

### 🛠️ Other Changes
- New dependency: `py7zr` (7z/CB7 support)
- `requirements.txt` notes that RAR support needs an external tool (7-Zip / PeaZip / WinRAR)

---

## [3.1.0] - 2026-08-01 - "Civitai Prep" 🏷️

### 🎉 Major New Feature

#### 🏷️ Civitai Prep (new mode, GUI + CLI)
- Rewrites PNGs with an A1111/Civitai-style `parameters` chunk so **Civitai auto-detects every resource on upload**: checkpoint, LoRAs (with weights), VAE, and embeddings
- Resolves workflow resource names to local model files (exact/stem/fuzzy/prefix matching across nested model folders), computes **AutoV2 hashes** with a persistent cache — each file hashed once, ever
- Optional **Civitai API enrichment** (public `by-hash` endpoint, no key): adds model/version names and AIR identifiers via `Civitai resources` entries; results cached as `.civitai.info` sidecars shared with ComfyUI-Image-Saver; misses negative-cached; degrades gracefully offline
- Primary-checkpoint selection is refiner-aware and filename-hinted — dual-loader workflows pick the model that actually generated the image
- Safe by default: copies into `civitai_ready/` (originals untouched); in-place rewrite and workflow-JSON stripping are opt-in

#### 🧠 Link-Aware Metadata Extraction (shared engine upgrade)
- New `WorkflowTrace` class in `core/metadata_engine.py`, used by Civitai Prep **and** the .txt metadata reports
- Follows ComfyUI node links (`[node_id, slot]`) through selector, primitive, pipe (`easy pipeIn/Out`), and `StringConcatenate` nodes to the literal values
- Prompts traced from the base sampler's own conditioning inputs — supports `CLIPTextEncodeSDXL+`/refiner encoders, keeps positive/negative branches separate, and scores base passes over refiner passes (no more refiner boilerplate in reports)
- **Runtime prompt merging**: prompts from the image's existing `parameters` chunk (where Florence2 captions / wildcard text actually live) are merged with workflow-traced template text
- Sampling parameters and seeds fully dereferenced — no more raw `['1029', 0]` links or refiner steps in .txt reports

---

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