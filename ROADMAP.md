# 🗺️ Development Roadmap - Unified Repository

## 🎯 Current Status (v3.8, Sorter 3.7.2 — November 2026)
- ✅ Repository consolidation complete
- ✅ Clean folder structure implemented
- ✅ Sorter 3.0 production ready (Extract Images, Manual Sort/Triage, HSV color engine)
- ✅ Civitai Prep (3.1): resource hashes so Civitai auto-detects checkpoint, LoRAs and embeddings on upload
- ✅ Universal archives, YOLO face crop, PDF page stitching (3.2–3.4)
- ✅ AI Upscale with the ComfyUI upscale models (3.5)
- ✅ Manual Crop at exact preset sizes, inside Triage or on its own (3.6, 3.6.1)
- ✅ Custom-sampler workflows (Krea2, Flux) traced for Civitai Prep and reports (3.6.2)
- ✅ Find Duplicates: identical copies and look-alikes, restorable trash (3.7). Keeper rule: never a copy in a
  REJECT folder, then most pixels, then a copy in a posted folder, then the one with metadata, then the bigger file
- ✅ Cleanup (3.7.1): Sort by Checkpoint uses the workflow's checkpoint, Extract face framing, Manual Crop review
  fixes, Find Duplicates polish
- ✅ HTML builders available
- ✅ Legacy tools archived
- 🗑️ CivitAI converter removed; standalone ImageExtractor deprecated

## ⏭️ Next Up

- [ ] **Try Sorter 3.7.1 on real folders**: Sort by Checkpoint (fewer odd folders like `00013`), Extract
  face crops, Manual Crop, Find Duplicates on a drive root
- [ ] **Manual Crop tab's model list** still reads the default upscale models folder at startup; the editor
  itself now uses the AI Upscale tab's folder
- [ ] **Confirm 3.6.2 on Civitai** — prep a Krea2 image and upload it; prompt, settings and resources should all appear
- [ ] **Upscaling Phase 3** — face restore, colorize, denoise ([plan](docs/UPSCALING_PLAN.md))
- [ ] Re-tune Extract's face confidence threshold (0.6) on more than one magazine

## 💡 Parked Ideas
- **Civitai Prep as a standalone one-button tool** anyone could use
- **Source Finder**: given an image, find where it came from in the indexed library (reuses the Find Duplicates index)
- **VAE auto-detection on Civitai** — still not showing after the 3.4.3 fix; cause unknown

## 🚀 Longer-Term Features

*The original Q4 2025–Q2 2026 dates have passed; work went to the Sorter features above.*

### **Phase 1: Integration**
- [ ] **Builder Integration** - Merge HTML builder tools into main sorter
- [ ] **Unified GUI** - Single interface for all tools
- [x] **Cross-tool Workflows** - Extract → Sort and Sort → Civitai Prep chaining (3.0, 3.2)
- [x] **Enhanced Metadata** - Link-aware workflow tracing (3.1, 3.6.2)

### **Phase 2: Advanced Features**
- [ ] **Batch Processing** - Multi-folder operations
- [ ] **AI-Powered Tagging** - Automatic content classification
- [ ] **Custom Sorting Rules** - User-defined organization logic
- [ ] **Integration APIs** - Connect with external tools

### **Phase 3: Ecosystem**
- [ ] **Plugin System** - Third-party extensions
- [ ] **Cloud Sync** - Backup and sync capabilities
- [ ] **Mobile Companion** - Mobile app for quick sorting
- [ ] **Community Features** - Share sorting configurations

## 🛠️ Technical Roadmap

### **Code Quality**
- [ ] Increase test coverage to 90%+
- [ ] Add CI/CD pipeline
- [ ] Implement type hints throughout
- [ ] Add performance benchmarks

### **Architecture**
- [ ] Modular plugin architecture
- [ ] Configuration management system
- [ ] Async processing for large operations
- [ ] Database backend for metadata

### **User Experience**
- [ ] One-click installer
- [ ] Video tutorials and documentation
- [ ] Interactive help system
- [ ] Accessibility improvements

## 🔧 Development Priorities

### **High Priority**
1. **Builder Integration** - Users want unified interface
2. **Performance Optimization** - Handle larger image collections
3. **Documentation** - Comprehensive user guides

### **Medium Priority**
1. **Advanced Sorting** - More metadata options
2. **Backup/Restore** - Protect user configurations
3. **Batch Operations** - Process multiple folders

### **Low Priority**
1. **Mobile App** - Nice to have for power users
2. **Cloud Features** - Dependent on user demand
3. **Plugin Ecosystem** - After core features complete

## 📊 Success Metrics

### **User Adoption**
- GitHub stars: Target 1,000+
- Downloads: Track monthly downloads
- Issues resolved: <48 hour response time

### **Code Quality**
- Test coverage: >90%
- Code quality score: A grade
- Zero critical security issues

### **Performance**
- Sort 10,000 images in <5 minutes
- GUI response time <200ms
- Memory usage <500MB for typical operations

## 🤝 Contributing

### **How to Help**
1. **Test the tools** - Report bugs and suggestions
2. **Improve documentation** - Add examples and guides
3. **Add features** - Submit PRs for new functionality
4. **Share feedback** - Tell us what works and what doesn't

### **Development Setup**
See [Development Guide](docs/DEVELOPMENT_GUIDE.md) for complete setup instructions.

```bash
# Clone and set up development environment
git clone https://github.com/tbmorgan70/SDXL_COMFYUI_CODE.git
cd SDXL_COMFYUI_CODE
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development
cd sorter/
python gui.py
```

## 📅 Release Schedule

### **Minor Releases (Monthly)**
- Bug fixes and small improvements
- New sorting options
- Documentation updates

### **Major Releases (Quarterly)**
- New tool integrations
- Significant feature additions
- Performance improvements

### **LTS Releases (Yearly)**
- Stable release for production users
- Long-term support and maintenance
- Major architectural changes

---

**Join us in building the ultimate ComfyUI toolkit! 🚀**
