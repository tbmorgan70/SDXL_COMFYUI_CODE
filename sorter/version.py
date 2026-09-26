# Sorter 3.5.0 - AI Upscale
VERSION = "3.5.0"
BUILD_DATE = "2026-09-26"
DESCRIPTION = "Advanced ComfyUI Image Organizer - AI Upscale"

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
    "AI Upscale (ComfyUI models via spandrel)",   # NEW in v3.5.0!
    "Extract: AI Upscale When Needed",            # NEW in v3.5.0!
    "View Session Logs",
    "Modern GUI Interface",
    "Command Line Interface",
    "Windows Path Optimization",    # v2.3.0
    "Metadata Caching System",      # v2.3.0
    "Cross-Platform File Operations",  # v2.3.0
    "Associated File Detection",    # v2.4.0
    "Empty Folder Cleanup"          # Enhanced in v2.4.0
]

# Upscale with the models already in ComfyUI, and only where it's needed
NOTES = "AI Upscale mode runs any model in ComfyUI's upscale_models folder on the GPU, landing on a target long edge and preserving PNG metadata. Extract can AI-upscale just the region around a face when the source is too small for the requested framing."
