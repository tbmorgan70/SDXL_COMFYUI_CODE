# 🎯 SDXL ComfyUI Code - Complete Toolkit
**The ultimate collection of tools for managing, sorting, and optimizing AI image generation workflows.**

> 🆕 **Version 3.7 - Sorter 3.6.3** (October 2026): Manual Crop at exact preset sizes, Civitai Prep that reads custom-sampler workflows (Krea2, Flux), and AI Upscale with your ComfyUI models — all inside the main Sorter.

📚 **[Knowledge Index](KNOWLEDGE_INDEX.md)** | 📋 **[Version Info](VERSION.md)** | 🔀 **[Git Workflow](GIT_WORKFLOW.md)** | 🗺️ **[Roadmap](ROADMAP.md)**

## 🛠️ Complete Toolkit Overview

This unified repository contains these tools:

### 1. **🎯 Main Sorter v3.6** (`sorter/`) - *Production Ready*
- **Advanced ComfyUI Image Organizer**
- Sort by Base Checkpoint (SDXL, Pony, etc.)
- **v3.6** ✂️ Manual Crop - Fixed frame at exact preset sizes, image floats underneath; press C in Triage, Tab cycles sizes, O flips orientation
- **v3.5** 🔍 AI Upscale - Your ComfyUI upscale models on the GPU, to a target long edge, metadata kept
- **v3.1** 🏷️ Civitai Prep - Embeds checkpoint/LoRA/VAE/embedding hashes so Civitai auto-detects resources on upload; traces KSampler and custom-sampler (Krea2, Flux) workflows
- **v3.0** 📦 Extract Images - Pull images from PDF/EPUB/MOBI/CBR/CBZ and other archives with auto-crop presets and face-centered cropping
- **v3.0** 🖼️ Manual Sort (Triage) - Visual gallery with keyboard-driven bucket sorting
- **v3.0** 🌈 New Color Engine - HSV pixel voting with intuitive tuning sliders
- **v2.4** 🗂️ Automatic Metadata Preservation - PNG images move with their .txt files
- **v2.3+** 🧬 Sort by LoRA Stack - Group images by identical LoRA combinations
- **v2.3+** 📄 Generate Metadata Only - Extract metadata without moving files
- Search & Sort by Metadata (LoRAs, prompts, settings)
- Both GUI and CLI interfaces
- **Start here for most users!**

### 2. **🌐 HTML Builder Suite** (`builder/`)
- Dynamic prompt generation interfaces
- Interactive HTML dashboards
- Custom workflow builders
- *Will be integrated with main sorter in future releases*

### 3. **🧩 Modular Builder** (`modular_builder/`)
- Category-based prompt building with 168+ category CSV files
- Server-based interface, highly customizable

### 4. **📝 Unified Legacy Sorter** (`unified_sorter.py`)
- Original multi-mode sorter
- Text file organization
- ComfyUI batch processing
- Color analysis features

> 📦 **Deprecated:** The standalone `ImageExtractor/` tool has been superseded by the Sorter's built-in Extract Images mode.

## 🚀 Quick Start Guide

### **Recommended: Sorter 3.6 (Most Users)**
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

### **Prerequisites**
- Python 3.7 or higher
- pip (Python package manager)

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install for specific tools:
pip install -r sorter/requirements.txt        # For the Sorter
```

### **📁 Repository Structure**
```
SDXL_COMFYUI_CODE/
├── 🎯 sorter/                 # Main Sorter 3.6 (Production)
│   ├── gui.py                 # GUI interface
│   ├── main.py                # CLI interface
│   ├── core/                  # Core sorting logic
│   └── sorters/               # Individual sorting modules
├── 🌐 builder/                # HTML interface builders
├── 🧩 modular_builder/        # CSV-driven prompt builder (server)
├── 📝 unified_sorter.py       # Legacy unified sorter
├── 🧪 tests/                  # Unit tests
├── 📦 archive/                # Legacy versions (reference)
└── 📚 docs/                   # Documentation files
```

### **🎯 Which Tool Should I Use?**

| **Use Case** | **Recommended Tool** | **Why** |
|--------------|---------------------|---------|
| **Sort ComfyUI images by checkpoint** | `sorter/` | Most advanced, GUI, fastest |
| **Group images by LoRA combinations** | `sorter/` | LoRA Stack sorting |
| **Extract metadata without moving files** | `sorter/` | Metadata-only mode |
| **Organize by colors and metadata** | `sorter/` | Full feature set, visual previews |
| **Prep images for Civitai upload** | `sorter/` → Civitai Prep | Resources auto-detected on upload |
| **Crop to exact training/print sizes** | `sorter/` → Manual Crop | Fixed frame, metadata kept |
| **Upscale with ComfyUI models** | `sorter/` → AI Upscale | GPU, VRAM-aware tiling |
| **Build custom HTML interfaces** | `builder/` | Interactive dashboards |
| **Quick text file organization** | `unified_sorter.py` | Simple, lightweight |

---

## 🆕 What's New in Sorter 3.6 (October 2026)

### ✂️ Manual Crop (3.6.0, 3.6.1)
A fixed frame at an exact preset size with the image floating underneath: drag to pan, scroll to zoom, Enter to save. Press **C** in Triage to crop while you sort. Tab / Shift+Tab step through sizes, **O** flips portrait ↔ landscape, and the resolution badge warns when a crop would be soft. Crops are metadata-preserving copies; originals are never touched.

### 🧭 Custom-sampler workflows (3.6.2, 3.6.3)
Civitai Prep and the .txt reports now follow `SamplerCustomAdvanced` graphs (Krea2, Flux) to their prompt, seed, steps, sampler and CFG. `er_sde` is labelled "ER SDE".

**See full details in [Sorter Changelog](sorter/CHANGELOG.md)**

---

## 📚 Documentation & Guides

- **✨ [Sorter Changelog](sorter/CHANGELOG.md)** - Latest features and improvements
- **📖 [Migration Guide](MIGRATION_GUIDE.md)** - Switching from old repos/versions
- **🗺️ [Development Roadmap](ROADMAP.md)** - Future plans and priorities
- **🔧 [Sorter Guide](sorter/README.md)** - Detailed sorter documentation
- **🔍 [Upscaling Plan](docs/UPSCALING_PLAN.md)** - AI Upscale design and the restoration phase still to come
- **🌐 [Builder Guide](builder/README.md)** - HTML interface documentation

## 🤝 Contributing

We welcome contributions! Whether it's:
- 🐛 **Bug reports** - Help us identify issues
- ✨ **Feature requests** - Suggest improvements
- 📝 **Documentation** - Improve guides and examples
- 💻 **Code contributions** - Submit pull requests

See our [Roadmap](ROADMAP.md) for current development priorities.

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

## 📚 Documentation Navigator

### Quick Links
- 📖 [Knowledge Index](KNOWLEDGE_INDEX.md) - Find any documentation instantly
- 📌 [Version Information](VERSION.md) - Current versions and history
- 🔀 [Git Workflow](GIT_WORKFLOW.md) - Development best practices
- 🗺️ [Roadmap](ROADMAP.md) - Future development plans
- 📋 [Conversation Log](CONVERSATION_LOG.md) - Development session history

### Deep Dive
- 🏗️ [Architecture](docs/ARCHITECTURE.md) - System design and structure
- 🛠️ [Development Guide](docs/DEVELOPMENT_GUIDE.md) - Contributing guidelines
- 🔄 [Migration Guide](MIGRATION_GUIDE.md) - Upgrading from old versions
- 📦 [Archive](archive/README.md) - Historical versions reference

### Tool-Specific Docs
- [Sorter Documentation](sorter/README.md)
- [Builder Suite](builder/README.md)
- [Modular Builder](modular_builder/README.md)

---

## 📄 License

MIT License - see LICENSE file for details.
