# 📌 Version Information

**Last Updated:** July 12, 2026

---

## 🎯 Repository Version: 3.1.0

**Release Date:** July 12, 2026  
**Status:** ✅ Released  
**Codename:** "Sorter 3.0"

### What's New in 3.1:
- ✅ **Sorter 3.0 released** — Extract Images, Manual Sort (Triage), and rewritten Color engine
- ✅ Extract Images: PDF/EPUB/MOBI/CBR/CBZ extraction with auto-crop presets + face-centered crop
- ✅ Manual Sort: keyboard-driven visual triage into custom-named buckets
- ✅ Color sorting: HSV pixel voting with chromatic priority and intuitive tuning sliders
- ✅ Standalone `ImageExtractor/` deprecated (superseded by Sorter's Extract Images mode)
- ✅ `civitai_converter/` removed from repository
- ✅ Version numbers unified across code and documentation

### What Was New in 3.0:
- ✅ Complete knowledge preservation system (Phase 1)
- ✅ Resolved duplicate nested structures (Phase 1)
- ✅ Consolidated documentation (Phase 1)
- ✅ Unified Git workflow guide (Phase 1)
- ✅ Technical documentation hub created (Phase 2)
- ✅ Archive reorganization complete (Phase 2)
- ✅ Comprehensive documentation cross-linking (Phase 2)
- ✅ Tool-specific documentation enhancement (Phase 3)
- ✅ Builder catalog created (Phase 3)
- ✅ All tool READMEs enhanced with cross-references (Phase 3)
- ✅ Integration planning complete (Phase 4)
- ✅ Unified architecture designed (Phase 4)
- ✅ Testing strategy established (Phase 4)
- ✅ Quality assurance complete (Phase 5)
- ✅ Documentation validated (100+ links, 42 files)
- ✅ Repository audited and cleaned
- ✅ Quick start instructions verified
- ✅ Installation procedures validated

---

## 🛠️ Component Versions

### Main Sorter - **v3.0.0** ✅ Production Ready
**Location:** `sorter/`  
**Status:** Active Development  
**Last Updated:** July 12, 2026

#### Features:
- Sort by Base Checkpoint (SDXL, Pony, etc.)
- Sort by LoRA Stack (v2.3+)
- Generate Metadata Only mode (v2.3+)
- Auto-Open Output Folder (v2.3+)
- Automatic Metadata Preservation (v2.4+)
- Extract Images from PDF/EPUB/MOBI/CBR/CBZ with auto-crop + face crop (v3.0)
- Manual Sort — visual triage with custom buckets (v3.0)
- Color sorting via HSV pixel voting with tuning sliders (v3.0)
- Search & Sort by Metadata
- Both GUI and CLI interfaces

#### Recent Changes:
- **v3.0:** Extract Images mode, Manual Sort (Triage) mode, color engine rewrite
- **v2.4:** Automatic metadata preservation - PNG images move with their .txt files
- **v2.3:** LoRA Stack sorting, Metadata-only mode, Auto-open output
- **v2.0:** Production-ready release from consolidated repo

**Documentation:**
- [sorter/README.md](sorter/README.md)
- [sorter/CHANGELOG.md](sorter/CHANGELOG.md)
- [sorter/FEATURE_SHOWCASE.md](sorter/FEATURE_SHOWCASE.md)

---

### CivitAI Converter - 🗑️ Removed
**Status:** Removed from repository (2026)  
Old versions remain available in git history if ever needed.

---

### Image Extractor - 📦 Deprecated
**Location:** `ImageExtractor/`  
**Status:** Superseded by Sorter 3.0's built-in **Extract Images** mode  
Kept for reference only; will not receive further updates.

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

**Superseded By:** Sorter v3.0 (in `sorter/` directory)

---

## 📊 Version History

### v3.1.0 - July 12, 2026 - "Sorter 3.0" ✅ Released
**Focus:** Major Sorter feature expansion and documentation unification

**Highlights:**
- ✅ Sorter 3.0: Extract Images mode (PDF/EPUB/MOBI/CBR/CBZ → images, crop presets, face crop)
- ✅ Sorter 3.0: Manual Sort (Triage) — visual gallery with keyboard bucket assignment
- ✅ Sorter 3.0: Color engine rewrite (HSV pixel voting, chromatic priority, tuning sliders)
- ✅ Deprecated standalone ImageExtractor; removed civitai_converter
- ✅ Unified version numbers across code and docs

### v3.0.0 - March 2026 - "Unified Overhaul" ✅ Complete
**Focus:** Knowledge preservation, cleanup, and organization

**Phase 1 Complete (March 1, 2026):**
- ✅ Created knowledge management system (KNOWLEDGE_INDEX, CONVERSATION_LOG, CURATION_PLAN)
- ✅ Moved recovered knowledge into repository
- ✅ Resolved duplicate modular_builder/modular_builder/ structure
- ✅ Consolidated git documentation → GIT_WORKFLOW.md
- ✅ Created comprehensive VERSION.md (this file)
- ✅ Archived outdated documentation
- ✅ Standardized version numbers

**Phase 2 Complete (March 6, 2026):**
- ✅ Created docs/ directory with technical documentation
- ✅ ARCHITECTURE.md - Complete system design
- ✅ DEVELOPMENT_GUIDE.md - Contributor guidelines
- ✅ Consolidated archive structure (sorter_versions/)
- ✅ Comprehensive documentation cross-linking
- ✅ Enhanced navigation throughout repository

**Phase 3 Complete (March 6, 2026):**
- ✅ Created comprehensive builder catalog (builder/BUILDERS.md)
- ✅ Enhanced builder/README.md with cross-references and navigation
- ✅ Updated sorter/README.md (v2.4, added Related Documentation)
- ✅ Enhanced modular_builder/README.md with cross-references
- ✅ Enhanced civitai_converter/COMFYUI_TO_CIVITAI_README.md with cross-references
- ✅ Updated KNOWLEDGE_INDEX.md with Phase 3 additions
- ✅ All tool READMEs now have "Related Documentation" sections
- ✅ Version consistency across all documentation

**Phase 4 Complete (March 7, 2026):**
- ✅ Created comprehensive INTEGRATION_PLAN.md (~15,000 words)
- ✅ Documented all tool interfaces (inputs, outputs, data formats)
- ✅ Designed unified configuration system (YAML-based)
- ✅ Planned shared metadata format (UnifiedMetadata JSON)
- ✅ Created TESTING_STRATEGY.md with 90% coverage goal
- ✅ Audited existing tests (6 files, ~5% coverage currently)
- ✅ Defined progressive coverage milestones (25% → 60% → 90%)
- ✅ Designed CI/CD pipeline with GitHub Actions
- ✅ Proposed shared library structure (lib/ directory)
- ✅ Outlined unified dashboard concept (Tkinter + web)

**Phase 5 Complete (March 7, 2026):**
- ✅ Quality assurance
- ✅ Link validation
- ✅ Repository audit
- ✅ User testing

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

### Q2/Q3 2026 - v3.1.0 ✅ Delivered July 2026
- Sorter 3.0 (Extract Images, Manual Sort, new color engine)
- Documentation and version unification

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
