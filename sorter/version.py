# Sorter 3.7.0 - Find Duplicates
VERSION = "3.7.0"
BUILD_DATE = "2026-10-24"
DESCRIPTION = "Advanced ComfyUI Image Organizer - Find Duplicates"

# Features included in this build:
FEATURES = [
    "Sort by Base Checkpoint",
    "Sort by LoRA Stack",           # v2.3.0
    "Generate Metadata Only",       # v2.3.0
    "Auto-Open Output Folder",      # v2.3.0
    "Metadata File Preservation",   # v2.4.0
    "Search & Sort by Metadata",
    "Sort by Color (HSV pixel voting)",  # Rewritten in v3.0.0
    "Flatten Image Folders",
    "Extract Images from PDF/EPUB/MOBI/Archives",  # v3.0.0, expanded v3.2.0
    "Auto-Crop Presets + Face-Centered Crop",     # v3.0.0, YOLO backend v3.3.0
    "Manual Sort (Visual Triage)",                # v3.0.0
    "Civitai Prep (resource hash embedding)",     # v3.1.0
    "Link-Aware Workflow Metadata Tracing",       # v3.1.0
    "Magic-Byte Archive Detection (CBZ/CBR/CB7/CBT/ZIP/RAR/7Z/TAR)",  # v3.2.0
    "Civitai Prep Chained to Any Sort",           # v3.2.0
    "Multi-Backend Face Detection (YOLO/Haar)",   # v3.3.0
    "PDF Page Auto-Stitching (split scan strips)",  # v3.4.0
    "Named Face Framing Presets",                 # v3.4.0
    "Self-Describing Output Folders + Manifests",  # v3.4.1
    "AI Upscale (ComfyUI models via spandrel)",   # v3.5.0
    "Extract: AI Upscale When Needed",            # v3.5.0
    "Manual Crop (fixed frame, exact presets, metadata kept)",  # v3.6.0
    "Find Duplicates (Certain/Probable, highest-resolution keeper, restorable trash)",  # NEW in v3.7.0!
    "View Session Logs",
    "Modern GUI Interface",
    "Command Line Interface",
    "Windows Path Optimization",    # v2.3.0
    "Metadata Caching System",      # v2.3.0
    "Cross-Platform File Operations",  # v2.3.0
    "Associated File Detection",    # v2.4.0
    "Empty Folder Cleanup"          # Enhanced in v2.4.0
]

# Crop by hand without leaving Triage
NOTES = ("Find Duplicates: indexes the folders you pick, groups identical copies and look-alikes (e.g. a post_sampler image and its 4x upscale), keeps the highest-resolution copy, and moves extras to a restorable _duplicates_trash.")
