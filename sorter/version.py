# Sorter 3.1.0 - Civitai Prep Release
VERSION = "3.1.0"
BUILD_DATE = "2026-08-01"
DESCRIPTION = "Advanced ComfyUI Image Organizer - Civitai Prep Update"

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
    "Extract Images from PDF/EPUB/MOBI/CBR/CBZ",  # NEW in v3.0.0!
    "Auto-Crop Presets + Face-Centered Crop",     # NEW in v3.0.0!
    "Manual Sort (Visual Triage)",                # v3.0.0
    "Civitai Prep (resource hash embedding)",     # NEW in v3.1.0!
    "Link-Aware Workflow Metadata Tracing",       # NEW in v3.1.0!
    "View Session Logs",
    "Modern GUI Interface",
    "Command Line Interface",
    "Windows Path Optimization",    # v2.3.0
    "Metadata Caching System",      # v2.3.0
    "Cross-Platform File Operations",  # v2.3.0
    "Associated File Detection",    # v2.4.0
    "Empty Folder Cleanup"          # Enhanced in v2.4.0
]

# Civitai uploads now auto-detect every resource
NOTES = "Civitai Prep embeds Model/LoRA/VAE/embedding hashes and Civitai resource IDs into PNG metadata so uploads auto-detect everything; metadata extraction is now link-aware (selector/pipe/concat nodes, runtime prompt merging)."
