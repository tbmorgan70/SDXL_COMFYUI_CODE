# 📦 Archive Directory

**Purpose:** Historical versions and deprecated code for reference  
**Status:** Reference Only - Not for Active Use

---

## 📁 Directory Contents

### `legacy_scripts/`
**Original Python tools from early development**

Contains the foundational scripts that evolved into the current sorter system:
- `debug_filename.py` - Early filename debugging utilities
- `demo_final.py` - Demo versions of sorting functionality
- `robust_comfy_sort.py` - Early ComfyUI sorting implementation
- `final_batch_rename_sort.py` - Batch renaming utilities
- `text_file_sorter.py` - Text file organization tools
- And more...

**Historical Context:** These scripts represent the initial development phase before the repository was organized into the current structure.

---

### `sorter_versions/` **✅ Consolidated  Structure**
**All historical sorter versions in one organized location**

Contains three major iterations of the sorter tool:

#### `v1_original/` (formerly `sorter/`)
The initial attempt at organizing sorting functionality into a cohesive tool. Features included:
- Color-based sorting
- ComfyUI flattening
- Image organization
- Early metadata handling

#### `v2_iteration/` (formerly `sorter_v2/`)
Second generation sorter with enhanced features:
- Enhanced GUI
- Better metadata extraction
- Multiple sorting modes
- Improved error handling

#### `v2_dev/` (formerly `sorter_v2_dev_only/`)
Development workspace with experimental features:
- Testing and experiments
- Multiple GUI versions
- Analysis tools
- Work-in-progress features

#### `logs/`
Development and testing logs:
- `gui_standard_log.txt` - GUI development history

**All Evolved Into:** Current production `sorter/` (v2.4)

---

### `docs/`
**Historical documentation**

Contains documentation that has been superseded or consolidated:

- `case_standardization_summary.md` - Record of file naming convention changes (historical reference)
- `git_advice.md` - Git workflow conversations (consolidated into GIT_WORKFLOW.md)
- `development_notes.md` - Early development notes (consolidated into GIT_WORKFLOW.md)

**Current Equivalents:**
- Git workflows: See [GIT_WORKFLOW.md](../GIT_WORKFLOW.md)
- Development tracking: See [CONVERSATION_LOG.md](../CONVERSATION_LOG.md)

---

### `gui_standard_log.txt`
**GUI development log**

Detailed log from GUI development and testing sessions. Historical record of UI evolution.

---

## 🔍 When to Reference the Archive

### Use Archive When:
- ✅ Researching how a feature evolved
- ✅ Understanding design decisions
- ✅ Recovering old functionality (rare cases)
- ✅ Learning project history
- ✅ Debugging legacy compatibility issues

### Don't Use Archive For:
- ❌ Active development (use current tools)
- ❌ New projects (use current versions)
- ❌ Production deployments (use `sorter/` v2.4)
- ❌ Documentation reference (use current docs)

---

## 📊 Evolution Timeline

```
Legacy Scripts (Pre-v1)
    ↓
sorter/ (v1.0)
    ↓
sorter_v2/ (v2.0)
    ↓
sorter_v2_dev_only/ (v2.x development)
    ↓
Current: sorter/ (v2.4) ← Use This!
```

---

## 🎯 Current Active Tools

**For actual use, refer to:**
- **Sorter:** `../sorter/` (v2.4)
- **Builder Suite:** `../builder/`
- **CivitAI Converter:** `../civitai_converter/`
- **Modular Builder:** `../modular_builder/`

**Documentation:** See [KNOWLEDGE_INDEX.md](../KNOWLEDGE_INDEX.md)

---

## 🗂️ Archive Organization

### Current Structure: ✅ Phase 2 Complete (March 6, 2026)
```
archive/
├── README.md (this file)
├── legacy_scripts/              # Original Python tools
├── sorter_versions/             # CONSOLIDATED sorter history
│   ├── v1_original/             # First consolidated version
│   ├── v2_iteration/            # Second generation
│   ├── v2_dev/                  # Development workspace
│   └── logs/                    # Development logs
│       └── gui_standard_log.txt
└── docs/                        # Historical documentation
    ├── case_standardization_summary.md
    ├── git_advice.md
    └── development_notes.md
```

---

## 📝 Preservation Notes

**Why Archive Instead of Delete:**
- Preserves project history
- Reference for design decisions
- Recovery point if needed
- Educational value

**Archive Philosophy:**
- Keep historical versions accessible
- Maintain clear lineage
- Don't clutter active workspace
- Document evolution clearly

---

## 🔗 Related Documentation

- [VERSION.md](../VERSION.md) - Current version information
- [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) - Transitioning from old versions
- [CONVERSATION_LOG.md](../CONVERSATION_LOG.md) - Development history
- [ROADMAP.md](../ROADMAP.md) - Future development plans

---

**Archive Established:** Repository consolidation v2.0 (2025)  
**Last Updated:** March 1, 2026 (v3.0 cleanup)  
**Maintained By:** Project maintainers
