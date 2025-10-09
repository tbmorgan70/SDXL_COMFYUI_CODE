# 📋 Sorter 2.0 - Changelog

All notable changes to the Sorter 2.0 project will be documented in this file.

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
| 2.2.0 | Previous | Base functionality, Checkpoint sorting, Color sorting |

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.*