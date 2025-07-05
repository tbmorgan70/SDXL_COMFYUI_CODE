# SD_COMFYUI_HACKS
This repo is a curated collection of tools for managing, sorting, and optimizing AI image generation workflows. Built to evolve as your projects grow.

## 🎨 Unified Sorter - Now with Color Sorting!

The **Unified Sorter** is a comprehensive tool featuring three powerful modes:

### 1. **Text File Sorter** 📝
- Organizes text files using customizable placeholders
- Supports move or copy operations
- Perfect for organizing prompts, logs, and documentation

### 2. **ComfyUI Batch Sorter** 🖼️
- Renames images by Base+LoRA-sorted GEN format
- Generates detailed metadata files
- Sorts images into folders by checkpoint filenames
- Handles non-PNG files automatically

### 3. **🌈 Color Sorter** ✨ *NEW!*
- **Dominant Color Analysis**: Automatically detects each image's primary color
- **Smart Classification**: Sorts into 11 color categories (Red, Blue, Green, Yellow, Purple, Orange, Pink, Brown, Black, White, Gray)
- **Custom Renaming**: Optional color-based file prefixes (e.g., `[MySet_RED] image.png`)
- **Visual Preview**: Creates color distribution bar showing your collection breakdown
- **Perfect Final Step**: Ideal for final organization after other sorting methods

## 🚀 Getting Started

### Prerequisites
```bash
# Clone the repository
git clone <your-repo-url>
cd SD_COMFYUI_HACKS

# Install dependencies
pip install -r requirements.txt
```

### Quick Start
```bash
# Launch the main unified sorter
python unified_sorter.py

# Or try the color sorting demo
python demo_color_sorter.py
```

### File Structure
```
SD_COMFYUI_HACKS/
├── unified_sorter.py          # 🎯 Main application (start here!)
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
