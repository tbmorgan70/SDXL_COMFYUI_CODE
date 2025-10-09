# 🎯 SDXL ComfyUI Code - Complete Toolkit
**The ultimate collection of tools for managing, sorting, and optimizing AI image generation workflows.**

> 🆕 **Now Unified!** All tools consolidated into one clean, powerful repository. Previously scattered across multiple repos, now everything you need is here in one organized place.

## 🛠️ Complete Toolkit Overview

This unified repository contains four powerful tools:

### 1. **🎯 Main Sorter 2.0** (`sorter/`) - *Production Ready*
- **Advanced ComfyUI Image Organizer**
- Sort by Base Checkpoint (SDXL, Pony, etc.)
- **NEW!** 🧬 Sort by LoRA Stack - Group images by identical LoRA combinations
- **NEW!** 📄 Generate Metadata Only - Extract metadata without moving files  
- **NEW!** 📁 Auto-Open Output Folder - Instant access to results
- Search & Sort by Metadata (LoRAs, prompts, settings)
- Color-based sorting with visual previews
- Both GUI and CLI interfaces
- **Start here for most users!**

### 2. **🔄 CivitAI Converter** (`civitai_converter/`)
- Convert ComfyUI workflows to CivitAI format
- Metadata preservation and cleanup
- Batch processing support

### 3. **🌐 HTML Builder Suite** (`builder/`)
- Dynamic prompt generation interfaces
- Interactive HTML dashboards
- Custom workflow builders
- *Will be integrated with main sorter in future releases*

### 4. **📝 Unified Legacy Sorter** (`unified_sorter.py`)
- Original multi-mode sorter
- Text file organization
- ComfyUI batch processing
- Color analysis features

## 🚀 Quick Start Guide

### **Recommended: Sorter 2.0 (Most Users)**
```bash
# Navigate to the main sorter
cd sorter/

# GUI Version (Recommended)
python gui.py

# Command Line Version
python main.py
```

### **Alternative: Legacy Unified Sorter**
```bash
# Launch the original unified sorter
python unified_sorter.py
```

### **CivitAI Converter**
```bash
cd civitai_converter/
python comfyui_to_civitai_converter.py
```

### **Prerequisites**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install for specific tools only:
pip install -r sorter/requirements.txt        # For Sorter 2.0
pip install -r civitai_converter/requirements.txt  # For converter (if exists)
```

### **📁 Repository Structure**
```
SDXL_COMFYUI_CODE/
├── 🎯 sorter/                 # Main Sorter 2.0 (Production)
│   ├── gui.py                 # GUI interface
│   ├── main.py                # CLI interface
│   ├── core/                  # Core sorting logic
│   └── sorters/               # Individual sorting modules
├── 🔄 civitai_converter/      # ComfyUI to CivitAI converter
├── 🌐 builder/                # HTML interface builders
├── 📝 unified_sorter.py       # Legacy unified sorter
├── 🧪 tests/                  # Unit tests
├── 📦 archive/                # Legacy versions (reference)
└── 📚 docs/                   # Documentation files
```

### **🎯 Which Tool Should I Use?**

| **Use Case** | **Recommended Tool** | **Why** |
|--------------|---------------------|---------|
| **Sort ComfyUI images by checkpoint** | `sorter/` | Most advanced, GUI, fastest |
| **Group images by LoRA combinations** | `sorter/` | 🧬 NEW! LoRA Stack sorting |
| **Extract metadata without moving files** | `sorter/` | 📄 NEW! Metadata-only mode |
| **Organize by colors and metadata** | `sorter/` | Full feature set, visual previews |
| **Convert workflows for CivitAI** | `civitai_converter/` | Specialized tool |
| **Build custom HTML interfaces** | `builder/` | Interactive dashboards |
| **Quick text file organization** | `unified_sorter.py` | Simple, lightweight |

---

## 🆕 What's New in Version 2.3.0 (October 2025)

### 🧬 LoRA Stack Sorting
The most requested feature! Group your images by **identical LoRA combinations** - perfect for finding images with the same style effects regardless of checkpoint used.

### � Metadata-Only Mode  
Extract comprehensive metadata without moving files. Perfect for cataloging and analysis workflows.

### 📁 Auto-Open Results
Every operation now ends with a handy "Open Output Folder" button for instant access to your organized images.

**See full details in [Sorter Changelog](sorter/CHANGELOG.md)**

---

## �📚 Documentation & Guides

- **✨ [Sorter Changelog](sorter/CHANGELOG.md)** - Latest features and improvements
- **📖 [Migration Guide](MIGRATION_GUIDE.md)** - Switching from old repos/versions
- **🗺️ [Development Roadmap](ROADMAP.md)** - Future plans and priorities
- **🔧 [Sorter 2.0 Guide](sorter/README.md)** - Detailed sorter documentation
- **🔄 [Converter Guide](civitai_converter/COMFYUI_TO_CIVITAI_README.md)** - CivitAI conversion help
- **🌐 [Builder Guide](builder/README.md)** - HTML interface documentation

## 🤝 Contributing

We welcome contributions! Whether it's:
- 🐛 **Bug reports** - Help us identify issues
- ✨ **Feature requests** - Suggest improvements
- 📝 **Documentation** - Improve guides and examples
- 💻 **Code contributions** - Submit pull requests

See our [Roadmap](ROADMAP.md) for current development priorities.
├── color_sorter.py            # 🌈 Color sorting engine
├── text_file_sorter.py        # 📝 Text file organizer
├── final_batch_rename_sort.py # 🖼️ ComfyUI batch processor
├── demo_color_sorter.py       # 🧪 Color sorting demo
├── requirements.txt           # 📦 Dependencies
└── README.md                  # 📖 Documentation
```

## 🎯 Color Sorter Features

- **HSV-based Analysis**: Uses HSV color space for accurate classification
- **Handles Any Image Format**: PNG, JPG, JPEG, BMP, TIFF, WebP
- **Noise Reduction**: Groups similar colors to avoid over-categorization
- **Batch Processing**: Handles hundreds of images efficiently
- **Move or Copy**: Choose whether to move files or create copies
- **Preview Generation**: Visual color distribution chart for your collection

## 📁 Example Output Structure
```
color_sorted/
├── Red/
│   ├── [MySet_RED] sunset.png
│   └── [MySet_RED] roses.png
├── Blue/
│   ├── [MySet_BLUE] ocean.png
│   └── [MySet_BLUE] sky.png
├── Green/
│   └── [MySet_GREEN] forest.png
└── color_distribution_preview.png
```

Perfect for organizing AI-generated images by color themes, mood boards, or final collection curation!


# SDXL ComfyUI Prompt Builders Collection

A comprehensive collection of interactive HTML-based prompt builders designed for generating high-quality AI image prompts, specifically optimized for SDXL and ComfyUI workflows.

## 🎯 Overview

This collection contains specialized prompt builders for various artistic styles and subjects. Each builder provides an intuitive interface for assembling complex prompts by selecting from curated categories of elements.

## 📁 Available Builders

### Character & Portrait Builders
- **`1girl_cybergoth_legacy.html`** - Cybergoth girl character prompts
- **`1girl_extended_NSFW.html`** - Extended character options with adult content
- **`1girl_solo_setting_NSFW.html`** - Solo character settings with adult themes
- **`Nova_Skyrift.html`** - Nova Skyrift character portrait builder
- **`Nova_Skyrift_cybergoth_nsfw.html`** - Cybergoth variant with adult content
- **`Nova_Skydrift_x_Retro_SciFi.html`** - Retro sci-fi themed characters

### Vintage & Retro Builders
- **`ULTRA_1girl_vintage_NSFW.html`** - 1970s vintage girl prompts
- **`ULTRA_1girl_vintage_dualtoggle_NSFW.html`** - Dual-toggle vintage builder
- **`ULTRA_CUSTOM_1girl_vintage_NSFW.html`** - Customizable vintage builder

### Theme-Specific Builders
- **`disco_dollz_legacy_SFW.html`** - Disco-themed safe-for-work prompts
- **`ULTRA_disco_dollz_latest.HTML`** - Advanced disco theme builder
- **`Pink_Gunz_anime_SFW.html`** - Anime-style safe content

### Specialized Effect Builders
- **`ULTRA_1girl_glitch_cybergoth_NSFW.html`** - Glitch effect cybergoth
- **`ULTRA_super_heavy_glitch.html`** - Heavy glitch effects
- **`ULTRA_nova_skyrift_dualtoggle.html`** - Dual-toggle interface
- **`ULTRA_retro_scifi_controlroom.html`** - Retro sci-fi control room scenes

### Utility Builders
- **`HD_wallpaper_legacy.html`** - High-definition wallpaper prompts
- **`prompt_elements_dashboard.html`** - Comprehensive prompt elements reference

## 🚀 Getting Started

### Quick Start
1. Open any HTML file in your web browser
2. Click elements from different categories to build your prompt
3. Use the "🎲 Randomize" button for inspiration
4. Copy the generated prompt with "📋 Copy Prompt"

### Basic Usage
Each builder follows a consistent pattern:
- **Categories**: Different aspects like outfit, body type, mood, etc.
- **Selection**: Click items to add them to your prompt
- **Preview**: Real-time prompt assembly in the text area
- **Controls**: Randomize and copy functionality

## 🔧 Features

### Core Features
- **Interactive Selection**: Click-to-select interface for all prompt elements
- **Real-time Preview**: See your prompt build as you make selections
- **Randomization**: Generate random combinations for inspiration
- **Copy to Clipboard**: One-click copying of completed prompts
- **Dark Theme**: Eye-friendly dark interface for extended use

### Advanced Features
- **NSFW Toggle**: Content filtering for appropriate use (where applicable)
- **Dual Toggle**: Advanced control options in select builders
- **Category Expansion**: Collapsible sections for organized navigation
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Prompt Categories

Common categories across builders include:
- **Race/Ethnicity**: Character appearance options
- **Body Type**: Physical characteristics and build
- **Outfit/Clothing**: Detailed clothing and style options
- **Makeup & Beauty**: Cosmetic and beauty details
- **Accessories**: Jewelry, props, and additional items
- **Background/Setting**: Environmental and scene details
- **Pose**: Character positioning and stance
- **Mood/Expression**: Emotional tone and atmosphere
- **Lighting**: Illumination and visual effects
- **Style**: Artistic rendering approach

## 🎨 Builder Types

### Legacy Builders
- Basic functionality with core features
- Proven reliable prompt generation
- Ideal for quick prompt creation

### ULTRA Builders
- Enhanced feature sets
- More detailed customization options
- Advanced styling and effects
- Optimized for high-quality output

### Dashboard Tools
- Comprehensive reference materials
- Organized prompt element libraries
- Educational and reference purposes

## 💡 Usage Tips

### For Best Results
1. **Mix Categories**: Select from multiple categories for rich prompts
2. **Experiment**: Use randomize function to discover new combinations
3. **Refine**: Manually edit generated prompts as needed
4. **Save Favorites**: Keep track of successful prompt combinations

### ComfyUI Integration
- Generated prompts work directly with SDXL models
- Optimized for ComfyUI workflow compatibility
- Include quality and style suffixes for best results

### Content Guidelines
- NSFW builders include age verification and content warnings
- SFW builders are safe for all audiences
- Toggle options provide content filtering where available

## 🔒 Content Ratings

- **SFW**: Safe for work, general audiences
- **NSFW**: Adult content, age verification required
- **Legacy**: Original versions with proven functionality
- **ULTRA**: Enhanced versions with expanded features

## 🛠️ Technical Details

### Browser Compatibility
- Works in all modern web browsers
- No external dependencies required
- Pure HTML/CSS/JavaScript implementation

### File Structure
- Self-contained HTML files
- Embedded CSS styling
- Inline JavaScript functionality
- No server requirements

### Customization
- Easy to modify prompt lists
- Customizable styling via CSS
- Extensible JavaScript functions

## 📝 Contributing

To add new prompt elements or create new builders:
1. Follow existing file naming conventions
2. Maintain consistent UI/UX patterns
3. Include appropriate content warnings
4. Test across different browsers

## 📄 License

These prompt builders are provided for creative and educational use. Please respect content guidelines and age restrictions where applicable.

---

*Last updated: July 2025*
*Compatible with: SDXL, ComfyUI, and most AI image generation platforms*







## 📄 License

MIT License - see LICENSE file for details.
