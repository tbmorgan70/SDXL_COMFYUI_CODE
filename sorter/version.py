# Sorter 3.2.0 - Universal Archives & Chained Prep Release
VERSION = "3.2.0"
BUILD_DATE = "2026-08-03"
DESCRIPTION = "Advanced ComfyUI Image Organizer - Universal Archives & Chained Prep"

# Features included in this build:
FEATURES = [
    "Sort by Base Checkpoint",
    "Sort by LoRA Stack",           # v2.3.0
    "Generate Metadata Only",       # v2.3.0
    "Auto-Open Output Folder",      # v2.3.0
    "Metadata File Preservation",   # v2.4.0
    "Search & Sort by Metadata",
    "Sort by Color (HSV pixel voting)",  # Rewritten in v3.0.0!
    "Flatten Image Folders",
    "Extract Images from PDF/EPUB/MOBI/Archives",  # v3.0.0, expanded v3.2.0
    "Auto-Crop Presets + Face-Centered Crop",     # v3.0.0
    "Manual Sort (Visual Triage)",                # v3.0.0
    "Civitai Prep (resource hash embedding)",     # v3.1.0
    "Link-Aware Workflow Metadata Tracing",       # v3.1.0
    "Magic-Byte Archive Detection (CBZ/CBR/CB7/CBT/ZIP/RAR/7Z/TAR)",  # NEW in v3.2.0!
    "Civitai Prep Chained to Any Sort",           # NEW in v3.2.0!
    "View Session Logs",
    "Modern GUI Interface",
    "Command Line Interface",
    "Windows Path Optimization",    # v2.3.0
    "Metadata Caching System",      # v2.3.0
    "Cross-Platform File Operations",  # v2.3.0
    "Associated File Detection",    # v2.4.0
    "Empty Folder Cleanup"          # Enhanced in v2.4.0
]

# One-pass workflow: extract anything, sort it, ship it to Civitai
NOTES = "Archive extraction now detects the real container format by magic bytes (mislabeled .cbr/.cbz just work) and supports CB7/CBT/ZIP/RAR/7Z/TAR; Civitai Prep can run automatically as part of any sort operation."
