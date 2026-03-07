# 🏗️ System Architecture

**Last Updated:** March 6, 2026  
**Repository Version:** 3.0.0

---

## 📋 Overview

The SDXL ComfyUI Code repository is a unified toolkit consisting of four independent yet complementary tools for AI image generation workflow management. Each component operates independently while sharing common design principles and potential future integration points.

### Design Philosophy
- **Modularity:** Each tool is self-contained and functional independently
- **Clarity:** Clear separation of concerns with logical organization
- **Extensibility:** Designed for future integration and expansion
- **User-Focused:** Both GUI and CLI interfaces where appropriate

---

## 🎯 High-Level Architecture

```
SDXL_COMFYUI_CODE Repository
│
├── Sorter (v2.4) ──────────────┐
│   └── Core sorting engine     │
│                                │
├── CivitAI Converter (v1.0) ───┤──► Future: Unified Interface
│   └── Format conversion        │    (Planned Phase 4)
│                                │
├── Builder Suite (v1.5) ────────┤
│   └── HTML prompt builders     │
│                                │
└── Modular Builder (v1.0) ──────┘
    └── Category-based system
```

---

## 🧩 Component Architecture

### 1. Sorter (Main Tool)

**Location:** `sorter/`  
**Version:** 2.4.0  
**Language:** Python

#### Structure:
```
sorter/
├── main.py                    # CLI entry point
├── gui.py                     # GUI entry point
├── version.py                 # Version info
│
├── core/                      # Core functionality
│   ├── metadata_engine.py     # ComfyUI metadata extraction
│   ├── logging_system.py      # Logging and error handling
│   └── formatting.py          # Output formatting
│
├── sorters/                   # Sorting algorithms
│   ├── checkpoint_sorter.py   # Sort by base model
│   ├── lora_sorter.py         # Sort by LoRA stacks
│   ├── metadata_sorter.py     # Sort by metadata search
│   ├── color_sorter.py        # Sort by dominant colors
│   └── flatten_sorter.py      # Flatten directory structures
│
└── sort_logs/                 # Session logs
```

#### Data Flow:
```
User Input (GUI/CLI)
    ↓
Configuration Selection
    ↓
File Discovery & Validation
    ↓
Metadata Extraction (core/metadata_engine.py)
    ↓
Sorting Algorithm (sorters/*)
    ↓
File Organization & Moving
    ↓
Metadata Preservation (.txt files)
    ↓
Logging & Reporting
    ↓
Auto-Open Results (optional)
```

#### Key Components:

**Metadata Engine:**
- Extracts PNG metadata from ComfyUI images
- Parses workflow JSON embedded in images
- Identifies checkpoints, LoRAs, prompts, settings
- Handles malformed or missing metadata gracefully

**Sorting Engines:**
- **Checkpoint Sorter:** Groups by base model (SDXL, Pony, etc.)
- **LoRA Sorter:** Creates unique folders per LoRA combination
- **Metadata Sorter:** Searches workflows for specific terms
- **Color Sorter:** Analyzes dominant colors, groups visually
- **Flatten Sorter:** Consolidates nested directories

**Logging System:**
- Session-based CSV logs
- Error tracking and reporting
- Operation summaries

---

### 2. CivitAI Converter

**Location:** `civitai_converter/`  
**Version:** 1.0.0  
**Language:** Python

#### Purpose:
Converts ComfyUI workflow format to CivitAI-compatible format for sharing and publishing.

#### Structure:
```
civitai_converter/
├── comfyui_to_civitai_converter.py    # Main converter
├── convert_comfyui_to_civitai.bat     # Windows launcher
└── COMFYUI_TO_CIVITAI_README.md       # Documentation
```

#### Conversion Process:
```
ComfyUI Workflow JSON
    ↓
Parse ComfyUI Structure
    ↓
Extract Nodes & Connections
    ↓
Transform to CivitAI Format
    ↓
Metadata Cleanup
    ↓
CivitAI-Compatible Output
```

#### Key Features:
- Preserves workflow logic
- Cleans unnecessary metadata
- Batch processing support
- Validates output format

---

### 3. Builder Suite

**Location:** `builder/`  
**Version:** 1.5.0  
**Language:** HTML/JavaScript

#### Purpose:
Collection of interactive HTML prompt builders for various themes and styles.

#### Structure:
```
builder/
├── README.md                              # Overview
├── usage_guide.md                         # User guide
├── technical_reference.md                 # Tech details
│
├── ultra_disco_dollz_final.html           # Disco theme
├── ultra_nova_skyrift_dualtoggle.html     # Sci-fi theme
├── ultra_retro_scifi_controlroom.html     # Retro sci-fi
├── ultra_txt2img_generic_dualtoggle.html  # Generic builder
└── [15+ additional themed builders]
```

#### Architecture Pattern:
```html
HTML Structure
    ↓
CSS Styling (Embedded)
    ↓
JavaScript Logic
    ├── Category Management
    ├── Random Selection
    ├── Dual Toggle System
    ├── Copy to Clipboard
    └── Export Functions
```

#### Common Features:
- Category-based prompt elements
- Random combination generation
- Dual-toggle switches (SFW/NSFW, Style A/B)
- One-click copy to clipboard
- Customizable categories
- Standalone operation (no server required)

---

### 4. Modular Builder

**Location:** `modular_builder/`  
**Version:** 1.0.0  
**Language:** Python/HTML

#### Purpose:
Server-based modular prompt building system with extensive CSV-based categories.

#### Structure:
```
modular_builder/
├── start_server.py                # Python server
├── START_SERVER.bat               # Windows launcher
├── modular_prompt_builder.html    # Main interface
│
├── categories/                    # 168+ CSV category files
│   ├── cat_bodytype_generic.csv
│   ├── cat_outfit_spacetime.csv
│   ├── cat_accessories_goth.csv
│   ├── vintage_categories/        # Vintage subcategory
│   └── [165+ more categories]
│
└── docs/
    ├── README.md
    ├── GETTING_STARTED.md
    └── TECHNICAL.md
```

#### System Flow:
```
Python Server (Flask/HTTP)
    ↓
Loads CSV Categories
    ↓
Serves HTML Interface
    ↓
User Selects Categories
    ↓
Dynamic Prompt Generation
    ↓
Export/Copy Results
```

#### Category System:
- **168+ CSV files** covering:
  - Body types, poses, expressions
  - Outfits, accessories, hairstyles
  - Settings, lighting, moods
  - Art styles, cameras, visual effects
  - Abstract elements, textures
  - Theme-specific (goth, punk, vintage, sci-fi, fantasy)
  
#### Advantages:
- Highly customizable via CSV editing
- Extensive category library
- Server allows dynamic loading
- Easy to add new categories

---

## 🔗 Integration Points (Future)

### Planned Unified Interface (Phase 4 - Q3 2026)

**Vision:**
```
Unified GUI/Dashboard
    │
    ├──► Sorter Operations
    │       └── Pre/Post-process with other tools
    │
    ├──► CivitAI Export
    │       └── Convert workflows directly
    │
    ├──► Prompt Building
    │       └── Generate → ComfyUI → Sort
    │
    └──► Shared Configuration
            └── Common settings & preferences
```

### Potential Integration Features:
- **Unified Config:** Shared settings across all tools
- **Workflow Chain:** Generate prompt → Create image → Sort results
- **Metadata Bridge:** Share metadata between components
- **Plugin System:** Third-party extensions
- **API Layer:** Programmatic access to all functions

---

## 💾 Data Management

### File Types Handled:
- **Images:** PNG (primary), JPG, JPEG
- **Metadata:** .txt files (ComfyUI metadata)
- **Workflows:** JSON (embedded in PNGs)
- **Categories:** CSV files (Modular Builder)
- **Logs:** CSV session logs

### Metadata Preservation:
- PNG images move with their .txt metadata files
- Workflow JSON preserved in PNG metadata
- Session logs track all operations
- Error logs capture issues

### Storage Pattern:
```
Input Directory
    ↓
Sorter Processing
    ↓
Output Directory Structure
    ├── checkpoint_name_1/
    │   ├── image001.png
    │   └── image001.txt
    ├── checkpoint_name_2/
    │   ├── image002.png
    │   └── image002.txt
    └── sort_logs/
        └── session_TIMESTAMP.csv
```

---

## 🔒 Error Handling

### Sorter:
- **Missing Metadata:** Moves to "no_metadata" folder
- **Malformed JSON:** Logs error, processes what's available
- **File Access Errors:** Logs and continues with remaining files
- **Duplicate Filenames:** Appends counter to prevent overwrites

### CivitAI Converter:
- **Invalid Workflow:** Logs error, skips file
- **Missing Nodes:** Attempts partial conversion
- **Format Errors:** Validates and reports issues

### Builders:
- **Missing Files:** Graceful degradation
- **JavaScript Errors:** Console logging
- **CSV Parse Errors:** Skip invalid entries

---

## 📊 Performance Considerations

### Sorter:
- **Scalability:** Tested with 10,000+ images
- **Memory:** <500MB for typical operations
- **Speed:** ~100-200 images/minute (hardware dependent)
- **Optimization:** Batch processing, efficient file I/O

### Modular Builder:
- **CSV Loading:** Fast initial load
- **Category Count:** 168+ files loaded on startup
- **Response Time:** <200ms for prompt generation
- **Server:** Lightweight Python HTTP server

---

## 🔧 Technology Stack

### Python Components:
- **Python:** 3.7+
- **Libraries:**
  - PIL/Pillow (image processing)
  - tkinter (GUI)
  - json, csv (data handling)
  - pathlib, os (file operations)
  - Flask/http.server (Modular Builder server)

### HTML/JavaScript Components:
- **Pure JavaScript:** No external dependencies
- **Modern HTML5/CSS3**
- **Standalone operation**

---

## 🎯 Design Patterns

### Sorter:
- **Strategy Pattern:** Interchangeable sorting algorithms
- **Factory Pattern:** Sorter selection based on user choice
- **Observer Pattern:** Logging system monitors operations

### Modular Builder:
- **MVC-like:** Server (Model), HTML (View), JS (Controller)
- **Data-Driven:** CSV files drive category system

### Overall:
- **Separation of Concerns:** Core logic separate from UI
- **DRY Principle:** Shared utilities and common code
- **Modular Design:** Independent components

---

## 🚀 Future Architecture Evolution

### Short-term (Q2-Q3 2026):
- Shared configuration system
- Common utility libraries
- Unified logging format

### Long-term (Q4 2026+):
- Plugin architecture
- REST API layer
- Database backend for metadata
- Cross-tool workflows
- Cloud integration options

---

## 📚 Related Documentation

- [VERSION.md](../VERSION.md) - Component versions and history
- [ROADMAP.md](../ROADMAP.md) - Development plans
- [CURATION_PLAN.md](../CURATION_PLAN.md) - Repository organization plan
- [sorter/README.md](../sorter/README.md) - Sorter details
- [builder/technical_reference.md](../builder/technical_reference.md) - Builder implementation

---

**Document Status:** Living document - updated as architecture evolves  
**Maintained By:** Project contributors  
**Next Review:** Q3 2026 (during integration planning)
