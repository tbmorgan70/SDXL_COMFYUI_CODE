# 🔗 Integration Plan - Unified Toolkit Architecture

**Created:** March 7, 2026  
**Status:** Phase 4 - Active Planning  
**Target:** Q3 2026 Implementation  
**Repository Version:** 3.0.0

---

## 📋 Executive Summary

This document outlines the integration strategy for unifying the four independent tools (Sorter, CivitAI Converter, Builder Suite, Modular Builder) into a cohesive, interoperable system while maintaining their standalone functionality.

### Goals:
1. **Preserve Independence:** Each tool remains functional standalone
2. **Enable Interoperability:** Tools can pass data and chain operations
3. **Unified Configuration:** Shared settings and preferences
4. **Seamless Workflows:** End-to-end generation → organization pipelines
5. **Extensibility:** Plugin architecture for future expansion

---

## 🛠️ Current Tool Interfaces

### 1. Sorter (v2.4) - Core Functionality

**Entry Points:**
- `sorter/main.py` - CLI interface
- `sorter/gui.py` - Tkinter GUI interface

**Inputs:**
```python
{
    "source_directory": Path,           # Required: Images to sort
    "output_directory": Path,           # Required: Destination folder
    "operation_mode": str,              # checkpoint|lora_stack|metadata_only|color|flatten
    "file_operation": str,              # copy|move
    "create_metadata": bool,            # Generate .txt files
    "metadata_options": {
        "include_prompts": bool,
        "include_settings": bool,
        "include_workflow": bool
    }
}
```

**Outputs:**
```python
{
    "success": bool,
    "files_processed": int,
    "files_failed": int,
    "output_structure": {
        "checkpoint_name/": [
            "image001.png",
            "image001.txt"
        ]
    },
    "log_file": Path,                   # CSV session log
    "errors": List[dict]
}
```

**Core Modules:**
- `core/metadata_engine.py` - Extracts ComfyUI PNG metadata
- `sorters/checkpoint_sorter.py` - Groups by base model
- `sorters/lora_sorter.py` - Groups by LoRA combinations
- `sorters/metadata_sorter.py` - Search and filter
- `sorters/color_sorter.py` - Dominant color sorting

**Data Formats:**
- **Input:** PNG images with ComfyUI workflow JSON
- **Output:** Organized folders + optional .txt metadata
- **Logs:** CSV format with timestamps

---

### 2. CivitAI Converter (v1.0) - Format Translation

**Entry Points:**
- `civitai_converter/comfyui_to_civitai_converter.py` - CLI script
- `civitai_converter/convert_comfyui_to_civitai.bat` - Batch wrapper

**Inputs:**
```python
{
    "input_directory": Path,            # Required: ComfyUI images
    "output_directory": Path,           # Optional: Defaults to input
    "model_paths": {
        "checkpoints": Path,
        "loras": Path,
        "vaes": Path,
        "embeddings": Path
    },
    "calculate_hashes": bool            # Generate SHA256 hashes
}
```

**Outputs:**
```python
{
    "converted_files": int,
    "failed_conversions": int,
    "hashes_calculated": {
        "model_name": "sha256_hash",
        "lora_name": "sha256_hash"
    },
    "metadata_added": List[Path]        # Files with Civitai metadata
}
```

**Core Functions:**
- Reads ComfyUI workflow JSON from PNG metadata
- Identifies model resources (checkpoints, LoRAs, VAEs)
- Calculates SHA256 hashes for resources
- Adds Civitai-compatible metadata to images

**Data Formats:**
- **Input:** PNG with ComfyUI metadata
- **Output:** PNG with Civitai + ComfyUI metadata
- **Hash Format:** `{"model": "abc123", "lora:name": "def456"}`

---

### 3. Builder Suite (v1.5) - Prompt Generation

**Entry Points:**
- 13 standalone HTML files (`builder/*.html`)
- No programmatic API (browser-based)

**Inputs (User Interaction):**
- Category selections (character, style, mood, etc.)
- Toggle switches (NSFW filters, dual-toggle features)
- Randomization controls
- Base prompt modifications

**Outputs:**
```javascript
{
    "prompt": String,                    // Complete prompt text
    "categories_used": Array[String],    // Selected categories
    "elements": {
        "body_type": String,
        "outfit": String,
        "mood": String,
        // ... etc
    },
    "quality_tags": String,              // Suffix quality modifiers
    "timestamp": Date
}
```

**Interface Methods:**
- Copy to clipboard (browser API)
- No file export (manual copy/paste workflow)
- No programmatic access

**Data Formats:**
- **Input:** HTML form selections
- **Output:** Text string (clipboard)
- **Storage:** LocalStorage for randomization state

---

### 4. Modular Builder (v1.0) - Category Management

**Entry Points:**
- `modular_builder/modular_prompt_builder.html` - Web interface
- `modular_builder/start_server.py` - Local server
- `modular_builder/START_SERVER.bat` - Quick launch

**Inputs:**
```python
# Server Configuration
{
    "port": int,                         # Default: 8000
    "directory": Path,                   # Serve location
    "categories_path": Path              # CSV files location
}

# Builder Interface (JavaScript)
{
    "base_prompt": String,               # User-defined base
    "quality_tags": String,              # User-defined quality
    "category_selections": {
        "bodytype": String,
        "scene": String,
        "outfit": String,
        // ... 10 categories
    },
    "locked_categories": Array[String],  // Categories to preserve
    "csv_files": {
        "bodytype": "cat_bodytype_fantasy.csv",
        "scene": "cat_scene_cyberpunk.csv",
        // ...
    }
}
```

**Outputs:**
```javascript
{
    "prompt": String,                    // Assembled prompt
    "combinations_count": Number,        // Total possibilities
    "batch_prompts": Array[String],      // For batch generation
    "export_file": String                // Text file with prompts
}
```

**Core Components:**
- Flask local server (Python)
- JavaScript prompt builder (browser)
- CSV category files (168+ files)

**Data Formats:**
- **Input:** CSV files (`categories/*.csv`)
- **Output:** Text string or .txt file (batch export)
- **Config:** HTML-embedded defaults

---

## 🔗 Integration Points

### Current State: Isolated Tools

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Builder   │────▶│  User (Manual)   │────▶│   Sorter    │
│   Suite     │     │  Copy/Paste      │     │             │
└─────────────┘     └──────────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │    ComfyUI       │
                    │  (External App)  │
                    └──────────────────┘
                            │
                            ▼
                    ┌──────────────────┐     ┌─────────────┐
                    │  PNG Images      │────▶│  CivitAI    │
                    │  Generated       │     │  Converter  │
                    └──────────────────┘     └─────────────┘
```

### Proposed Unified Architecture

```
┌───────────────────────────────────────────────────────────┐
│              Unified Interface / Dashboard                 │
│                   (Python Tkinter/Web)                     │
├───────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Prompt     │  │   Sorting    │  │  Conversion  │   │
│  │  Generation  │  │   Engine     │  │    Tools     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            │                               │
├────────────────────────────┼───────────────────────────────┤
│         Shared Services Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Config Mgmt  │  │  Metadata    │  │  File Ops    │   │
│  │              │  │   Handler    │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
├──────────────────────────────────────────────────────────┤
│         Data Layer (Files, Logs, Config)                  │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 Integration Opportunities

### 1. **Prompt → ComfyUI → Sort** Workflow

**Vision:** Seamless generation pipeline

```python
# Pseudo-code for integrated workflow
workflow = UnifiedWorkflow()

# Step 1: Generate prompt
prompt = workflow.generate_prompt(
    builder="ultra_disco_dollz",
    categories=["cybergoth", "neon", "glitch"],
    randomize=True
)

# Step 2: Send to ComfyUI (external API)
images = workflow.send_to_comfyui(
    prompt=prompt,
    checkpoint="sdxl_base.safetensors",
    loras=["cybergoth_v2", "glitch_effect"]
)

# Step 3: Auto-sort results
workflow.auto_sort(
    images=images,
    mode="checkpoint",
    create_metadata=True
)

# Step 4: Optional conversion
workflow.convert_to_civitai(
    images=images,
    calculate_hashes=True
)
```

### 2. **Shared Metadata System**

**Common Metadata Format:**
```json
{
    "unified_metadata": {
        "prompt": {
            "text": "String",
            "builder": "ultra_disco_dollz",
            "categories": ["bodytype", "scene"],
            "generated_by": "builder_suite_v1.5"
        },
        "generation": {
            "checkpoint": "sdxl_base.safetensors",
            "loras": [
                {"name": "cybergoth_v2", "weight": 0.8},
                {"name": "glitch_effect", "weight": 0.6}
            ],
            "seed": 123456,
            "cfg": 7.5,
            "steps": 30
        },
        "sorting": {
            "sorted_by": "checkpoint",
            "output_folder": "sdxl_base/",
            "sorted_date": "2026-03-07T14:30:00"
        },
        "conversion": {
            "civitai_hashes": {
                "model": "abc123",
                "lora:cybergoth_v2": "def456"
            },
            "converted": true
        }
    }
}
```

### 3. **Unified Configuration**

**Proposed Structure:**
```yaml
# config/unified_config.yaml

global:
  output_base: "C:/ComfyUI/output"
  temp_directory: "C:/temp"
  log_level: "INFO"
  theme: "dark"

sorter:
  default_operation: "checkpoint"
  default_file_op: "copy"
  create_metadata: true
  auto_open_results: true
  metadata_options:
    include_prompts: true
    include_settings: true
    include_workflow: true

converter:
  model_paths:
    checkpoints: "C:/ComfyUI/models/checkpoints"
    loras: "C:/ComfyUI/models/loras"
    vaes: "C:/ComfyUI/models/vae"
  calculate_hashes: true
  preserve_original: true

builders:
  default_quality_tags: "8K, ultra-textural, highly detailed"
  default_base_prompt: "1girl, solo"
  auto_copy_clipboard: true

modular_builder:
  server_port: 8000
  categories_path: "modular_builder/categories"
  default_categories: [
    "bodytype",
    "scene",
    "outfit"
  ]
```

---

## 🔧 Technical Implementation Plan

### Phase 4A: Foundation (Q3 2026)

#### 1. Create Shared Library (`lib/` directory)

```
lib/
├── __init__.py
├── config_manager.py          # Unified configuration
├── metadata_handler.py        # Shared metadata operations
├── file_operations.py         # Common file utilities
├── logger.py                  # Unified logging
└── api/                       # Future API layer
    ├── __init__.py
    ├── sorter_api.py
    ├── converter_api.py
    └── builder_api.py
```

#### 2. Configuration System

**Create:** `lib/config_manager.py`
```python
class ConfigManager:
    """Unified configuration management"""
    
    def __init__(self, config_path="config/unified_config.yaml"):
        self.config = self.load_config(config_path)
    
    def get_sorter_config(self) -> dict:
        """Get sorter-specific settings"""
        return self.config.get("sorter", {})
    
    def get_converter_config(self) -> dict:
        """Get converter-specific settings"""
        return self.config.get("converter", {})
    
    def get_global_config(self) -> dict:
        """Get global settings"""
        return self.config.get("global", {})
```

#### 3. Metadata Handler

**Create:** `lib/metadata_handler.py`
```python
class UnifiedMetadata:
    """Shared metadata format for all tools"""
    
    def __init__(self):
        self.data = {
            "unified_metadata": {
                "prompt": {},
                "generation": {},
                "sorting": {},
                "conversion": {}
            }
        }
    
    def add_prompt_metadata(self, prompt: str, builder: str, categories: list):
        """Add prompt generation metadata"""
        pass
    
    def add_generation_metadata(self, checkpoint: str, loras: list, settings: dict):
        """Add ComfyUI generation metadata"""
        pass
    
    def to_json(self) -> str:
        """Export as JSON"""
        pass
    
    def to_txt(self) -> str:
        """Export as human-readable text"""
        pass
```

#### 4. Tool APIs

**Sorter API:**
```python
# lib/api/sorter_api.py

class SorterAPI:
    """Programmatic access to sorter functionality"""
    
    def sort_images(self, 
                    source: Path,
                    output: Path,
                    mode: str = "checkpoint",
                    **kwargs) -> dict:
        """Sort images programmatically"""
        pass
    
    def extract_metadata(self, image_path: Path) -> dict:
        """Extract metadata from single image"""
        pass
    
    def batch_metadata(self, directory: Path) -> List[dict]:
        """Extract metadata from all images in directory"""
        pass
```

**Converter API:**
```python
# lib/api/converter_api.py

class ConverterAPI:
    """Programmatic access to conversion"""
    
    def convert_to_civitai(self,
                          source: Path,
                          output: Path = None,
                          **kwargs) -> dict:
        """Convert ComfyUI images to Civitai format"""
        pass
    
    def calculate_hashes(self, model_paths: dict) -> dict:
        """Calculate SHA256 hashes for resources"""
        pass
```

**Builder API:**
```python
# lib/api/builder_api.py

class BuilderAPI:
    """Programmatic access to prompt building"""
    
    def generate_prompt(self,
                       builder: str,
                       categories: dict,
                       base_prompt: str = None,
                       quality_tags: str = None) -> str:
        """Generate prompt from categories"""
        pass
    
    def randomize_prompt(self, builder: str, locked: list = None) -> str:
        """Generate random prompt with locked categories"""
        pass
    
    def batch_generate(self, builder: str, count: int) -> List[str]:
        """Generate multiple random prompts"""
        pass
```

---

### Phase 4B: Unified Interface (Q4 2026)

#### Dashboard Concept

**Technology Options:**
1. **Python Tkinter** - Matches existing sorter GUI, native feel
2. **Web Interface** - Flask/FastAPI backend, React/Vue frontend
3. **Electron** - Hybrid approach, web tech with native wrapper

**Recommended:** Python Tkinter initially (consistency with sorter), web version in future

**Dashboard Features:**
```
┌─────────────────────────────────────────────────────────┐
│  SDXL Toolkit - Unified Interface                       │
├─────────────────────────────────────────────────────────┤
│  [Prompt Builder] [Sorter] [Converter] [Settings]      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Quick Actions:                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Generate    │  │  Sort Last   │  │  Convert All │ │
│  │   Prompt     │  │   Batch      │  │  to Civitai  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  Workflows:                                              │
│  ┌────────────────────────────────────────────────────┐│
│  │ [✓] Generate Prompt                                ││
│  │ [ ] Send to ComfyUI (auto-detect)                  ││
│  │ [✓] Auto-Sort Results                              ││
│  │ [ ] Convert to Civitai                             ││
│  └────────────────────────────────────────────────────┘│
│                                                          │
│  Status:                                                 │
│  Last run: Sorted 150 images (checkpoint mode)          │
│  Output: C:/ComfyUI/output/sorted/                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Testing Strategy

### Current Test Coverage

**Existing Tests:** `tests/` directory (6 files)
- `test_seed_extraction.py` - Seed value parsing
- `test_enhanced_seeds.py` - Advanced seed handling
- `test_extract_primary_checkpoint.py` - Checkpoint detection
- `test_lora_formatting.py` - LoRA string parsing
- `test_cfg_resolution.py` - CFG parameter extraction
- `test_seed_edge_cases.py` - Edge case handling

**Coverage Assessment:**
- ✅ Core metadata extraction covered
- ⚠️ Sorter operations not covered
- ❌ GUI not tested
- ❌ Converter not tested
- ❌ Builders not tested

### Target Test Coverage: 90%

**test/ Organization:**
```
tests/
├── unit/                        # Unit tests
│   ├── test_config_manager.py
│   ├── test_metadata_handler.py
│   ├── test_sorter_api.py
│   ├── test_converter_api.py
│   └── test_builder_api.py
│
├── integration/                 # Integration tests
│   ├── test_workflow_chains.py
│   ├── test_unified_metadata.py
│   └── test_cross_tool.py
│
├── functional/                  # End-to-end tests
│   ├── test_complete_workflow.py
│   ├── test_gui_operations.py
│   └── test_batch_processing.py
│
└── fixtures/                    # Test data
    ├── sample_images/
    ├── sample_workflows/
    └── sample_configs/
```

### CI/CD Pipeline (Future)

**GitHub Actions Workflow:**
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=. --cov-report=html
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 🗺️ Implementation Roadmap

### Immediate (Phase 4 - Q2 2026)

- [x] Document current tool interfaces
- [x] Identify integration points
- [ ] Create `lib/` shared library structure
- [ ] Implement `config_manager.py`
- [ ] Implement `metadata_handler.py`
- [ ] Create unified config YAML template
- [ ] Expand test coverage to 50%

### Near-Term (Q3 2026)

- [ ] Implement tool APIs (sorter, converter, builder)
- [ ] Create basic unified dashboard (Tkinter)
- [ ] Implement workflow chaining
- [ ] Test integration between tools
- [ ] Achieve 75% test coverage

### Long-Term (Q4 2026)

- [ ] Web-based dashboard (optional)
- [ ] ComfyUI API integration
- [ ] Plugin system architecture
- [ ] Third-party extension support
- [ ] Achieve 90% test coverage

---

## 🚧 Challenges & Considerations

### 1. Backward Compatibility
**Challenge:** Existing users rely on standalone tools  
**Solution:** Maintain standalone functionality, unified interface is additive

### 2. Builder Integration
**Challenge:** HTML builders have no programmatic API  
**Solution:** Extract logic to Python, keep HTML for manual use

### 3. ComfyUI Integration
**Challenge:** ComfyUI is external application  
**Solution:** File watching + optional API integration (future)

### 4. Performance
**Challenge:** Unified interface may add overhead  
**Solution:** Keep tools modular, load only what's needed

### 5. Testing Complexity
**Challenge:** Testing GUI and workflows is complex  
**Solution:** Prioritize API testing, use fixtures for functional tests

---

## 📚 Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and component architecture
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Contributing and development setup
- [CURATION_PLAN.md](../CURATION_PLAN.md) - Repository overhaul phases
- [ROADMAP.md](../ROADMAP.md) - Future development plans
- [VERSION.md](../VERSION.md) - Version tracking and history

---

## 💡 Future Enhancements

### API-First Design
- RESTful API for all tools
- WebSocket for real-time updates
- OpenAPI/Swagger documentation

### Plugin System
- Third-party sorting algorithms
- Custom prompt builders
- External tool integrations

### Cloud Features
- Cloud storage integration
- Prompt library sharing
- Collaborative workflows

### AI Features
- Automatic prompt optimization
- Style transfer suggestions
- Smart sorting recommendations

---

**Status:** 📋 Planning Phase Complete  
**Next Steps:** Begin implementation of shared library (`lib/`)  
**Owner:** Development team  
**Last Updated:** March 7, 2026
