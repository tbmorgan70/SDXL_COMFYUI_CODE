# 🆕 New Features Update - Version 2.3.0

**For existing Sorter 2.0 users - here's what's new!**

---

## 🎯 Quick Summary

**3 major new features** added to your favorite ComfyUI image sorter:

1. **🧬 LoRA Stack Sorting** - Group images by identical LoRA combinations
2. **📄 Metadata-Only Mode** - Extract metadata without moving files  
3. **📁 Auto-Open Folder** - Instant access to results after every operation

---

## 🚀 How to Access New Features

### In GUI Mode:
1. Run `python gui.py` as usual
2. You'll see **new dropdown options**:
   - "Sort by LoRA Stack" 
   - "Generate Metadata"
3. **New button appears** after operations: "📁 Open Output Folder"

### What Each Does:

#### 🧬 LoRA Stack Sorting
- **What**: Groups images by same LoRA combinations (ignores checkpoints)
- **When to use**: Find images with identical style effects
- **Output**: `lora_sorted/` folder with groups like `DetailTweaker_and_FilmGrain/`

#### 📄 Generate Metadata  
- **What**: Creates .txt files with comprehensive metadata
- **When to use**: Catalog your collection without reorganizing
- **Output**: `.txt` file next to each image with full metadata

#### 📁 Auto-Open Folder
- **What**: Button appears after every successful operation
- **When to use**: Instant access to your organized results
- **Output**: Opens file manager to your results folder

---

## 🔧 No Breaking Changes

- **All existing features work exactly the same**
- **No changes to CLI interface**
- **Same file formats and options supported**
- **Your existing workflows are unchanged**

---

## 💡 Pro Tips for New Features

### LoRA Stack Sorting
```
Perfect for finding your most successful LoRA combinations!
Example: All images using "DetailTweaker + FilmGrain" regardless of checkpoint
```

### Metadata-Only Mode
```
Great for analysis before reorganizing:
1. Run "Generate Metadata" first
2. Review the .txt files to understand your collection  
3. Then run your preferred sorting method
```

### Auto-Open Folder
```
No more manual navigation! Every operation ends with easy folder access.
Works on Windows, macOS, and Linux.
```

---

## 🆙 How to Update

If you're using git:
```bash
git pull origin main
```

Otherwise, just download the latest version - no additional dependencies needed!

---

## 📚 Learn More

- **[Feature Showcase](FEATURE_SHOWCASE.md)** - Detailed examples and use cases
- **[Changelog](CHANGELOG.md)** - Complete technical details
- **[Main README](README.md)** - Full documentation

---

**Happy sorting with your new features!** 🎉