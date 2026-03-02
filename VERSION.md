# 📌 Version Information

**Last Updated:** March 1, 2026

---

## 🎯 Repository Version: 3.0.0

**Release Date:** March 2026  
**Status:** 🔄 In Progress - Major Cleanup & Reorganization  
**Codename:** "Unified Overhaul"

### What's New in 3.0:
- ✅ Complete knowledge preservation system
- ✅ Resolved duplicate nested structures
- ✅ Consolidated documentation (29 → organized set)
- ✅ Unified Git workflow guide
- 🔄 Version standardization in progress
- 🔄 Archive reorganization in progress
- ⏳ Documentation enhancement upcoming
- ⏳ Tool integration planning upcoming

---

## 🛠️ Component Versions

### Main Sorter - **v2.4.0** ✅ Production Ready
**Location:** `sorter/`  
**Status:** Active Development  
**Last Updated:** Recent

#### Features:
- Sort by Base Checkpoint (SDXL, Pony, etc.)
- Sort by LoRA Stack (v2.3+)
- Generate Metadata Only mode (v2.3+)
- Auto-Open Output Folder (v2.3+)
- Automatic Metadata Preservation (v2.4+)
- Search & Sort by Metadata
- Color-based sorting with visual previews
- Both GUI and CLI interfaces

#### Recent Changes:
- **v2.4:** Automatic metadata preservation - PNG images move with their .txt files
- **v2.3:** LoRA Stack sorting, Metadata-only mode, Auto-open output
- **v2.0:** Production-ready release from consolidated repo

**Documentation:**
- [sorter/README.md](sorter/README.md)
- [sorter/CHANGELOG.md](sorter/CHANGELOG.md)
- [sorter/FEATURE_SHOWCASE.md](sorter/FEATURE_SHOWCASE.md)

---

### CivitAI Converter - **v1.0.0** ✅ Functional
**Location:** `civitai_converter/`  
**Status:** Stable  
**Last Updated:** Repository consolidation (v2.0)

#### Features:
- Convert ComfyUI workflows to CivitAI format
- Metadata preservation and cleanup
- Batch processing support

**Documentation:**
- [civitai_converter/COMFYUI_TO_CIVITAI_README.md](civitai_converter/COMFYUI_TO_CIVITAI_README.md)

---

### Builder Suite - **v1.5.0** ✅ Available
**Location:** `builder/`  
**Status:** Active Collection  
**Last Updated:** Ongoing additions

#### Features:
- Dynamic prompt generation interfaces
- Interactive HTML dashboards
- Custom workflow builders
- 15+ themed builder templates

#### Templates Include:
- Ultra Disco Dollz
- Ultra Nova Skyrift
- Ultra Retro Sci-Fi
- Generic Dual-Toggle
- Pink Gunz Anime
- And many more...

**Documentation:**
- [builder/README.md](builder/README.md)
- [builder/usage_guide.md](builder/usage_guide.md)
- [builder/technical_reference.md](builder/technical_reference.md)

---

### Modular Builder - **v1.0.0** ✅ Active
**Location:** `modular_builder/`  
**Status:** Active Development  
**Last Updated:** March 2026

#### Features:
- Category-based prompt building
- 168+ category CSV files
- Vintage categories collection
- Server-based interface
- Highly customizable

#### Recent Changes:
- **March 2026:** Resolved duplicate nested structure
- Preserved unique Nova Skyrift HTML
- Consolidated vintage categories

**Documentation:**
- [modular_builder/README.md](modular_builder/README.md)
- [modular_builder/GETTING_STARTED.md](modular_builder/GETTING_STARTED.md)
- [modular_builder/TECHNICAL.md](modular_builder/TECHNICAL.md)

---

### Legacy Unified Sorter - **v1.0.0** 📦 Archived
**Location:** `unified_sorter.py` (root)  
**Status:** Legacy Reference  
**Last Updated:** Pre-consolidation

#### Features:
- Original multi-mode sorter
- Text file organization
- ComfyUI batch processing
- Color analysis features

**Superseded By:** Sorter v2.4 (in `sorter/` directory)

---

## 📊 Version History

### v3.0.0 - March 2026 - "Unified Overhaul" 🔄 In Progress
**Focus:** Knowledge preservation, cleanup, and organization

**Completed:**
- ✅ Created knowledge management system (KNOWLEDGE_INDEX, CONVERSATION_LOG, CURATION_PLAN)
- ✅ Moved recovered knowledge into repository
- ✅ Resolved duplicate modular_builder/modular_builder/ structure
- ✅ Consolidated git documentation → GIT_WORKFLOW.md
- ✅ Created comprehensive VERSION.md (this file)

**In Progress:**
- 🔄 Archive reorganization
- 🔄 Documentation standardization
- 🔄 Version consistency updates

**Upcoming:**
- ⏳ Documentation enhancement (Phase 3)
- ⏳ Integration planning (Phase 4)
- ⏳ Quality assurance (Phase 5)

### v2.0.0 - 2025 - "Repository Consolidation"
**Focus:** Unifying multiple separate repositories

**Achievements:**
- ✅ Consolidated multiple repos into single unified structure
- ✅ Case standardization (UPPER → lower)
- ✅ Clean folder structure implementation
- ✅ Sorter v2.0 production ready
- ✅ Archive system for legacy versions
- ✅ Migration guide for users

**Major Milestone:** All tools now in one cohesive repository

### v1.x - Pre-2025 - "Independent Development"
**Multiple Repositories Era**

**Components:**
- Individual sorter iterations (v1, v2, v2_dev)
- Separate builder collection
- Various experimental scripts

**Archived:** Multiple versions preserved in `archive/` for reference

---

## 🔢 Versioning Scheme

We follow **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

### Repository Level:
- **MAJOR:** Significant restructuring, major new features, breaking changes
- **MINOR:** New features, component updates, non-breaking changes
- **PATCH:** Bug fixes, documentation updates, minor tweaks

### Component Level:
Each tool maintains independent versioning:
- Components can update independently
- Repository version reflects overall state
- Major component updates may trigger repository minor version bump

---

## 🎯 Version Roadmap

### Q2 2026 - v3.1.0 (Planned)
- Complete documentation overhaul
- Archive consolidation
- Enhanced cross-linking
- Quality assurance complete

### Q3 2026 - v3.2.0 (Planned)
- Tool integration preparation
- Unified configuration system
- Testing infrastructure
- CI/CD pipeline

### Q4 2026 - v4.0.0 (Vision)
- Unified interface for all tools
- Cross-tool workflows
- Plugin architecture
- Enhanced metadata handling

---

## 📝 Component Change Tracking

### How to Update Versions:

#### For Sorter Updates:
1. Update `sorter/version.py`
2. Update `sorter/CHANGELOG.md`
3. Update this VERSION.md
4. Update main README.md if significant

#### For Builder Suite Updates:
1. Update `builder/changelog.md`
2. Update this VERSION.md
3. Document in CONVERSATION_LOG.md

#### For Repository Updates:
1. Update this VERSION.md
2. Update CONVERSATION_LOG.md
3. Update ROADMAP.md if affects future plans
4. Commit with clear version message

---

## 🔗 Related Documentation

- [README.md](README.md) - Project overview and quick start
- [ROADMAP.md](ROADMAP.md) - Future development plans
- [CHANGELOG.md](sorter/CHANGELOG.md) - Detailed sorter changes
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Transitioning from old structure
- [CONVERSATION_LOG.md](CONVERSATION_LOG.md) - Development session tracking
- [CURATION_PLAN.md](CURATION_PLAN.md) - Ongoing overhaul plan

---

## ℹ️ Version Check

### Current Installed Version
To check which version you're using:

```powershell
# Check sorter version
python sorter/version.py

# Check repository version
# (This file - VERSION.md header)
```

### Latest Version
Always available at: https://github.com/tbmorgan70/SDXL_COMFYUI_CODE

---

**Maintained By:** Project maintainers and contributors  
**Update Frequency:** After significant changes or component updates  
**Questions?** Check [CONVERSATION_LOG.md](CONVERSATION_LOG.md) or open an issue
