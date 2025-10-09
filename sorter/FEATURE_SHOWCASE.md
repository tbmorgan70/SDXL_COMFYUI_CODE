# 🚀 Sorter 2.0 - Feature Showcase

**Quick reference for all the powerful features available in Sorter 2.0**

---

## 🧬 LoRA Stack Sorting ⭐ *FLAGSHIP FEATURE*

### What It Does
Groups images by **identical LoRA combinations**, ignoring checkpoints, VAEs, and CLIP strengths.

### Perfect For
- Finding images with the same style effects
- Analyzing your LoRA usage patterns  
- Organizing by creative themes rather than technical settings
- Workflow optimization and duplicate style detection

### Example Results
```
output/lora_sorted/
├── DetailTweaker_and_FilmGrain_and_Vintage/     # 15 images
├── CyberPunk_and_Neon_and_Glitch/              # 23 images  
├── Glitchcore_SDXL/                            # 8 images
├── Breast_Size_Slider_and_Curvy_Natural_4f8a1b2c/ # Long names get hashed
└── no_loras/                                   # 31 images
```

### Technical Features
- ✅ **Windows Path Optimization**: Handles long LoRA names with smart truncation + hashing
- ✅ **Metadata Caching**: Optimized performance, no double-extraction
- ✅ **Cross-Platform**: Works on Windows, macOS, Linux
- ✅ **Progress Tracking**: Real-time updates during processing

---

## 📄 Metadata-Only Generation ⭐ *ANALYSIS POWERHOUSE*

### What It Does
Extracts comprehensive metadata and creates .txt files **without moving or organizing images**.

### Perfect For
- Cataloging existing collections
- Analyzing workflow patterns
- Creating searchable metadata archives
- Research and documentation
- Backup metadata before reorganizing

### What Gets Extracted
```
📄 Generated .txt file contains:
├── 🎯 Base Checkpoint: "realvisxlV50_v50Bakedvae.safetensors"
├── 🧬 LoRAs Used: "DetailTweaker.safetensors", "FilmGrain.safetensors"  
├── 💬 Positive Prompt: "masterpiece, best quality, 1girl..."
├── 🚫 Negative Prompt: "worst quality, low quality..."
├── ⚙️ Generation Settings: Steps, CFG, Sampler, etc.
├── 🖼️ Image Info: Dimensions, file size, creation date
└── 🔗 Workflow: Full ComfyUI node structure
```

### Example Output
```
my_image.png          ← Original untouched
my_image.txt          ← Comprehensive metadata
another_image.png     ← Original untouched  
another_image.txt     ← Comprehensive metadata
```

---

## 📁 Auto-Open Output Folder ⭐ *CONVENIENCE CHAMPION*

### What It Does
Automatically provides a "📁 Open Output Folder" button after **every successful operation**.

### Perfect For
- Instant access to organized results
- Streamlined workflow - no manual navigation
- Quick verification of sorting results
- Immediate access for further processing

### Cross-Platform Support
- 🪟 **Windows**: Opens in Windows Explorer
- 🍎 **macOS**: Opens in Finder  
- 🐧 **Linux**: Opens in default file manager

### Smart Behavior
- ✅ Only appears when output directory exists
- ✅ Automatically detects successful operations
- ✅ One-click folder opening
- ✅ Handles network drives and complex paths

---

## 🎯 Classic Features (Still Amazing!)

### Sort by Base Checkpoint
- **SDXL Detection**: Automatically identifies SDXL vs other models
- **Smart Grouping**: Organizes by actual checkpoint used
- **LoRA Integration**: Optional grouping by LoRA combinations within checkpoints

### Search & Sort by Metadata
- **Flexible Search**: Find by LoRAs, prompts, settings, any metadata
- **Search Modes**: ANY (contains any term), ALL (contains all terms), EXACT (exact match)
- **Case Sensitivity**: Toggle case-sensitive searching
- **Comprehensive Results**: Copies matching images to organized folders

### Sort by Color
- **HSV Analysis**: Accurate color classification using HSV color space
- **Multi-Format**: PNG, JPG, GIF, BMP, TIFF, WebP support
- **Dark Threshold**: Configurable sensitivity for dark images
- **Visual Preview**: Generates color distribution charts

### Flatten Image Folders
- **Recursive Processing**: Handles deeply nested folder structures
- **Smart Renaming**: Automatic conflict resolution with sequential numbering
- **Empty Cleanup**: Optional removal of empty folders after flattening
- **Preserve Metadata**: Maintains creation dates and file properties

---

## 🎨 User Experience Features

### Modern GUI
- **CustomTkinter Interface**: Modern, dark-themed design
- **Compact Layout**: 750x700 window fits any screen
- **Real-Time Progress**: Live updates with progress bars
- **Auto-Close Options**: Configurable window behavior on completion

### Comprehensive Logging
- **Session Logs**: Detailed logs of every operation
- **Error Tracking**: Clear error messages and troubleshooting info
- **Performance Stats**: Processing time and file count summaries
- **Audit Trail**: Complete record of all file operations

### Smart File Handling
- **Copy vs Move**: Choose whether to preserve originals
- **Duplicate Detection**: Automatic handling of filename conflicts
- **Metadata Files**: Optional .txt files with comprehensive image data
- **Batch Processing**: Optimized for large collections (100s-1000s of images)

---

## 💡 Pro Tips

### LoRA Stack Sorting
- Use this to find your most successful LoRA combinations
- Great for identifying overused or underused LoRAs
- Perfect for creating style-consistent image sets

### Metadata-Only Mode
- Run this first to catalog your collection before reorganizing
- Use the generated .txt files for advanced searching and analysis
- Perfect for backing up metadata before major reorganizations

### Workflow Optimization
1. **Catalog First**: Use Metadata-Only mode to understand your collection
2. **Analyze Patterns**: Use LoRA Stack sorting to identify successful combinations  
3. **Organize**: Use Checkpoint sorting for final organization
4. **Access**: Use Auto-Open folder feature for immediate results access

---

## 🔧 Technical Specifications

### Performance
- **Optimized Processing**: Metadata caching prevents duplicate extraction
- **Memory Efficient**: Handles large collections without memory issues
- **Cross-Platform**: Full compatibility across operating systems

### File Support
- **Image Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP
- **Metadata Sources**: ComfyUI PNG metadata, EXIF data, custom fields
- **Path Handling**: Robust support for long paths, Unicode filenames, network drives

### Error Handling
- **Graceful Failures**: Continues processing even if individual files fail
- **Detailed Logging**: Comprehensive error reporting for troubleshooting
- **Recovery Options**: Smart handling of partial runs and interrupted operations

---

*This showcase covers Sorter 2.0 version 2.3.0 features. For technical details, see [README.md](README.md) and [CHANGELOG.md](CHANGELOG.md).*