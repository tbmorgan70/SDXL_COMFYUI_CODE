# Sorter 3.4.1 - Page Stitching & Honest Framing Release
VERSION = "3.4.1"
BUILD_DATE = "2026-08-30"
DESCRIPTION = "Advanced ComfyUI Image Organizer - Page Stitching & Honest Framing"

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
    "Auto-Crop Presets + Face-Centered Crop",     # v3.0.0, YOLO backend v3.3.0
    "Manual Sort (Visual Triage)",                # v3.0.0
    "Civitai Prep (resource hash embedding)",     # v3.1.0
    "Link-Aware Workflow Metadata Tracing",       # v3.1.0
    "Magic-Byte Archive Detection (CBZ/CBR/CB7/CBT/ZIP/RAR/7Z/TAR)",  # NEW in v3.2.0!
    "Civitai Prep Chained to Any Sort",           # v3.2.0
    "Multi-Backend Face Detection (YOLO/Haar)",   # v3.3.0
    "PDF Page Auto-Stitching (split scan strips)",  # NEW in v3.4.0!
    "Named Face Framing Presets",                 # v3.4.0
    "Self-Describing Output Folders + Manifests",  # NEW in v3.4.1!
    "View Session Logs",
    "Modern GUI Interface",
    "Command Line Interface",
    "Windows Path Optimization",    # v2.3.0
    "Metadata Caching System",      # v2.3.0
    "Cross-Platform File Operations",  # v2.3.0
    "Associated File Detection",    # v2.4.0
    "Empty Folder Cleanup"          # Enhanced in v2.4.0
]

# Scanned pages come out whole, and framing limits are no longer silent
NOTES = "PDF pages that scanners stored as several tiled strips are now reassembled automatically, so magazine scans extract as whole pages instead of halves. Face framing moved to named presets, and the extractor reports when a source lacks the resolution for the requested framing instead of silently widening the crop."
